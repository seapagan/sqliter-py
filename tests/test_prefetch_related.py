"""Tests for prefetch_related() eager loading of reverse FK and M2M.

Tests cover reverse FK prefetching, M2M forward and reverse prefetching,
symmetrical self-referential M2M, combined chaining with filter/order/limit,
coexistence with select_related, error cases, and cache key differentiation.
"""

from __future__ import annotations

import pytest

from sqliter import SqliterDB
from sqliter.exceptions import InvalidPrefetchError
from sqliter.orm import BaseDBModel, ForeignKey, ManyToMany
from sqliter.orm.m2m import PrefetchedM2MResult
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
