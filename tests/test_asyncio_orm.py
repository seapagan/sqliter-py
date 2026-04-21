"""Tests for async ORM support."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

import pytest

from sqliter.asyncio import AsyncSqliterDB
from sqliter.asyncio.orm import (
    AsyncBaseDBModel,
    AsyncForeignKey,
    AsyncLazyLoader,
    AsyncManyToMany,
    AsyncManyToManyManager,
    AsyncPrefetchedM2MResult,
    AsyncPrefetchedResult,
    AsyncReverseManyToMany,
    AsyncReverseQuery,
)
from sqliter.asyncio.orm.query import AsyncReverseRelationship
from sqliter.exceptions import ManyToManyIntegrityError, RecordFetchError
from sqliter.orm.m2m import ManyToManyOptions
from sqliter.orm.registry import ModelRegistry

if TYPE_CHECKING:
    from sqliter.asyncio.orm.m2m import HasPKAndContext as AsyncM2MContext
    from sqliter.asyncio.orm.query import HasPKAndContext as AsyncReverseContext
    from sqliter.model.model import BaseDBModel


@pytest.mark.asyncio
async def test_async_fk_lazy_fetch_and_select_related() -> None:
    """Async FK access supports explicit lazy fetch and eager cache use."""
    state = ModelRegistry.snapshot()
    try:

        class Author(AsyncBaseDBModel):
            """Author model for async FK tests."""

            name: str

        class Book(AsyncBaseDBModel):
            """Book model for async FK tests."""

            title: str
            author: AsyncForeignKey[Author] = AsyncForeignKey(
                Author,
                on_delete="CASCADE",
                related_name="books",
            )

        db = AsyncSqliterDB(memory=True)
        await db.create_table(Author)
        await db.create_table(Book)

        author = await db.insert(Author(name="Ada"))
        book = await db.insert(Book(title="Notes", author_id=author.pk))

        fetched = await db.get(Book, book.pk)
        assert fetched is not None
        loader = fetched.author
        assert isinstance(loader, AsyncLazyLoader)

        loaded = await loader.fetch()
        assert loaded is not None
        assert loaded.name == "Ada"

        eager = await db.select(Book).select_related("author").fetch_one()
        assert eager is not None
        assert isinstance(eager.author, Author)
        assert eager.author.name == "Ada"

        await db.close()
    finally:
        ModelRegistry.restore(state)


@pytest.mark.asyncio
async def test_async_fk_loader_descriptor_and_model_edge_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Async FK helpers cover null, cache, error, and refresh paths."""
    state = ModelRegistry.snapshot()
    try:

        class Author(AsyncBaseDBModel):
            """Author model for async loader edge tests."""

            name: str

        class Book(AsyncBaseDBModel):
            """Book model for async loader edge tests."""

            title: str
            author: AsyncForeignKey[Author] = AsyncForeignKey(
                Author,
                null=True,
                on_delete="CASCADE",
                related_name="books",
            )

        assert isinstance(Book.author, AsyncForeignKey)
        assert isinstance(Author.__dict__["books"], AsyncReverseRelationship)

        draft = Book(title="Draft", author_id=None)
        assert draft.author is None

        draft.author_id = 1
        unloaded = cast("AsyncLazyLoader[Author]", draft.author)
        assert unloaded.db_context is None
        assert "unloaded" in repr(unloaded)
        with pytest.raises(AttributeError, match=r"await relation\.fetch"):
            _ = unloaded.name

        db = AsyncSqliterDB(memory=True)
        await db.create_table(Author)
        await db.create_table(Book)
        author = await db.insert(Author(name="Ada"))

        draft.author_id = author.pk
        draft.db_context = db
        refreshed = cast("AsyncLazyLoader[Author]", draft.author)
        assert refreshed.db_context is db
        loaded = await refreshed.fetch()
        assert loaded is not None
        assert loaded.name == "Ada"
        assert "loaded" in repr(refreshed)

        draft.__dict__.setdefault("_fk_cache", {})["author"] = loaded
        assert draft.author is loaded

        async def broken_get(
            model: type[AsyncBaseDBModel],
            pk: int | None,
        ) -> None:
            raise RecordFetchError(model.get_table_name(), pk or 0)

        monkeypatch.setattr(db, "get", broken_get)
        failing = AsyncLazyLoader(
            instance=draft,
            to_model=Author,
            fk_id=author.pk,
            db_context=db,
        )
        with pytest.raises(RecordFetchError):
            await failing.fetch()

        await db.close()
    finally:
        ModelRegistry.restore(state)


@pytest.mark.asyncio
async def test_async_fk_missing_relation_is_cached(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing async FK lookups should not re-query after first fetch."""
    state = ModelRegistry.snapshot()
    try:

        class Author(AsyncBaseDBModel):
            """Author model for missing async FK cache tests."""

            name: str

        class Book(AsyncBaseDBModel):
            """Book model for missing async FK cache tests."""

            title: str
            author: AsyncForeignKey[Author] = AsyncForeignKey(
                Author,
                null=True,
                on_delete="CASCADE",
                related_name="books",
            )

        db = AsyncSqliterDB(memory=True)
        loader = AsyncLazyLoader(
            instance=Book(title="Draft", author_id=99),
            to_model=Author,
            fk_id=99,
            db_context=db,
        )
        calls = {"count": 0}

        async def missing_get(
            model: type[AsyncBaseDBModel],
            pk: int,
        ) -> None:
            calls["count"] += 1

        monkeypatch.setattr(db, "get", missing_get)

        assert await loader.fetch() is None
        assert await loader.fetch() is None
        assert calls["count"] == 1
        assert "loaded" in repr(loader)

        await db.close()
    finally:
        ModelRegistry.restore(state)


@pytest.mark.asyncio
async def test_async_fk_zero_fk_id_is_missing() -> None:
    """Async FK with unsaved value 0 should behave as a missing relation."""
    state = ModelRegistry.snapshot()
    try:

        class Author(AsyncBaseDBModel):
            """Author model for async unsaved FK tests."""

            name: str

        class Book(AsyncBaseDBModel):
            """Book model for async unsaved FK tests."""

            title: str
            author: AsyncForeignKey[Author] = AsyncForeignKey(
                Author,
                null=True,
                on_delete="CASCADE",
                related_name="books",
            )

        draft = Book(title="Draft", author_id=0)
        assert draft.author is None
        assert draft.__dict__.get("_fk_cache", {}) == {}
    finally:
        ModelRegistry.restore(state)


@pytest.mark.asyncio
async def test_async_fk_cache_refreshes_when_fk_id_changes() -> None:
    """Changing FK id invalidates stale async FK cache entries."""
    state = ModelRegistry.snapshot()
    try:

        class Author(AsyncBaseDBModel):
            """Author model for async cache refresh tests."""

            name: str

        class Book(AsyncBaseDBModel):
            """Book model for async cache refresh tests."""

            title: str
            author: AsyncForeignKey[Author] = AsyncForeignKey(
                Author,
                null=True,
                on_delete="CASCADE",
                related_name="books",
            )

        book = Book(title="Draft", author_id=1)
        first_loader = cast("AsyncLazyLoader[Author]", book.author)
        assert first_loader._fk_id == 1

        object.__setattr__(book, "author_id", 2)
        second_loader = cast("AsyncLazyLoader[Author]", book.author)
        assert second_loader is not first_loader
        assert second_loader._fk_id == 2

        cached_author = Author(name="Loaded")
        cached_author.pk = 2
        book.__dict__.setdefault("_fk_cache", {})["author"] = cached_author

        object.__setattr__(book, "author_id", 3)
        stale_cache = book.__dict__["_fk_cache"]["author"]
        assert stale_cache is not second_loader

        refresh_loader = cast("AsyncLazyLoader[Author]", book.author)
        assert refresh_loader is not stale_cache
        assert refresh_loader._fk_id == 3
    finally:
        ModelRegistry.restore(state)


@pytest.mark.asyncio
async def test_async_fk_descriptor_direct_paths() -> None:
    """Direct descriptor access covers null, cached, and new loader branches."""
    state = ModelRegistry.snapshot()
    try:

        class Author(AsyncBaseDBModel):
            """Author model for direct descriptor tests."""

            name: str

        class Book(AsyncBaseDBModel):
            """Book model for direct descriptor tests."""

            title: str
            author: AsyncForeignKey[Author] = AsyncForeignKey(
                Author,
                null=True,
                related_name="books",
            )

        descriptor = cast("AsyncForeignKey[Author]", Book.__dict__["author"])
        empty_loader = AsyncLazyLoader(
            instance=object(),
            to_model=Author,
            fk_id=None,
            db_context=None,
        )
        assert await empty_loader.fetch() is None

        draft = Book(title="Draft", author_id=None)
        assert descriptor.__get__(draft, Book) is None

        cached = AsyncLazyLoader(
            instance=draft,
            to_model=Author,
            fk_id=1,
            db_context=None,
        )
        draft.author_id = 1
        draft.__dict__["_fk_cache"] = {"author": cached}
        cached_value = descriptor.__get__(draft, Book)
        assert isinstance(cached_value, AsyncLazyLoader)
        assert cached_value is cached

        fresh = Book(title="Fresh", author_id=2)
        loader = descriptor.__get__(fresh, Book)
        assert isinstance(loader, AsyncLazyLoader)
        assert fresh.__dict__["_fk_cache"]["author"] is loader
    finally:
        ModelRegistry.restore(state)


@pytest.mark.asyncio
async def test_async_reverse_relationship_and_prefetch() -> None:
    """Async reverse descriptors support lazy queries and prefetched reads."""
    state = ModelRegistry.snapshot()
    try:

        class Author(AsyncBaseDBModel):
            """Author model for async reverse tests."""

            name: str

        class Book(AsyncBaseDBModel):
            """Book model for async reverse tests."""

            title: str
            author: AsyncForeignKey[Author] = AsyncForeignKey(
                Author,
                on_delete="CASCADE",
                related_name="books",
            )

        db = AsyncSqliterDB(memory=True)
        await db.create_table(Author)
        await db.create_table(Book)

        author = await db.insert(Author(name="Jane"))
        await db.insert(Book(title="One", author_id=author.pk))
        await db.insert(Book(title="Two", author_id=author.pk))

        fetched_author = await db.get(Author, author.pk)
        assert fetched_author is not None
        reverse = fetched_author.books
        assert isinstance(reverse, AsyncReverseQuery)
        assert await reverse.count() == 2
        book_items = cast("list[Book]", await reverse.fetch_all())
        titles = {book.title for book in book_items}
        assert titles == {"One", "Two"}

        prefetched = await (
            db.select(Author).prefetch_related("books").fetch_one()
        )
        assert prefetched is not None
        prefetched_books = prefetched.books
        assert isinstance(prefetched_books, AsyncPrefetchedResult)
        assert await prefetched_books.exists() is True
        assert await prefetched_books.count() == 2

        await db.close()
    finally:
        ModelRegistry.restore(state)


@pytest.mark.asyncio
async def test_async_reverse_query_and_prefetched_result_edge_paths() -> None:
    """Async reverse wrappers handle empty, prefetched, and paged paths."""
    state = ModelRegistry.snapshot()
    try:

        class Author(AsyncBaseDBModel):
            """Author model for async reverse edge tests."""

            name: str

        class Book(AsyncBaseDBModel):
            """Book model for async reverse edge tests."""

            title: str
            author: AsyncForeignKey[Author] = AsyncForeignKey(
                Author,
                on_delete="CASCADE",
                related_name="books",
            )

        empty_author = Author(name="No DB")
        empty_reverse = AsyncReverseQuery(
            instance=cast("AsyncReverseContext", empty_author),
            to_model=Book,
            fk_field="author",
            db_context=None,
        )
        assert await empty_reverse.fetch_all() == []
        assert await empty_reverse.fetch_one() is None
        assert await empty_reverse.count() == 0
        assert await empty_reverse.exists() is False

        db = AsyncSqliterDB(memory=True)
        await db.create_table(Author)
        await db.create_table(Book)

        author = await db.insert(Author(name="Grace"))
        await db.insert(Book(title="One", author_id=author.pk))
        await db.insert(Book(title="Two", author_id=author.pk))

        fetched_author = await db.get(Author, author.pk)
        assert fetched_author is not None
        reverse = cast("AsyncReverseQuery", fetched_author.books)
        second = cast(
            "Book | None",
            await reverse.offset(1).limit(1).fetch_one(),
        )
        assert second is not None
        assert second.title == "Two"

        prefetched = AsyncPrefetchedResult(
            cached_items=cast("list[BaseDBModel]", [author]),
            instance=cast("AsyncReverseContext", fetched_author),
            to_model=Author,
            fk_field="author",
            db_context=db,
        )
        assert await prefetched.fetch_all() == [author]
        assert await prefetched.fetch_one() == author
        assert await prefetched.count() == 1
        assert await prefetched.exists() is True
        filtered = prefetched.filter(name="Grace")
        assert isinstance(filtered, AsyncReverseQuery)

        await db.close()
    finally:
        ModelRegistry.restore(state)


@pytest.mark.asyncio
async def test_async_reverse_query_skips_unsaved_parent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unsaved parent with pk=0 should skip reverse query execution."""
    state = ModelRegistry.snapshot()
    try:

        class Author(AsyncBaseDBModel):
            """Author model for unsaved reverse skip tests."""

            name: str

        class Book(AsyncBaseDBModel):
            """Book model for unsaved reverse skip tests."""

            title: str
            author: AsyncForeignKey[Author] = AsyncForeignKey(
                Author,
                on_delete="CASCADE",
                related_name="books",
            )

        db = AsyncSqliterDB(memory=True)
        await db.create_table(Author)
        await db.create_table(Book)

        def guarded_select(*args: object, **kwargs: object) -> object:
            msg = (
                "reverse queries should be skipped for unsaved parent instances"
            )
            raise AssertionError(msg)

        monkeypatch.setattr(db, "select", guarded_select)
        unsaved_author = Author(name="Unsaved")
        unsaved_author.db_context = db

        reverse = cast("AsyncReverseQuery", unsaved_author.books)
        assert unsaved_author.pk == 0
        assert await reverse.fetch_all() == []
        assert await reverse.fetch_one() is None
        assert await reverse.count() == 0
        assert await reverse.exists() is False

        await db.close()
    finally:
        ModelRegistry.restore(state)


@pytest.mark.asyncio
async def test_async_reverse_query_filter_and_model_registry_skip_paths() -> (
    None
):
    """Filtered reverse queries and async registry skip branches behave."""
    state = ModelRegistry.snapshot()
    try:

        class Author(AsyncBaseDBModel):
            """Author model for reverse filter tests."""

            name: str

        class Book(AsyncBaseDBModel):
            """Book model for reverse filter tests."""

            title: str
            author: AsyncForeignKey[Author] = AsyncForeignKey(
                Author,
                on_delete="CASCADE",
                related_name="books",
            )

        db = AsyncSqliterDB(memory=True)
        await db.create_table(Author)
        await db.create_table(Book)

        author = await db.insert(Author(name="Lin"))
        await db.insert(Book(title="One", author_id=author.pk))
        await db.insert(Book(title="Two", author_id=author.pk))

        fetched = await db.get(Author, author.pk)
        assert fetched is not None
        filtered = cast("AsyncReverseQuery", fetched.books).filter(title="Two")
        match = cast("Book | None", await filtered.fetch_one())
        assert match is not None
        assert match.title == "Two"

        draft = Book(title="Draft", author_id=author.pk)
        first = cast("AsyncLazyLoader[Author]", draft.author)
        draft.db_context = db
        second = cast("AsyncLazyLoader[Author]", draft.author)
        assert second is not first
        assert second.db_context is db

        cached_author = await db.get(Author, author.pk)
        assert cached_author is not None
        draft.__dict__["_fk_cache"] = {"author": cached_author}
        assert draft.author is cached_author

        Author._install_async_fk_reverse_accessors(
            {
                Book.get_table_name(): [
                    {
                        "to_model": Author,
                        "fk_field": "author",
                        "related_name": "written_books",
                    },
                    {"to_model": Author, "fk_field": "author"},
                ]
            }
        )
        assert isinstance(
            Author.__dict__["written_books"],
            AsyncReverseRelationship,
        )
        Author._install_async_m2m_reverse_accessors(
            {
                Book.get_table_name(): [
                    {
                        "to_model": Author,
                        "junction_table": "book_author",
                        "related_name": "linked_books",
                        "symmetrical": False,
                    },
                    {
                        "to_model": Author,
                        "junction_table": "book_author",
                        "symmetrical": False,
                    },
                ]
            }
        )
        assert isinstance(
            Author.__dict__["linked_books"],
            AsyncReverseManyToMany,
        )

        await db.close()
    finally:
        ModelRegistry.restore(state)


@pytest.mark.asyncio
async def test_async_many_to_many_manager_and_prefetch() -> None:
    """Async M2M descriptors support manager writes and prefetched reads."""
    state = ModelRegistry.snapshot()
    try:

        class Tag(AsyncBaseDBModel):
            """Tag model for async M2M tests."""

            name: str

        class Article(AsyncBaseDBModel):
            """Article model for async M2M tests."""

            title: str
            tags: AsyncManyToMany[Tag] = AsyncManyToMany(
                Tag,
                related_name="articles",
            )

        db = AsyncSqliterDB(memory=True)
        await db.create_table(Tag)
        await db.create_table(Article)

        tag_a = await db.insert(Tag(name="python"))
        tag_b = await db.insert(Tag(name="sqlite"))
        article = await db.insert(Article(title="Guide"))

        manager = article.tags
        assert isinstance(manager, AsyncManyToManyManager)
        await manager.add(tag_a, tag_b)
        assert await manager.count() == 2
        fetched_tags = await manager.fetch_all()
        assert {tag.name for tag in fetched_tags} == {"python", "sqlite"}

        reverse_manager = tag_a.articles
        assert isinstance(reverse_manager, AsyncManyToManyManager)
        article_manager = cast(
            "AsyncManyToManyManager[Article]",
            reverse_manager,
        )
        reverse_articles = await article_manager.fetch_all()
        article_items = cast("list[Article]", reverse_articles)
        assert [item.title for item in article_items] == ["Guide"]

        prefetched = await (
            db.select(Article).prefetch_related("tags").fetch_one()
        )
        assert prefetched is not None
        prefetched_tags = prefetched.tags
        assert isinstance(prefetched_tags, AsyncPrefetchedM2MResult)
        assert await prefetched_tags.count() == 2

        await manager.remove(tag_b)
        assert await manager.count() == 1
        await manager.clear()
        assert await manager.count() == 0

        await db.close()
    finally:
        ModelRegistry.restore(state)


@pytest.mark.asyncio
async def test_async_m2m_manager_and_prefetched_edge_paths() -> None:
    """Async M2M helpers cover empty, delegated, and descriptor paths."""
    state = ModelRegistry.snapshot()
    try:

        class Tag(AsyncBaseDBModel):
            """Tag model for async M2M edge tests."""

            name: str

        class Article(AsyncBaseDBModel):
            """Article model for async M2M edge tests."""

            title: str
            tags: AsyncManyToMany[Tag] = AsyncManyToMany(
                Tag,
                related_name="articles",
            )

        assert isinstance(Article.tags, AsyncManyToMany)

        draft = Article(title="Draft")
        unresolved = AsyncManyToManyManager(
            instance=cast("AsyncM2MContext", draft),
            to_model=Tag,
            from_model=Article,
            junction_table="article_tags",
            db_context=None,
        )
        assert unresolved.sql_metadata.junction_table == "article_tags"
        assert await unresolved.fetch_all() == []
        assert await unresolved.fetch_one() is None
        assert await unresolved.count() == 0
        assert await unresolved.exists() is False
        with pytest.raises(
            ManyToManyIntegrityError,
            match="No database context",
        ):
            await unresolved.filter(name="python")

        db = AsyncSqliterDB(memory=True)
        await db.create_table(Tag)
        await db.create_table(Article)

        article = await db.insert(Article(title="Guide"))
        tag = await db.insert(Tag(name="python"))
        manager = cast("AsyncManyToManyManager[Tag]", article.tags)
        assert await manager.fetch_one() is None
        empty_query = await manager.filter(name="python")
        assert await empty_query.exists() is False

        prefetched = AsyncPrefetchedM2MResult([tag], manager)
        assert prefetched.sql_metadata == manager.sql_metadata
        assert await prefetched.fetch_all() == [tag]
        assert await prefetched.fetch_one() == tag
        assert await prefetched.count() == 1
        assert await prefetched.exists() is True
        await prefetched.add(tag)
        assert await manager.count() == 1
        found = await manager.fetch_one()
        assert found is not None
        assert found.name == "python"
        await prefetched.remove(Tag(name="missing"))
        await prefetched.set(tag)
        filtered = await prefetched.filter(name="python")
        assert await filtered.exists() is True
        await prefetched.clear()
        assert await manager.count() == 0

        with pytest.raises(
            ManyToManyIntegrityError,
            match="Related instance has no primary key",
        ):
            await manager.add(Tag(name="unsaved"))

        await db.close()
    finally:
        ModelRegistry.restore(state)


@pytest.mark.asyncio
async def test_async_prefetched_wrapper_refreshes_after_writes() -> None:
    """Async prefetched wrapper reflects delegated write operations."""
    state = ModelRegistry.snapshot()
    try:

        class Tag(AsyncBaseDBModel):
            """Tag model for async prefetched wrapper tests."""

            name: str

        class Article(AsyncBaseDBModel):
            """Article model for async prefetched wrapper tests."""

            title: str
            tags: AsyncManyToMany[Tag] = AsyncManyToMany(
                Tag,
                related_name="articles",
            )

        db = AsyncSqliterDB(memory=True)
        await db.create_table(Tag)
        await db.create_table(Article)

        article = await db.insert(Article(title="Guide"))
        tag1 = await db.insert(Tag(name="python"))
        tag2 = await db.insert(Tag(name="tutorial"))
        manager = cast("AsyncManyToManyManager[Tag]", article.tags)
        prefetched = AsyncPrefetchedM2MResult([tag1], manager)

        assert await prefetched.count() == 1
        await prefetched.add(tag1)
        assert await prefetched.count() == 1
        await prefetched.remove(Tag(name="missing"))
        assert await prefetched.count() == 1
        await prefetched.set(tag2)
        fetched = await prefetched.fetch_one()
        assert fetched is not None
        assert fetched.name == "tutorial"
        await prefetched.clear()
        assert await prefetched.fetch_all() == []
        await db.close()
    finally:
        ModelRegistry.restore(state)


@pytest.mark.asyncio
async def test_async_m2m_set_preserves_links_on_validation_failure() -> None:
    """Async M2M set keeps existing links when replacement validation fails."""
    state = ModelRegistry.snapshot()
    try:

        class Tag(AsyncBaseDBModel):
            """Tag model for async M2M set validation tests."""

            name: str

        class Article(AsyncBaseDBModel):
            """Article model for async M2M set validation tests."""

            title: str
            tags: AsyncManyToMany[Tag] = AsyncManyToMany(
                Tag,
                related_name="articles",
            )

        db = AsyncSqliterDB(memory=True)
        await db.create_table(Tag)
        await db.create_table(Article)

        article = await db.insert(Article(title="Guide"))
        replacement = await db.insert(Tag(name="keep"))
        manager = cast("AsyncManyToManyManager[Tag]", article.tags)
        await manager.add(replacement)

        with pytest.raises(
            ManyToManyIntegrityError,
            match="Related instance has no primary key",
        ):
            await manager.set(Tag(name="unsaved"))

        remaining = await manager.fetch_one()
        assert remaining is not None
        assert remaining.name == "keep"
        await db.close()
    finally:
        ModelRegistry.restore(state)


@pytest.mark.asyncio
async def test_async_m2m_manager_rollback_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Async M2M write failures rollback implicit transactions."""
    state = ModelRegistry.snapshot()
    try:

        class Tag(AsyncBaseDBModel):
            """Tag model for rollback tests."""

            name: str

        class Article(AsyncBaseDBModel):
            """Article model for rollback tests."""

            title: str
            tags: AsyncManyToMany[Tag] = AsyncManyToMany(
                Tag,
                related_name="articles",
            )

        db = AsyncSqliterDB(memory=True)
        await db.create_table(Tag)
        await db.create_table(Article)

        article = await db.insert(Article(title="Guide"))
        tag = await db.insert(Tag(name="python"))
        manager = cast("AsyncManyToManyManager[Tag]", article.tags)

        rollback_calls = {"count": 0}

        async def fake_rollback() -> None:
            rollback_calls["count"] += 1

        async def broken_execute(
            cursor: object,
            sql: str,
            params: tuple[object, ...] | tuple[int, ...],
        ) -> None:
            msg = "boom"
            raise RuntimeError(msg)

        monkeypatch.setattr(db.conn, "rollback", fake_rollback)
        monkeypatch.setattr(db, "execute_cursor", broken_execute)

        with pytest.raises(RuntimeError, match="boom"):
            await manager.add(tag)
        with pytest.raises(RuntimeError, match="boom"):
            await manager.remove(tag)
        with pytest.raises(RuntimeError, match="boom"):
            await manager.clear()
        assert rollback_calls["count"] == 3

        await db.close()
    finally:
        ModelRegistry.restore(state)


@pytest.mark.asyncio
async def test_async_m2m_symmetrical_and_descriptor_edge_paths() -> None:
    """Async M2M covers symmetrical ordering and descriptor edge cases."""
    state = ModelRegistry.snapshot()
    try:

        class Person(AsyncBaseDBModel):
            """Person model for symmetrical M2M tests."""

            name: str

        db = AsyncSqliterDB(memory=True)

        left = Person(name="Ada")
        left.pk = 5
        right = Person(name="Grace")
        right.pk = 2
        manager = AsyncManyToManyManager(
            instance=cast("AsyncM2MContext", left),
            to_model=Person,
            from_model=Person,
            junction_table="people_people",
            db_context=db,
            options=ManyToManyOptions(symmetrical=True),
        )

        calls: list[tuple[int, int]] = []

        async def fake_execute(
            cursor: object,
            sql: str,
            params: tuple[int, ...],
        ) -> None:
            if len(params) == 2:
                calls.append(params)

        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr(db, "execute_cursor", fake_execute)

        async def fake_maybe_commit() -> None:
            return None

        monkeypatch.setattr(db, "maybe_commit", fake_maybe_commit)

        await manager.add(right)
        await manager.remove(right)
        monkeypatch.undo()

        assert calls == [(2, 5), (2, 5)]

        no_pk_manager = AsyncManyToManyManager(
            instance=cast(
                "AsyncM2MContext",
                SimpleNamespace(pk=None, db_context=db),
            ),
            to_model=Person,
            from_model=Person,
            junction_table="people_people",
            db_context=db,
            options=ManyToManyOptions(symmetrical=True),
        )
        assert await no_pk_manager.fetch_all() == []
        assert await no_pk_manager.count() == 0
        with pytest.raises(
            ManyToManyIntegrityError,
            match="Instance has no primary key",
        ):
            no_pk_manager._get_instance_pk()
        with pytest.raises(
            ManyToManyIntegrityError,
            match="Instance has no primary key",
        ):
            await no_pk_manager.filter(name="Ada")

        reverse = AsyncReverseManyToMany(
            from_model=Person,
            to_model=Person,
            junction_table="people_people",
            related_name="friends",
            symmetrical=True,
        )
        assert reverse.__get__(None, Person) is reverse
        left.__dict__["_prefetch_cache"] = {"friends": [right]}
        prefetched = reverse.__get__(left, Person)
        assert isinstance(prefetched, AsyncPrefetchedM2MResult)

        class Broken(AsyncBaseDBModel):
            """Broken model for unresolved M2M access."""

            name: str
            links: AsyncManyToMany[Person] = AsyncManyToMany("Missing")

        broken = Broken(name="Oops")
        with pytest.raises(TypeError, match="target model is unresolved"):
            _ = broken.links
    finally:
        ModelRegistry.restore(state)


def test_async_model_registry_and_symmetrical_m2m_helpers() -> None:
    """Async model helper installation and symmetric M2M SQL stay correct."""
    state = ModelRegistry.snapshot()
    try:

        class Author(AsyncBaseDBModel):
            """Author model for registry helper tests."""

            name: str

        class Book(AsyncBaseDBModel):
            """Book model for registry helper tests."""

            title: str
            author: AsyncForeignKey[Author] = AsyncForeignKey(
                Author,
                on_delete="CASCADE",
                related_name="books",
            )

        class Person(AsyncBaseDBModel):
            """Person model for symmetric M2M helper tests."""

            name: str

        person = Person(name="Ada")
        person.pk = 1
        manager = AsyncManyToManyManager(
            instance=cast("AsyncM2MContext", person),
            to_model=Person,
            from_model=Person,
            junction_table="people_people",
            db_context=None,
            options=ManyToManyOptions(symmetrical=True),
        )
        assert manager.sql_metadata.symmetrical is True
        assert (
            'CASE WHEN "people_pk_left" = ?'
            in manager._select_related_ids_sql()
        )
        clear_sql, clear_params = manager._clear_sql()
        assert '"people_pk_left" = ? OR "people_pk_right" = ?' in clear_sql
        assert clear_params == (1, 1)
        assert (
            '"people_pk_left" = ? OR "people_pk_right" = ?'
            in manager._count_sql()
        )

        orphan_state = {"missing": [{"to_model": Author, "fk_field": "author"}]}
        Author._install_async_fk_reverse_accessors(orphan_state)
        Author._install_async_m2m_reverse_accessors(
            {"missing": [{"to_model": Author, "junction_table": "jt"}]}
        )

        cached_author = Author(name="Cached")
        assert cached_author.name == "Cached"

        reader = Book(title="Reader", author_id=1)
        reader.__dict__["_fk_cache"] = {"author": "cached"}
        assert cast("object", reader.author) == "cached"
    finally:
        ModelRegistry.restore(state)
