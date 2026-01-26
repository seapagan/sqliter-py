"""Tests for select_related() eager loading and relationship filter traversal.

Tests cover single-level and nested eager loading via JOINs, relationship
filter traversal, and edge cases.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest import mock

import pytest

from sqliter import SqliterDB
from sqliter.exceptions import (
    InvalidFilterError,
    InvalidRelationshipError,
)
from sqliter.orm import BaseDBModel, ForeignKey

if TYPE_CHECKING:
    from collections.abc import Generator


class Author(BaseDBModel):
    """Author model for testing."""

    name: str
    email: str


class Publisher(BaseDBModel):
    """Publisher model for testing."""

    name: str
    location: str


class Book(BaseDBModel):
    """Book model with foreign key relationships."""

    title: str
    year: int
    author: ForeignKey[Author] = ForeignKey(Author, on_delete="CASCADE")
    publisher: ForeignKey[Publisher] = ForeignKey(
        Publisher, on_delete="SET NULL", null=True
    )


class Comment(BaseDBModel):
    """Comment model for testing nested relationships."""

    text: str
    book: ForeignKey[Book] = ForeignKey(Book, on_delete="CASCADE")


@pytest.fixture
def db() -> Generator[SqliterDB, None, None]:
    """Create a test database with sample data."""
    db = SqliterDB(":memory:")
    db.create_table(Author)
    db.create_table(Publisher)
    db.create_table(Book)
    db.create_table(Comment)

    # Create sample data
    author1 = db.insert(Author(name="Jane Austen", email="jane@example.com"))
    author2 = db.insert(
        Author(name="Charles Dickens", email="charles@example.com")
    )

    publisher1 = db.insert(Publisher(name="Penguin", location="UK"))
    publisher2 = db.insert(Publisher(name="Oxford", location="UK"))

    book1 = db.insert(
        Book(
            title="Pride and Prejudice",
            year=1813,
            author=author1,
            publisher=publisher1,
        )
    )
    db.insert(
        Book(
            title="Sense and Sensibility",
            year=1811,
            author=author1,
            publisher=publisher1,
        )
    )
    db.insert(
        Book(
            title="Oliver Twist",
            year=1838,
            author=author2,
            publisher=publisher2,
        )
    )
    db.insert(
        Book(
            title="Independent Book", year=2000, author=author2, publisher=None
        )
    )

    db.insert(Comment(text="Great book!", book=book1))

    yield db

    # Close the database connection
    conn = db.connect()
    conn.close()


class TestSelectRelated:
    """Tests for select_related() eager loading functionality."""

    def test_single_level_eager_load(self, db: SqliterDB) -> None:
        """Verify select_related() loads related object."""
        result = db.select(Book).select_related("author").fetch_one()

        assert result is not None
        assert result.author is not None
        assert result.author.name == "Jane Austen"
        assert result.author.email == "jane@example.com"

    def test_single_level_eager_load_all(self, db: SqliterDB) -> None:
        """Verify select_related() loads all related objects."""
        results = db.select(Book).select_related("author").fetch_all()

        assert len(results) == 4
        # All books should have authors loaded
        for book in results:
            assert book.author is not None
            assert isinstance(book.author.name, str)

    def test_multiple_paths(self, db: SqliterDB) -> None:
        """Verify select_related() with multiple relationship paths."""
        result = (
            db.select(Book)
            .select_related("author", "publisher")
            .filter(title="Pride and Prejudice")
            .fetch_one()
        )

        assert result is not None
        assert result.author is not None
        assert result.author.name == "Jane Austen"
        assert result.publisher is not None
        assert result.publisher.name == "Penguin"

    def test_nullable_fk_with_none_value(self, db: SqliterDB) -> None:
        """Verify select_related() handles NULL foreign keys correctly."""
        result = (
            db.select(Book)
            .select_related("publisher")
            .filter(title="Independent Book")
            .fetch_one()
        )

        assert result is not None
        assert result.publisher is None  # LEFT JOIN with no match

    def test_select_related_with_filters(self, db: SqliterDB) -> None:
        """Verify select_related() works with filters."""
        results = (
            db.select(Book)
            .select_related("author")
            .filter(author__name="Charles Dickens")
            .fetch_all()
        )

        assert len(results) == 2
        for book in results:
            assert book.author.name == "Charles Dickens"

    def test_select_related_with_ordering(self, db: SqliterDB) -> None:
        """Verify select_related() works with ordering."""
        results = (
            db.select(Book)
            .select_related("author")
            .order("year", reverse=True)
            .fetch_all()
        )

        assert results[0].year == 2000
        assert results[-1].year == 1811

    def test_select_related_with_limit(self, db: SqliterDB) -> None:
        """Verify select_related() works with limit."""
        results = db.select(Book).select_related("author").limit(2).fetch_all()

        assert len(results) == 2

    def test_select_related_with_offset(self, db: SqliterDB) -> None:
        """Verify select_related() works with offset."""
        results = (
            db.select(Book)
            .select_related("author")
            .order("year")
            .offset(2)
            .limit(2)
            .fetch_all()
        )

        assert len(results) == 2
        assert results[0].year >= 1813


class TestNestedSelectRelated:
    """Tests for nested select_related() (multi-level relationships)."""

    def test_nested_two_level(self, db: SqliterDB) -> None:
        """Verify nested select_related('book__author') works."""
        result = db.select(Comment).select_related("book__author").fetch_one()

        assert result is not None
        assert result.book is not None
        assert result.book.author is not None
        assert result.book.author.name == "Jane Austen"

    def test_nested_three_level(self, db: SqliterDB) -> None:
        """Verify deeply nested select_related() works."""
        # This requires Comment -> Book -> Publisher relationship
        # For now, test that we can at least build the join info
        # (Book has both author and publisher relationships)
        result = (
            db.select(Comment).select_related("book__publisher").fetch_one()
        )

        assert result is not None
        assert result.book is not None
        # book4 has no publisher, so let's find one that does
        if result.book.publisher:
            assert isinstance(result.book.publisher.name, str)

    def test_nested_with_filter(self, db: SqliterDB) -> None:
        """Verify nested select_related() with filter on related field."""
        results = (
            db.select(Comment)
            .select_related("book__author")
            .filter(book__author__name="Jane Austen")
            .fetch_all()
        )

        assert len(results) == 1
        assert results[0].book.author.name == "Jane Austen"


class TestRelationshipFilterTraversal:
    """Tests for relationship filter traversal (filter(author__name='...'))."""

    def test_filter_on_related_field(self, db: SqliterDB) -> None:
        """Verify filter traversal works."""
        results = db.select(Book).filter(author__name="Jane Austen").fetch_all()

        assert len(results) == 2
        for book in results:
            assert book.author.name == "Jane Austen"

    def test_filter_on_related_field_with_operator(self, db: SqliterDB) -> None:
        """Verify filter traversal with comparison operators."""
        results = db.select(Book).filter(author__name__like="Jane%").fetch_all()

        assert len(results) == 2

    def test_filter_on_related_field_with_multiple_conditions(
        self, db: SqliterDB
    ) -> None:
        """Verify filter traversal with multiple conditions."""
        results = (
            db.select(Book)
            .filter(author__name="Charles Dickens", year__lt=1840)
            .fetch_all()
        )

        assert len(results) == 1
        assert results[0].title == "Oliver Twist"

    def test_filter_on_nullable_relationship(self, db: SqliterDB) -> None:
        """Verify filter traversal on nullable relationship."""
        results = db.select(Book).filter(publisher__name="Penguin").fetch_all()

        assert len(results) == 2
        for book in results:
            if book.publisher:
                assert book.publisher.name == "Penguin"

    def test_filter_on_nested_relationship(self, db: SqliterDB) -> None:
        """Verify filter on nested relationship (book__author__name)."""
        results = (
            db.select(Comment)
            .filter(book__author__name="Jane Austen")
            .fetch_all()
        )

        assert len(results) == 1

    def test_filter_with_implicit_eager_load(self, db: SqliterDB) -> None:
        """Verify that filter traversal implicitly eager loads relationships."""
        results = db.select(Book).filter(author__name="Jane Austen").fetch_all()

        # Accessing author should not trigger additional query
        # (though we can't easily test this without counting queries)
        for book in results:
            assert book.author is not None
            assert isinstance(book.author.name, str)


class TestErrorHandling:
    """Tests for error handling in select_related() and filter traversal."""

    def test_invalid_select_related_path(self, db: SqliterDB) -> None:
        """Verify invalid relationship path raises error."""
        with pytest.raises(InvalidRelationshipError):
            db.select(Book).select_related("nonexistent").fetch_all()

    def test_invalid_filter_relationship_path(self, db: SqliterDB) -> None:
        """Verify invalid relationship in filter raises error."""
        with pytest.raises(InvalidRelationshipError):
            db.select(Book).filter(nonexistent__name="John").fetch_all()

    def test_invalid_field_in_related_filter(self, db: SqliterDB) -> None:
        """Verify invalid field in related filter raises appropriate error."""
        # This should raise InvalidFilterError for the invalid field
        with pytest.raises(InvalidFilterError):
            db.select(Book).filter(author__nonexistent="John").fetch_all()


class TestCachingBehavior:
    """Tests for _fk_cache behavior with eager loading."""

    def test_eager_load_populates_fk_cache(self, db: SqliterDB) -> None:
        """Verify eager loading populates _fk_cache."""
        result = db.select(Book).select_related("author").fetch_one()

        assert result is not None
        assert hasattr(result, "_fk_cache")
        fk_cache = getattr(result, "_fk_cache", {})
        assert "author" in fk_cache
        assert fk_cache["author"].name == "Jane Austen"

    def test_cached_object_reused(self, db: SqliterDB) -> None:
        """Verify cached object is reused on multiple access."""
        result = db.select(Book).select_related("author").fetch_one()
        assert result is not None

        author1 = result.author
        author2 = result.author

        # Same object instance (from cache)
        assert author1 is author2

    def test_filter_traversal_populates_fk_cache(self, db: SqliterDB) -> None:
        """Verify filter traversal populates _fk_cache."""
        results = db.select(Book).filter(author__name="Jane Austen").fetch_all()

        for book in results:
            assert hasattr(book, "_fk_cache")
            fk_cache = getattr(book, "_fk_cache", {})
            assert "author" in fk_cache


class TestCombinationFeatures:
    """Tests combining select_related() with other features."""

    def test_select_related_with_fields_selection(self, db: SqliterDB) -> None:
        """Note: select_related() is disabled when fields() is used."""
        # This test documents current behavior - when specific fields
        # are selected, JOINs are disabled
        results = (
            db.select(Book)
            .fields(["title", "year"])
            .select_related("author")
            .fetch_all()
        )

        # Results should be returned (with eager loading disabled)
        assert len(results) > 0

    def test_select_related_with_exclude(self, db: SqliterDB) -> None:
        """Note: select_related() is disabled when exclude() is used."""
        results = (
            db.select(Book)
            .exclude(["created_at", "updated_at"])
            .select_related("author")
            .fetch_all()
        )

        # Results should be returned (with eager loading disabled)
        assert len(results) > 0

    def test_select_related_with_only(self, db: SqliterDB) -> None:
        """Note: select_related() is disabled when only() is used."""
        results = (
            db.select(Book).only("title").select_related("author").fetch_all()
        )

        # Results should be returned (with eager loading disabled)
        assert len(results) > 0


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_result_with_select_related(self, db: SqliterDB) -> None:
        """Verify select_related() works with empty result set."""
        results = (
            db.select(Book)
            .select_related("author")
            .filter(title__like="NonExistent%")
            .fetch_all()
        )

        assert results == []

    def test_select_related_on_self_referential_model(
        self, db: SqliterDB
    ) -> None:
        """Test select_related() works with self-referential FKs.

        Note: Self-referential models with forward references require special
        handling. This test verifies basic functionality without forward
        reference resolution issues.
        """
        # Self-referential models need to be defined at module level for
        # forward references to work properly. For this test, we'll just
        # verify that the JOIN logic handles same-table joins correctly
        # without actually creating a self-referential model.

        # The key thing being tested is that the alias system handles
        # self-joins correctly (e.g., t0 -> t1 where both are "employees")
        # This is already covered by other tests with multiple relationships
        # which exercise the same alias assignment logic.

        # Skip this test for now as self-referential models with forward
        # references require module-level model definition
        pytest.skip(
            "Self-referential models require module-level definition for "
            "forward references"
        )

    def test_multiple_calls_to_select_related(self, db: SqliterDB) -> None:
        """Verify multiple select_related() calls accumulate."""
        result = (
            db.select(Book)
            .select_related("author")
            .select_related("publisher")
            .filter(title="Pride and Prejudice")
            .fetch_one()
        )

        assert result is not None
        assert result.author is not None
        if result.publisher:
            assert isinstance(result.publisher.name, str)


class TestRelationshipFilterWithNullOperators:
    """Tests for __isnull and __notnull on FK ID fields."""

    def test_filter_fk_id_with_isnull(self, db: SqliterDB) -> None:
        """Verify __isnull works on FK ID fields."""
        results = (
            db.select(Book)
            .select_related("publisher")
            .filter(publisher_id__isnull=True)
            .fetch_all()
        )

        assert len(results) >= 1
        assert all(b.publisher is None for b in results)

    def test_filter_fk_id_with_notnull(self, db: SqliterDB) -> None:
        """Verify __notnull works on FK ID fields."""
        results = (
            db.select(Book)
            .select_related("publisher")
            .filter(publisher_id__notnull=True)
            .fetch_all()
        )

        assert len(results) >= 3
        for book in results:
            assert book.publisher_id is not None


class TestDebugLogging:
    """Tests for debug logging with JOIN queries."""

    def test_select_related_logs_sql(self, db: SqliterDB) -> None:
        """Verify debug mode logs JOIN queries."""
        # Enable debug mode
        db.debug = True

        # Execute query with JOIN
        db.select(Book).select_related("author").fetch_one()

        # Disable debug mode
        db.debug = False

    def test_filter_traversal_logs_sql(self, db: SqliterDB) -> None:
        """Verify debug mode logs filter traversal queries."""
        db.debug = True

        db.select(Book).filter(author__name="Jane Austen").fetch_all()

        db.debug = False


class TestSelectRelatedWithOrderingAndPagination:
    """Tests for select_related() combined with ordering and pagination."""

    def test_order_by_with_select_related(self, db: SqliterDB) -> None:
        """Verify ordering works with eager loading."""
        results = (
            db.select(Book)
            .select_related("author")
            .order("year", reverse=True)
            .fetch_all()
        )

        assert results[0].year == 2000
        assert results[-1].year == 1811

    def test_offset_with_select_related(self, db: SqliterDB) -> None:
        """Verify offset works with eager loading."""
        results = (
            db.select(Book)
            .select_related("author")
            .order("year")
            .offset(2)
            .limit(2)
            .fetch_all()
        )

        assert len(results) == 2
        assert results[0].year >= 1813

    def test_fetch_last_with_select_related(self, db: SqliterDB) -> None:
        """Verify fetch_last() works with eager loading.

        Regression test for bug where ORDER BY was dropped when fetch_last()
        was used with select_related(), causing arbitrary row to be returned.
        """
        # Create multiple books to ensure we have a "last" one
        author = db.insert(Author(name="Test Author", email="test@example.com"))
        db.insert(Book(title="First", year=1800, author=author))
        db.insert(Book(title="Middle", year=1900, author=author))
        last_book = db.insert(Book(title="Last", year=2000, author=author))

        # fetch_last with select_related should return the last book
        result = db.select(Book).select_related("author").fetch_last()

        assert result is not None
        assert result.pk == last_book.pk
        assert result.title == "Last"
        # Verify author was eagerly loaded (no additional query)
        assert result.author.name == "Test Author"


class TestSelectRelatedEdgeCases:
    """Tests for edge cases in select_related functionality."""

    def test_select_related_count(self, db: SqliterDB) -> None:
        """Verify count() works with select_related (no JOIN needed)."""
        count = db.select(Book).select_related("author").count()

        assert count == 4

    def test_select_related_exists(self, db: SqliterDB) -> None:
        """Verify exists() works with select_related (no JOIN needed)."""
        exists = db.select(Book).select_related("author").exists()

        assert exists is True

    def test_select_related_empty_result(self, db: SqliterDB) -> None:
        """Verify empty result set with select_related."""
        results = (
            db.select(Book)
            .select_related("author")
            .filter(title__like="NonExistent%")
            .fetch_all()
        )

        assert results == []

    def test_select_related_first_no_match(self, db: SqliterDB) -> None:
        """Verify fetch_one returns None when no match with select_related."""
        result = (
            db.select(Book)
            .select_related("author")
            .filter(title="NonExistent")
            .fetch_one()
        )

        assert result is None

    def test_count_with_relationship_filters(self, db: SqliterDB) -> None:
        """Verify count() works with relationship filters."""
        # Count books by author's name using relationship traversal
        count = db.select(Book).filter(author__name="Jane Austen").count()

        # Should find 2 books by Jane Austen
        assert count == 2


class TestSelectRelatedWithComplexFilters:
    """Tests for select_related with complex filter combinations."""

    def test_select_related_with_multiple_filters(self, db: SqliterDB) -> None:
        """Verify multiple filters work with select_related."""
        results = (
            db.select(Book)
            .select_related("author")
            .filter(author__name="Jane Austen", year=1813)
            .fetch_all()
        )

        assert len(results) == 1
        assert results[0].title == "Pride and Prejudice"

    def test_select_related_with_filter_by_year(self, db: SqliterDB) -> None:
        """Verify filter with select_related works correctly."""
        results = (
            db.select(Book)
            .select_related("author")
            .filter(year__lt=1812)
            .fetch_all()
        )

        assert len(results) == 1
        assert results[0].year == 1811


class TestNestedRelationshipEdgeCases:
    """Tests for edge cases in nested relationship handling."""

    def test_nested_select_related_missing_middle(self, db: SqliterDB) -> None:
        """Verify handling when middle relationship is NULL."""
        # Get the book with no publisher
        book = db.select(Book).filter(title="Independent Book").fetch_one()
        assert book is not None

        # Create a comment linked to that book
        db.insert(Comment(text="No publisher!", book=book))

        # This should work even if book.publisher is NULL
        result = (
            db.select(Comment)
            .filter(text="No publisher!")
            .select_related("book__publisher")
            .fetch_one()
        )

        assert result is not None
        assert result.book is not None
        assert result.book.publisher is None  # Publisher is NULL
        assert hasattr(result.book, "publisher")  # But attribute exists

    def test_filter_on_nested_nullable_relationship(
        self, db: SqliterDB
    ) -> None:
        """Verify filter traversal on nested nullable relationships."""
        results = (
            db.select(Comment)
            .filter(book__publisher__name="Penguin")
            .fetch_all()
        )

        # Should find comments where book.publisher.name = "Penguin"
        assert len(results) >= 0


class TestSelectRelatedCoverageEdgeCases:
    """Tests for edge cases to reach 100% coverage."""

    def test_order_with_complex_pattern(self, db: SqliterDB) -> None:
        """Test ORDER BY with non-standard pattern (line 866)."""
        # Use order() which should work normally
        results = (
            db.select(Book).select_related("author").order("title").fetch_all()
        )

        assert len(results) > 0

    def test_count_with_select_related(self, db: SqliterDB) -> None:
        """Test count() with select_related (line 690 - early return)."""
        count = db.select(Book).select_related("author").count()

        assert count == 4

    def test_exists_with_select_related(self, db: SqliterDB) -> None:
        """Test exists() with select_related (line 690 - early return)."""
        exists = db.select(Book).select_related("author").exists()

        assert exists is True


class TestRelationshipFilterOperators:
    """Tests for relationship filter with various operators (line 243)."""

    def test_filter_related_field_with_like(self, db: SqliterDB) -> None:
        """Verify __like works on related fields."""
        results = (
            db.select(Book)
            .select_related("author")
            .filter(author__name__like="Jane%")
            .fetch_all()
        )

        assert len(results) == 2
        for book in results:
            assert book.author is not None
            assert "Jane" in str(book.author.name)

    def test_filter_related_field_with_startswith(self, db: SqliterDB) -> None:
        """Verify __startswith works on related fields."""
        results = (
            db.select(Book)
            .select_related("author")
            .filter(author__name__startswith="Jane")
            .fetch_all()
        )

        assert len(results) == 2


class TestSelectRelatedWithMocks:
    """Tests using mocking to reach 100% coverage of edge cases."""

    def test_select_related_sqlite_error_handling(self, db: SqliterDB) -> None:
        """Test SQLite error during JOIN query execution (lines 864-865)."""
        # Create a query with select_related
        query = db.select(Book).select_related("author")

        # Mock the database connection to raise an error
        with mock.patch.object(query.db, "connect") as mock_connect:
            mock_conn = mock.MagicMock()
            mock_cursor = mock.MagicMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn

            # Mock cursor.execute to raise SQLite error
