"""Tests for prefetch_related() eager loading of reverse FK and M2M.

Tests cover reverse FK prefetching, M2M forward and reverse prefetching,
symmetrical self-referential M2M, combined chaining with filter/order/limit,
coexistence with select_related, error cases, and cache key differentiation.
"""

from __future__ import annotations

from typing import Any, cast

import pytest

from sqliter import SqliterDB
from sqliter.exceptions import InvalidPrefetchError
from sqliter.orm import BaseDBModel, ForeignKey, ManyToMany
from sqliter.orm.m2m import PrefetchedM2MResult, ReverseManyToMany
from sqliter.orm.query import PrefetchedResult, ReverseQuery

# ── Test models ──────────────────────────────────────────────────────


class Author(BaseDBModel):
    """Author model for testing."""

    name: str
    email: str


class Publisher(BaseDBModel):
    """Publisher model for testing."""

    name: str
    location: str


class Book(BaseDBModel):
    """Book model with FK to Author and Publisher."""

    title: str
    year: int
    author: ForeignKey[Author] = ForeignKey(Author, on_delete="CASCADE")
    publisher: ForeignKey[Publisher] = ForeignKey(
        Publisher, on_delete="SET NULL", null=True
    )


class Review(BaseDBModel):
    """Review model with FK to Author."""

    text: str
    author: ForeignKey[Author] = ForeignKey(Author, on_delete="CASCADE")


class Tag(BaseDBModel):
    """Tag model for M2M tests."""

    name: str


class Article(BaseDBModel):
    """Article model with M2M to Tag."""

    title: str
    tags: ManyToMany[Tag] = ManyToMany(Tag)


class Person(BaseDBModel):
    """Person model for symmetrical self-ref M2M."""

    name: str
    friends: ManyToMany[Person] = ManyToMany("Person", symmetrical=True)


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
def db() -> SqliterDB:
    """Create a test database with sample data."""
    database = SqliterDB(":memory:")
    database.create_table(Author)
    database.create_table(Publisher)
    database.create_table(Book)
    database.create_table(Review)
    database.create_table(Tag)
    database.create_table(Article)
    database.create_table(Person)

    # Authors
    a1 = database.insert(Author(name="Jane Austen", email="jane@example.com"))
    a2 = database.insert(
        Author(name="Charles Dickens", email="charles@example.com")
    )
    a3 = database.insert(
        Author(name="No Books Author", email="nobooks@example.com")
    )

    # Publisher
    p1 = database.insert(Publisher(name="Penguin", location="UK"))

    # Books
    database.insert(
        Book(
            title="Pride and Prejudice",
            year=1813,
            author_id=a1.pk,
            publisher_id=p1.pk,
        )
    )
    database.insert(
        Book(
            title="Sense and Sensibility",
            year=1811,
            author_id=a1.pk,
            publisher_id=p1.pk,
        )
    )
    database.insert(
        Book(
            title="Oliver Twist",
            year=1837,
            author_id=a2.pk,
            publisher_id=p1.pk,
        )
    )

    # Reviews
    database.insert(Review(text="Great writer!", author_id=a1.pk))
    database.insert(Review(text="Love her work", author_id=a1.pk))
    database.insert(Review(text="Classic", author_id=a2.pk))

    # Set up articles and tags for M2M tests
    t1 = database.insert(Tag(name="python"))
    t2 = database.insert(Tag(name="sqlite"))
    t3 = database.insert(Tag(name="orm"))
    t4 = database.insert(Tag(name="unused"))

    art1 = database.insert(Article(title="SQLiter Guide"))
    art2 = database.insert(Article(title="Python Tips"))
    art3 = database.insert(Article(title="No Tags"))

    art1.tags.add(t1, t2, t3)
    art2.tags.add(t1)

    # Symmetrical M2M: Persons/Friends
    pe1 = database.insert(Person(name="Alice"))
    pe2 = database.insert(Person(name="Bob"))
    pe3 = database.insert(Person(name="Carol"))
    pe4 = database.insert(Person(name="Loner"))

    pe1.friends.add(pe2, pe3)
    pe2.friends.add(pe3)

    # Suppress unused variable warnings — data is in the DB
    _ = (a3, t4, art3, pe4)

    return database


# ── Reverse FK prefetch tests ────────────────────────────────────────


class TestReverseFKPrefetch:
    """Reverse FK prefetch_related tests."""

    def test_basic_reverse_fk_prefetch(self, db: SqliterDB) -> None:
        """Prefetching reverse FK populates _prefetch_cache."""
        authors = db.select(Author).prefetch_related("books").fetch_all()

        for author in authors:
            cache = author.__dict__.get("_prefetch_cache", {})
            assert "books" in cache

    def test_access_prefetched_data(self, db: SqliterDB) -> None:
        """Accessing prefetched relationship returns PrefetchedResult."""
        authors = db.select(Author).prefetch_related("books").fetch_all()

        jane = next(a for a in authors if a.name == "Jane Austen")
        result = jane.books
        assert isinstance(result, PrefetchedResult)
        books = result.fetch_all()
        assert len(books) == 2
        titles = {b.title for b in books}
        assert "Pride and Prejudice" in titles

    def test_prefetched_count_and_exists(self, db: SqliterDB) -> None:
        """Prefetched .count() and .exists() work without DB query."""
        authors = db.select(Author).prefetch_related("books").fetch_all()

        jane = next(a for a in authors if a.name == "Jane Austen")
        assert jane.books.count() == 2
        assert jane.books.exists() is True

        nobooks = next(a for a in authors if a.name == "No Books Author")
        assert nobooks.books.count() == 0
        assert nobooks.books.exists() is False

    def test_prefetched_fetch_one(self, db: SqliterDB) -> None:
        """Prefetched .fetch_one() returns first or None."""
        authors = db.select(Author).prefetch_related("books").fetch_all()

        jane = next(a for a in authors if a.name == "Jane Austen")
        book = jane.books.fetch_one()
        assert book is not None

        nobooks = next(a for a in authors if a.name == "No Books Author")
        assert nobooks.books.fetch_one() is None

    def test_prefetched_filter_falls_back_to_db(self, db: SqliterDB) -> None:
        """Prefetched .filter() falls back to a DB query."""
        authors = db.select(Author).prefetch_related("books").fetch_all()

        jane = next(a for a in authors if a.name == "Jane Austen")
        result = jane.books.filter(year__gt=1812)
        # filter() returns a ReverseQuery (falls back to DB)
        assert isinstance(result, ReverseQuery)
        filtered = result.fetch_all()
        assert len(filtered) == 1
        assert filtered[0].title == "Pride and Prejudice"

    def test_multiple_prefetch_paths(self, db: SqliterDB) -> None:
        """Multiple prefetch paths populate all caches."""
        authors = (
            db.select(Author).prefetch_related("books", "reviews").fetch_all()
        )

        jane = next(a for a in authors if a.name == "Jane Austen")
        assert jane.books.count() == 2
        assert jane.reviews.count() == 2

    def test_no_related_objects_get_empty_list(self, db: SqliterDB) -> None:
        """Instances with no related objects get [] in cache."""
        authors = db.select(Author).prefetch_related("books").fetch_all()

        nobooks = next(a for a in authors if a.name == "No Books Author")
        cache = nobooks.__dict__.get("_prefetch_cache", {})
        assert cache["books"] == []

    def test_combined_with_filter(self, db: SqliterDB) -> None:
        """prefetch_related works after filter."""
        authors = (
            db.select(Author)
            .filter(name="Jane Austen")
            .prefetch_related("books")
            .fetch_all()
        )

        assert len(authors) == 1
        assert authors[0].books.count() == 2

    def test_combined_with_order_and_limit(self, db: SqliterDB) -> None:
        """Chaining with order and limit works."""
        authors = (
            db.select(Author)
            .prefetch_related("books")
            .order("name")
            .limit(2)
            .fetch_all()
        )

        assert len(authors) == 2
        for a in authors:
            assert "books" in a.__dict__.get("_prefetch_cache", {})

    def test_fetch_one_with_prefetch(self, db: SqliterDB) -> None:
        """fetch_one() with prefetch wraps single instance."""
        author = (
            db.select(Author)
            .filter(name="Jane Austen")
            .prefetch_related("books")
            .fetch_one()
        )

        assert author is not None
        assert isinstance(author.books, PrefetchedResult)
        assert author.books.count() == 2

    def test_combined_with_select_related(self, db: SqliterDB) -> None:
        """prefetch_related and select_related can coexist."""
        books = (
            db.select(Book)
            .select_related("author")
            .prefetch_related()
            .fetch_all()
        )

        # select_related populates _fk_cache
        for book in books:
            fk_cache = getattr(book, "_fk_cache", {})
            assert "author" in fk_cache


# ── M2M prefetch tests ──────────────────────────────────────────────


class TestM2MPrefetch:
    """M2M prefetch_related tests."""

    def test_m2m_forward_prefetch(self, db: SqliterDB) -> None:
        """Forward M2M prefetch — articles with tags prefetched."""
        articles = db.select(Article).prefetch_related("tags").fetch_all()

        guide = next(a for a in articles if a.title == "SQLiter Guide")
        result = guide.tags
        assert isinstance(result, PrefetchedM2MResult)
        tags = result.fetch_all()
        assert len(tags) == 3
        tag_names = {t.name for t in tags}
        assert "python" in tag_names
        assert "sqlite" in tag_names

    def test_m2m_reverse_prefetch(self, db: SqliterDB) -> None:
        """Reverse M2M prefetch — tags with articles prefetched."""
        tags = db.select(Tag).prefetch_related("articles").fetch_all()

        python_tag = next(t for t in tags if t.name == "python")
        result = python_tag.articles
        assert isinstance(result, PrefetchedM2MResult)
        articles = result.fetch_all()
        assert len(articles) == 2

        unused_tag = next(t for t in tags if t.name == "unused")
        assert unused_tag.articles.count() == 0

    def test_m2m_prefetched_count_exists(self, db: SqliterDB) -> None:
        """Prefetched M2M .count() and .exists() work."""
        articles = db.select(Article).prefetch_related("tags").fetch_all()

        guide = next(a for a in articles if a.title == "SQLiter Guide")
        assert guide.tags.count() == 3
        assert guide.tags.exists() is True

        notags = next(a for a in articles if a.title == "No Tags")
        assert notags.tags.count() == 0
        assert notags.tags.exists() is False

    def test_m2m_prefetched_fetch_one(self, db: SqliterDB) -> None:
        """Prefetched M2M .fetch_one() returns first or None."""
        articles = db.select(Article).prefetch_related("tags").fetch_all()

        guide = next(a for a in articles if a.title == "SQLiter Guide")
        tag = guide.tags.fetch_one()
        assert tag is not None

        notags = next(a for a in articles if a.title == "No Tags")
        assert notags.tags.fetch_one() is None

    def test_m2m_prefetched_filter_falls_back(self, db: SqliterDB) -> None:
        """Prefetched M2M .filter() falls back to DB query."""
        articles = db.select(Article).prefetch_related("tags").fetch_all()

        guide = next(a for a in articles if a.title == "SQLiter Guide")
        query = guide.tags.filter(name="python")
        results = query.fetch_all()
        assert len(results) == 1
        assert results[0].name == "python"

    def test_m2m_prefetched_write_delegates(self, db: SqliterDB) -> None:
        """Prefetched M2M write operations delegate to real manager."""
        articles = db.select(Article).prefetch_related("tags").fetch_all()

        guide = next(a for a in articles if a.title == "SQLiter Guide")
        assert isinstance(guide.tags, PrefetchedM2MResult)

        # Add a new tag through the prefetched wrapper
        new_tag = db.insert(Tag(name="new_tag"))
        guide.tags.add(new_tag)

        # Verify through a fresh query
        fresh = db.select(Article).filter(pk=guide.pk).fetch_one()
        assert fresh is not None
        fresh_tags = fresh.tags.fetch_all()
        assert len(fresh_tags) == 4

    def test_m2m_prefetched_remove_delegates(self, db: SqliterDB) -> None:
        """Prefetched M2M .remove() delegates to real manager."""
        articles = db.select(Article).prefetch_related("tags").fetch_all()

        guide = next(a for a in articles if a.title == "SQLiter Guide")
        assert isinstance(guide.tags, PrefetchedM2MResult)

        # Remove a tag through the prefetched wrapper
        python_tag = next(
            t for t in guide.tags.fetch_all() if t.name == "python"
        )
        guide.tags.remove(python_tag)

        # Verify through a fresh query
        fresh = db.select(Article).filter(pk=guide.pk).fetch_one()
        assert fresh is not None
        fresh_tags = fresh.tags.fetch_all()
        assert len(fresh_tags) == 2
        assert "python" not in {t.name for t in fresh_tags}

    def test_m2m_prefetched_clear_delegates(self, db: SqliterDB) -> None:
        """Prefetched M2M .clear() delegates to real manager."""
        articles = db.select(Article).prefetch_related("tags").fetch_all()

        guide = next(a for a in articles if a.title == "SQLiter Guide")
        assert isinstance(guide.tags, PrefetchedM2MResult)
        assert guide.tags.count() == 3

        guide.tags.clear()

        # Verify through a fresh query
        fresh = db.select(Article).filter(pk=guide.pk).fetch_one()
        assert fresh is not None
        assert fresh.tags.count() == 0

    def test_m2m_prefetched_set_delegates(self, db: SqliterDB) -> None:
        """Prefetched M2M .set() delegates to real manager."""
        articles = db.select(Article).prefetch_related("tags").fetch_all()

        guide = next(a for a in articles if a.title == "SQLiter Guide")
        assert isinstance(guide.tags, PrefetchedM2MResult)
        assert guide.tags.count() == 3

        # Replace all tags with just one
        new_tag = db.insert(Tag(name="replacement"))
        guide.tags.set(new_tag)

        # Verify through a fresh query
        fresh = db.select(Article).filter(pk=guide.pk).fetch_one()
        assert fresh is not None
        fresh_tags = fresh.tags.fetch_all()
        assert len(fresh_tags) == 1
        assert fresh_tags[0].name == "replacement"

    def test_symmetrical_self_ref_m2m_prefetch(self, db: SqliterDB) -> None:
        """Symmetrical self-referential M2M prefetch works."""
        people = db.select(Person).prefetch_related("friends").fetch_all()

        alice = next(p for p in people if p.name == "Alice")
        friends = alice.friends.fetch_all()
        friend_names = {f.name for f in friends}
        assert "Bob" in friend_names
        assert "Carol" in friend_names

        # Bob should also see Alice and Carol
        bob = next(p for p in people if p.name == "Bob")
        bob_friends = bob.friends.fetch_all()
        bob_friend_names = {f.name for f in bob_friends}
        assert "Alice" in bob_friend_names
        assert "Carol" in bob_friend_names

        # Loner has no friends
        loner = next(p for p in people if p.name == "Loner")
        assert loner.friends.count() == 0

    def test_empty_queryset_prefetch(self, db: SqliterDB) -> None:
        """Prefetch on empty queryset returns empty lists."""
        authors = (
            db.select(Author)
            .filter(name="NonExistent")
            .prefetch_related("books")
            .fetch_all()
        )

        assert authors == []


# ── Error cases ──────────────────────────────────────────────────────


class TestPrefetchErrors:
    """Error handling for prefetch_related."""

    def test_invalid_path_raises_error(self, db: SqliterDB) -> None:
        """Invalid prefetch path raises InvalidPrefetchError."""
        with pytest.raises(InvalidPrefetchError):
            db.select(Author).prefetch_related("nonexistent")

    def test_forward_fk_path_raises_error(self, db: SqliterDB) -> None:
        """Forward FK path raises InvalidPrefetchError."""
        with pytest.raises(InvalidPrefetchError):
            db.select(Book).prefetch_related("author")

    def test_prefetch_skips_instances_without_pks(self, db: SqliterDB) -> None:
        """Prefetch is a no-op when all instances lack PKs."""
        query = db.select(Author).prefetch_related("books")

        # Create unsaved instances (pk=None)
        unsaved = [
            Author(name="Ghost", email="ghost@example.com"),
            Author(name="Phantom", email="phantom@example.com"),
        ]
        # Manually invoke _execute_prefetch with pk-less instances
        query._execute_prefetch(unsaved)

        # No cache should be populated (no error raised either)
        for inst in unsaved:
            assert not inst.__dict__.get("_prefetch_cache")

    def test_resolve_m2m_columns_returns_none_for_unknown(
        self, db: SqliterDB
    ) -> None:
        """_resolve_m2m_columns returns None for unsupported descriptor."""
        query = db.select(Article).prefetch_related("tags")

        # Pass a plain object as descriptor — not ManyToMany/Reverse
        result = query._resolve_m2m_columns(object(), "articles")
        assert result is None

    def test_prefetch_m2m_skips_unresolvable_descriptor(
        self, db: SqliterDB
    ) -> None:
        """_prefetch_m2m_for_model is a no-op for unresolvable descriptors."""
        articles = db.select(Article).prefetch_related("tags").fetch_all()
        guide = next(a for a in articles if a.title == "SQLiter Guide")

        query = db.select(Article).prefetch_related("tags")
        pks = [guide.pk]

        # Call _prefetch_m2m_for_model with an unsupported descriptor
        query._prefetch_m2m_for_model(
            "tags", object(), articles, pks, owner_model=Article
        )

        # Original prefetch cache should be unaffected
        cache = guide.__dict__.get("_prefetch_cache", {})
        assert cache.get("tags") is not None


# ── Cache key tests ──────────────────────────────────────────────────


class TestPrefetchCacheKey:
    """Cache key differentiation with prefetch_related."""

    def test_cache_key_differs_with_prefetch(self, db: SqliterDB) -> None:
        """Cache key includes prefetch_related in its computation."""
        q1 = db.select(Author)
        q2 = db.select(Author).prefetch_related("books")

        key1 = q1._make_cache_key(fetch_one=False)
        key2 = q2._make_cache_key(fetch_one=False)

        assert key1 != key2


# ── Nested prefetch models ──────────────────────────────────────────


class Category(BaseDBModel):
    """Category model for nested M2M tests."""

    name: str


class BookWithCategories(BaseDBModel):
    """Book with FK to Author and M2M to Category."""

    title: str
    year: int
    author: ForeignKey[Author] = ForeignKey(
        Author, on_delete="CASCADE", related_name="authored_books"
    )
    categories: ManyToMany[Category] = ManyToMany(
        Category, related_name="books_in_category"
    )


class Comment(BaseDBModel):
    """Comment with FK to Article."""

    text: str
    article: ForeignKey[Article] = ForeignKey(
        Article, on_delete="CASCADE", related_name="comments"
    )


class Reply(BaseDBModel):
    """Reply with FK to Comment."""

    text: str
    comment: ForeignKey[Comment] = ForeignKey(
        Comment, on_delete="CASCADE", related_name="replies"
    )


# ── Nested prefetch fixture ────────────────────────────────────────


@pytest.fixture
def nested_db() -> SqliterDB:
    """Create a test database with nested relationship data."""
    database = SqliterDB(":memory:")
    database.create_table(Author)
    database.create_table(Category)
    database.create_table(BookWithCategories)
    database.create_table(Tag)
    database.create_table(Article)
    database.create_table(Comment)
    database.create_table(Reply)
    database.create_table(Review)

    # Authors
    a1 = database.insert(Author(name="Jane Austen", email="jane@example.com"))
    a2 = database.insert(
        Author(name="Charles Dickens", email="charles@example.com")
    )
    a3 = database.insert(
        Author(name="No Books Author", email="nobooks@example.com")
    )

    # Categories
    c1 = database.insert(Category(name="Fiction"))
    c2 = database.insert(Category(name="Classic"))
    c3 = database.insert(Category(name="Drama"))

    # BooksWithCategories
    b1 = database.insert(
        BookWithCategories(
            title="Pride and Prejudice", year=1813, author_id=a1.pk
        )
    )
    b2 = database.insert(
        BookWithCategories(
            title="Sense and Sensibility", year=1811, author_id=a1.pk
        )
    )
    b3 = database.insert(
        BookWithCategories(title="Oliver Twist", year=1837, author_id=a2.pk)
    )

    # Assign categories
    b1.categories.add(c1, c2)
    b2.categories.add(c1)
    b3.categories.add(c1, c3)

    # Tags and Articles with comments
    t1 = database.insert(Tag(name="python"))
    t2 = database.insert(Tag(name="sqlite"))

    art1 = database.insert(Article(title="SQLiter Guide"))
    art2 = database.insert(Article(title="Python Tips"))
    art1.tags.add(t1, t2)
    art2.tags.add(t1)

    # Comments on articles
    com1 = database.insert(Comment(text="Great guide!", article_id=art1.pk))
    com2 = database.insert(Comment(text="Very helpful", article_id=art1.pk))
    com3 = database.insert(Comment(text="Nice tips", article_id=art2.pk))

    # Replies on comments
    database.insert(Reply(text="Totally agree", comment_id=com1.pk))
    database.insert(Reply(text="Same here", comment_id=com1.pk))
    database.insert(Reply(text="Thanks!", comment_id=com3.pk))

    # Reviews for Author
    database.insert(Review(text="Love her work", author_id=a1.pk))

    # Suppress unused variable warnings
    _ = (a3, c3, b3, t2, com2)

    return database


# ── Nested prefetch tests ───────────────────────────────────────────


class TestNestedPrefetch:
    """Tests for nested prefetch_related() paths."""

    def test_two_level_reverse_fk_then_m2m(self, nested_db: SqliterDB) -> None:
        """Author -> authored_books -> categories (reverse FK then M2M)."""
        authors = (
            nested_db.select(Author)
            .prefetch_related("authored_books__categories")
            .fetch_all()
        )

        jane = next(a for a in authors if a.name == "Jane Austen")
        books = jane.authored_books.fetch_all()
        assert len(books) == 2

        pride = next(b for b in books if b.title == "Pride and Prejudice")
        cats = pride.categories.fetch_all()
        cat_names = {c.name for c in cats}
        assert "Fiction" in cat_names
        assert "Classic" in cat_names

    def test_two_level_reverse_m2m_then_reverse_fk(
        self, nested_db: SqliterDB
    ) -> None:
        """Tag -> articles (reverse M2M) -> comments (reverse FK)."""
        tags = (
            nested_db.select(Tag)
            .prefetch_related("articles__comments")
            .fetch_all()
        )

        python_tag = next(t for t in tags if t.name == "python")
        articles = python_tag.articles.fetch_all()
        assert len(articles) == 2

        guide = next(a for a in articles if a.title == "SQLiter Guide")
        comments = guide.comments.fetch_all()
        assert len(comments) == 2
        comment_texts = {c.text for c in comments}
        assert "Great guide!" in comment_texts

    def test_mixed_nested_and_flat_paths(self, nested_db: SqliterDB) -> None:
        """Mix of nested and flat paths on the same query."""
        authors = (
            nested_db.select(Author)
            .prefetch_related("authored_books__categories", "reviews")
            .fetch_all()
        )

        jane = next(a for a in authors if a.name == "Jane Austen")

        # Flat path
        reviews = jane.reviews.fetch_all()
        assert len(reviews) == 1

        # Nested path
        books = jane.authored_books.fetch_all()
        pride = next(b for b in books if b.title == "Pride and Prejudice")
        cats = pride.categories.fetch_all()
        assert len(cats) == 2

    def test_overlapping_paths_deduplicated(self, nested_db: SqliterDB) -> None:
        """Both 'authored_books' and 'authored_books__categories' work."""
        authors = (
            nested_db.select(Author)
            .prefetch_related("authored_books", "authored_books__categories")
            .fetch_all()
        )

        jane = next(a for a in authors if a.name == "Jane Austen")
        books = jane.authored_books.fetch_all()
        assert len(books) == 2

        pride = next(b for b in books if b.title == "Pride and Prejudice")
        cats = pride.categories.fetch_all()
        assert len(cats) == 2

    def test_nested_prefetch_with_filter(self, nested_db: SqliterDB) -> None:
        """Nested prefetch combined with filter on the root query."""
        authors = (
            nested_db.select(Author)
            .filter(name="Jane Austen")
            .prefetch_related("authored_books__categories")
            .fetch_all()
        )

        assert len(authors) == 1
        books = authors[0].authored_books.fetch_all()
        assert len(books) == 2

    def test_nested_prefetch_with_fetch_one(self, nested_db: SqliterDB) -> None:
        """Nested prefetch with fetch_one on the root query."""
        author = (
            nested_db.select(Author)
            .filter(name="Jane Austen")
            .prefetch_related("authored_books__categories")
            .fetch_one()
        )

        assert author is not None
        books = author.authored_books.fetch_all()
        assert len(books) == 2

        pride = next(b for b in books if b.title == "Pride and Prejudice")
        cats = pride.categories.fetch_all()
        assert len(cats) == 2

    def test_empty_intermediate_level(self, nested_db: SqliterDB) -> None:
        """Author with no books — nested categories is empty."""
        authors = (
            nested_db.select(Author)
            .prefetch_related("authored_books__categories")
            .fetch_all()
        )

        nobooks = next(a for a in authors if a.name == "No Books Author")
        books = nobooks.authored_books.fetch_all()
        assert books == []

    def test_cache_populated_at_each_level(self, nested_db: SqliterDB) -> None:
        """_prefetch_cache is set on both parent and child instances."""
        authors = (
            nested_db.select(Author)
            .prefetch_related("authored_books__categories")
            .fetch_all()
        )

        jane = next(a for a in authors if a.name == "Jane Austen")
        author_cache = jane.__dict__.get("_prefetch_cache", {})
        assert "authored_books" in author_cache

        for book in author_cache["authored_books"]:
            book_cache = book.__dict__.get("_prefetch_cache", {})
            assert "categories" in book_cache

    def test_invalid_first_segment(self, nested_db: SqliterDB) -> None:
        """Invalid first segment raises InvalidPrefetchError."""
        with pytest.raises(InvalidPrefetchError):
            nested_db.select(Author).prefetch_related("nonexistent__books")

    def test_invalid_second_segment(self, nested_db: SqliterDB) -> None:
        """Invalid second segment raises InvalidPrefetchError."""
        with pytest.raises(InvalidPrefetchError):
            nested_db.select(Author).prefetch_related(
                "authored_books__nonexistent"
            )

    def test_unresolved_m2m_forward_ref(self) -> None:
        """Unresolved ManyToMany forward ref raises InvalidPrefetchError."""

        class LocalTag(BaseDBModel):
            name: str

        class LocalPost(BaseDBModel):
            title: str
            tags: ManyToMany[Any] = ManyToMany("NeverDefinedModel")

        db = SqliterDB(":memory:")
        db.create_table(LocalTag)
        db.create_table(LocalPost)

        with pytest.raises(InvalidPrefetchError):
            db.select(LocalPost).prefetch_related("tags")

    def test_unresolved_reverse_m2m_forward_ref(self) -> None:
        """Unresolved reverse M2M forward ref raises InvalidPrefetchError."""

        class LocalHost(BaseDBModel):
            name: str

        LocalHost.ghosts = ReverseManyToMany(  # type: ignore[attr-defined]
            from_model=cast("type[Any]", "GhostModel"),
            to_model=LocalHost,
            junction_table="ghost_host",
            related_name="ghosts",
        )

        db = SqliterDB(":memory:")
        db.create_table(LocalHost)

        with pytest.raises(InvalidPrefetchError):
            db.select(LocalHost).prefetch_related("ghosts")

    def test_three_levels_deep(self, nested_db: SqliterDB) -> None:
        """Three-level nesting: Tag -> articles -> comments -> replies."""
        tags = (
            nested_db.select(Tag)
            .prefetch_related("articles__comments__replies")
            .fetch_all()
        )

        python_tag = next(t for t in tags if t.name == "python")
        articles = python_tag.articles.fetch_all()
        guide = next(a for a in articles if a.title == "SQLiter Guide")
        comments = guide.comments.fetch_all()
        assert len(comments) == 2

        first_comment = next(c for c in comments if c.text == "Great guide!")
        replies = first_comment.replies.fetch_all()
        assert len(replies) == 2

    def test_cache_key_differs_for_nested(self, nested_db: SqliterDB) -> None:
        """Nested path produces a different cache key than flat path."""
        q1 = nested_db.select(Author).prefetch_related("authored_books")
        q2 = nested_db.select(Author).prefetch_related(
            "authored_books__categories"
        )

        key1 = q1._make_cache_key(fetch_one=False)
        key2 = q2._make_cache_key(fetch_one=False)
        assert key1 != key2

    def test_nested_prefetch_with_select_related(
        self, nested_db: SqliterDB
    ) -> None:
        """Nested prefetch coexists with select_related."""
        books = (
            nested_db.select(BookWithCategories)
            .select_related("author")
            .prefetch_related("categories")
            .fetch_all()
        )

        for book in books:
            fk_cache = getattr(book, "_fk_cache", {})
            assert "author" in fk_cache
            pf_cache = book.__dict__.get("_prefetch_cache", {})
            assert "categories" in pf_cache

    def test_all_parents_lack_books_nested(self, nested_db: SqliterDB) -> None:
        """Nested prefetch where all parents have empty intermediate."""
        authors = (
            nested_db.select(Author)
            .filter(name="No Books Author")
            .prefetch_related("authored_books__categories")
            .fetch_all()
        )

        assert len(authors) == 1
        nobooks = authors[0]
        assert nobooks.authored_books.fetch_all() == []

    def test_prefetch_segment_skips_pkless_instances(
        self, nested_db: SqliterDB
    ) -> None:
        """_prefetch_segment is a no-op when all instances lack PKs."""
        query = nested_db.select(Author).prefetch_related("authored_books")
        unsaved = [
            Author(name="Ghost", email="ghost@example.com"),
            Author(name="Phantom", email="phantom@example.com"),
        ]
        query._prefetch_segment("authored_books", unsaved, Author)

        for inst in unsaved:
            assert not inst.__dict__.get("_prefetch_cache")
