"""Test suite for foreign key support."""

import sqlite3
from typing import Optional

import pytest

from sqliter import SqliterDB
from sqliter.exceptions import (
    ForeignKeyConstraintError,
    ForeignKeyError,
    InvalidForeignKeyError,
    RecordDeletionError,
    RecordInsertionError,
)
from sqliter.model import BaseDBModel, ForeignKey, get_foreign_key_info


class Author(BaseDBModel):
    """Test model for an author."""

    name: str
    email: str


class Book(BaseDBModel):
    """Test model for a book with FK to author."""

    title: str
    author_id: int = ForeignKey(Author, on_delete="CASCADE")


class TestForeignKeyInfo:
    """Test suite for ForeignKey metadata and configuration."""

    def test_foreign_key_creates_field_info(self) -> None:
        """Test that ForeignKey creates proper field metadata."""

        class TestBook(BaseDBModel):
            title: str
            author_id: int = ForeignKey(Author, on_delete="CASCADE")

        field_info = TestBook.model_fields["author_id"]
        fk_info = get_foreign_key_info(field_info)

        assert fk_info is not None
        assert fk_info.to_model is Author
        assert fk_info.on_delete == "CASCADE"
        assert fk_info.on_update == "CASCADE"
        assert fk_info.null is False
        assert fk_info.unique is False

    def test_foreign_key_custom_on_delete(self) -> None:
        """Test ForeignKey with custom on_delete action."""

        class TestBook(BaseDBModel):
            title: str
            author_id: Optional[int] = ForeignKey(
                Author, on_delete="SET NULL", null=True
            )

        field_info = TestBook.model_fields["author_id"]
        fk_info = get_foreign_key_info(field_info)

        assert fk_info is not None
        assert fk_info.on_delete == "SET NULL"
        assert fk_info.null is True

    def test_foreign_key_custom_on_update(self) -> None:
        """Test ForeignKey with custom on_update action."""

        class TestBook(BaseDBModel):
            title: str
            author_id: int = ForeignKey(
                Author, on_delete="CASCADE", on_update="RESTRICT"
            )

        field_info = TestBook.model_fields["author_id"]
        fk_info = get_foreign_key_info(field_info)

        assert fk_info is not None
        assert fk_info.on_update == "RESTRICT"

    def test_foreign_key_unique_for_one_to_one(self) -> None:
        """Test ForeignKey with unique=True for one-to-one relationship."""

        class Profile(BaseDBModel):
            bio: str
            author_id: int = ForeignKey(
                Author, on_delete="CASCADE", unique=True
            )

        field_info = Profile.model_fields["author_id"]
        fk_info = get_foreign_key_info(field_info)

        assert fk_info is not None
        assert fk_info.unique is True

    def test_set_null_requires_null_true(self) -> None:
        """Test that SET NULL on_delete requires null=True."""
        with pytest.raises(
            ValueError, match="on_delete='SET NULL' requires null=True"
        ):

            class TestBook(BaseDBModel):
                title: str
                author_id: int = ForeignKey(
                    Author, on_delete="SET NULL", null=False
                )

    def test_set_null_on_update_requires_null_true(self) -> None:
        """Test that SET NULL on_update requires null=True."""
        with pytest.raises(
            ValueError, match="on_update='SET NULL' requires null=True"
        ):

            class TestBook(BaseDBModel):
                title: str
                author_id: int = ForeignKey(
                    Author, on_update="SET NULL", null=False
                )

    def test_get_foreign_key_info_returns_none_for_regular_field(self) -> None:
        """Test that get_foreign_key_info returns None for regular fields."""

        class TestBook(BaseDBModel):
            title: str

        field_info = TestBook.model_fields["title"]
        fk_info = get_foreign_key_info(field_info)

        assert fk_info is None

    def test_foreign_key_with_db_column(self) -> None:
        """Test ForeignKey with custom db_column name."""

        class TestBook(BaseDBModel):
            title: str
            writer_id: int = ForeignKey(
                Author, on_delete="CASCADE", db_column="auth_id"
            )

        field_info = TestBook.model_fields["writer_id"]
        fk_info = get_foreign_key_info(field_info)

        assert fk_info is not None
        assert fk_info.db_column == "auth_id"

    def test_foreign_key_with_related_name(self) -> None:
        """Test ForeignKey with related_name (reserved for Phase 2)."""

        class TestBook(BaseDBModel):
            title: str
            author_id: int = ForeignKey(
                Author, on_delete="CASCADE", related_name="books"
            )

        field_info = TestBook.model_fields["author_id"]
        fk_info = get_foreign_key_info(field_info)

        assert fk_info is not None
        assert fk_info.related_name == "books"


class TestForeignKeyTableCreation:
    """Test suite for FK table creation."""

    def test_create_table_with_fk(self) -> None:
        """Test that tables with FK constraints are created correctly."""
        db = SqliterDB(":memory:")
        db.create_table(Author)
        db.create_table(Book)

        # Verify tables exist
        assert "authors" in db.table_names
        assert "books" in db.table_names

    def test_fk_constraint_sql_generation(self, mocker) -> None:
        """Test that FK constraint SQL is generated correctly."""
        mock_cursor = mocker.MagicMock()
        mocker.patch.object(
            SqliterDB, "connect"
        ).return_value.__enter__.return_value.cursor.return_value = mock_cursor

        db = SqliterDB(":memory:")
        db.create_table(Book)

        # Get all execute calls and find the CREATE TABLE statement
        all_calls = mock_cursor.execute.call_args_list
        create_table_sql = None
        for call in all_calls:
            sql = call[0][0]
            if "CREATE TABLE" in sql:
                create_table_sql = sql
                break

        assert create_table_sql is not None, "CREATE TABLE statement not found"

        # Check for FK constraint syntax
        assert "FOREIGN KEY" in create_table_sql
        assert 'REFERENCES "authors"("pk")' in create_table_sql
        assert "ON DELETE CASCADE" in create_table_sql
        assert "ON UPDATE CASCADE" in create_table_sql

    def test_fk_creates_index(self) -> None:
        """Test that FK columns get indexed automatically."""
        db = SqliterDB(":memory:")
        db.create_table(Author)
        db.create_table(Book)

        # Check that the index was created
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index' "
                "AND name LIKE 'idx_books_author_id%'"
            )
            indexes = cursor.fetchall()

        assert len(indexes) >= 1

    def test_pragma_foreign_keys_enabled(self) -> None:
        """Test that PRAGMA foreign_keys is enabled."""
        db = SqliterDB(":memory:")
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys")
            result = cursor.fetchone()

        assert result[0] == 1  # 1 = enabled


class TestForeignKeyConstraintEnforcement:
    """Test suite for FK constraint enforcement."""

    def test_insert_with_valid_fk(self) -> None:
        """Test that inserting with valid FK succeeds."""
        db = SqliterDB(":memory:")
        db.create_table(Author)
        db.create_table(Book)

        author = db.insert(Author(name="John Doe", email="john@example.com"))
        book = db.insert(Book(title="My Book", author_id=author.pk))

        assert book.pk is not None
        assert book.author_id == author.pk

    def test_insert_with_invalid_fk_fails(self) -> None:
        """Test that inserting with invalid FK value fails."""
        db = SqliterDB(":memory:")
        db.create_table(Author)
        db.create_table(Book)

        # Try to insert book with non-existent author
        with pytest.raises(ForeignKeyConstraintError) as excinfo:
            db.insert(Book(title="Orphan Book", author_id=999))

        assert "does not exist" in str(excinfo.value)

    def test_on_delete_cascade(self) -> None:
        """Test that ON DELETE CASCADE deletes referencing records."""
        db = SqliterDB(":memory:")
        db.create_table(Author)
        db.create_table(Book)

        author = db.insert(Author(name="John Doe", email="john@example.com"))
        db.insert(Book(title="Book 1", author_id=author.pk))
        db.insert(Book(title="Book 2", author_id=author.pk))

        # Verify books exist
        books = db.select(Book).fetch_all()
        assert len(books) == 2

        # Delete author - should cascade to books
        db.delete(Author, str(author.pk))

        # Verify books are also deleted
        books = db.select(Book).fetch_all()
        assert len(books) == 0

    def test_on_delete_set_null(self) -> None:
        """Test that ON DELETE SET NULL sets FK to NULL."""

        class BookWithNullableAuthor(BaseDBModel):
            title: str
            author_id: Optional[int] = ForeignKey(
                Author, on_delete="SET NULL", null=True
            )

        db = SqliterDB(":memory:")
        db.create_table(Author)
        db.create_table(BookWithNullableAuthor)

        author = db.insert(Author(name="John Doe", email="john@example.com"))
        book = db.insert(
            BookWithNullableAuthor(title="My Book", author_id=author.pk)
        )

        # Delete author
        db.delete(Author, str(author.pk))

        # Verify book still exists but author_id is NULL
        updated_book = db.get(BookWithNullableAuthor, book.pk)
        assert updated_book is not None
        assert updated_book.author_id is None

    def test_on_delete_restrict(self) -> None:
        """Test that ON DELETE RESTRICT prevents deletion."""

        class BookWithRestrict(BaseDBModel):
            title: str
            author_id: int = ForeignKey(Author, on_delete="RESTRICT")

        db = SqliterDB(":memory:")
        db.create_table(Author)
        db.create_table(BookWithRestrict)

        author = db.insert(Author(name="John Doe", email="john@example.com"))
        db.insert(BookWithRestrict(title="My Book", author_id=author.pk))

        # Attempt to delete author should fail
        with pytest.raises(ForeignKeyConstraintError) as excinfo:
            db.delete(Author, str(author.pk))

        assert "still referenced" in str(excinfo.value)

    def test_nullable_fk_allows_null(self) -> None:
        """Test that nullable FK fields accept NULL values."""

        class BookWithNullableAuthor(BaseDBModel):
            title: str
            author_id: Optional[int] = ForeignKey(
                Author, on_delete="SET NULL", null=True
            )

        db = SqliterDB(":memory:")
        db.create_table(Author)
        db.create_table(BookWithNullableAuthor)

        # Insert book without author (NULL FK)
        book = db.insert(
            BookWithNullableAuthor(title="Anonymous Book", author_id=None)
        )

        assert book.pk is not None
        assert book.author_id is None


class TestForeignKeyFiltering:
    """Test suite for filtering by FK fields."""

    def test_filter_by_fk_field(self) -> None:
        """Test filtering by FK field value."""
        db = SqliterDB(":memory:")
        db.create_table(Author)
        db.create_table(Book)

        author1 = db.insert(Author(name="Author 1", email="a1@example.com"))
        author2 = db.insert(Author(name="Author 2", email="a2@example.com"))

        db.insert(Book(title="Book A", author_id=author1.pk))
        db.insert(Book(title="Book B", author_id=author1.pk))
        db.insert(Book(title="Book C", author_id=author2.pk))

        # Filter books by author1
        books = db.select(Book).filter(author_id=author1.pk).fetch_all()
        assert len(books) == 2
        assert all(b.author_id == author1.pk for b in books)

    def test_filter_by_fk_with_comparison_operators(self) -> None:
        """Test filtering by FK field with comparison operators."""
        db = SqliterDB(":memory:")
        db.create_table(Author)
        db.create_table(Book)

        author1 = db.insert(Author(name="Author 1", email="a1@example.com"))
        author2 = db.insert(Author(name="Author 2", email="a2@example.com"))
        author3 = db.insert(Author(name="Author 3", email="a3@example.com"))

        db.insert(Book(title="Book A", author_id=author1.pk))
        db.insert(Book(title="Book B", author_id=author2.pk))
        db.insert(Book(title="Book C", author_id=author3.pk))

        # Filter books where author_id > author1.pk
        books = db.select(Book).filter(author_id__gt=author1.pk).fetch_all()
        assert len(books) == 2

    def test_filter_by_fk_with_in_operator(self) -> None:
        """Test filtering by FK field with __in operator."""
        db = SqliterDB(":memory:")
        db.create_table(Author)
        db.create_table(Book)

        author1 = db.insert(Author(name="Author 1", email="a1@example.com"))
        author2 = db.insert(Author(name="Author 2", email="a2@example.com"))
        author3 = db.insert(Author(name="Author 3", email="a3@example.com"))

        db.insert(Book(title="Book A", author_id=author1.pk))
        db.insert(Book(title="Book B", author_id=author2.pk))
        db.insert(Book(title="Book C", author_id=author3.pk))

        # Filter books where author_id in [author1.pk, author3.pk]
        books = (
            db.select(Book)
            .filter(author_id__in=[author1.pk, author3.pk])  # type: ignore[arg-type]
            .fetch_all()
        )
        assert len(books) == 2
        assert {b.title for b in books} == {"Book A", "Book C"}


class TestForeignKeyUniqueConstraint:
    """Test suite for unique FK (one-to-one relationships)."""

    def test_unique_fk_enforced(self) -> None:
        """Test that unique FK constraint is enforced."""

        class Profile(BaseDBModel):
            bio: str
            author_id: int = ForeignKey(
                Author, on_delete="CASCADE", unique=True
            )

        db = SqliterDB(":memory:")
        db.create_table(Author)
        db.create_table(Profile)

        author = db.insert(Author(name="John", email="john@example.com"))

        # First profile should succeed
        db.insert(Profile(bio="Bio 1", author_id=author.pk))

        # Second profile with same author should fail
        with pytest.raises(RecordInsertionError) as excinfo:
            db.insert(Profile(bio="Bio 2", author_id=author.pk))

        assert "UNIQUE constraint failed" in str(excinfo.value)


class TestForeignKeyExceptions:
    """Test suite for FK exception classes."""

    def test_foreign_key_error_base(self) -> None:
        """Test ForeignKeyError base exception."""
        error = ForeignKeyError("test error")
        assert "Foreign key error" in str(error)

    def test_foreign_key_constraint_error(self) -> None:
        """Test ForeignKeyConstraintError exception."""
        error = ForeignKeyConstraintError("insert", "does not exist")
        assert "Foreign key constraint violation" in str(error)
        assert "insert" in str(error)

    def test_invalid_foreign_key_error(self) -> None:
        """Test InvalidForeignKeyError exception."""
        error = InvalidForeignKeyError("bad config")
        assert "Invalid foreign key configuration" in str(error)


class TestForeignKeyNoAction:
    """Test ON DELETE/UPDATE NO ACTION behavior."""

    def test_on_delete_no_action(self) -> None:
        """Test that ON DELETE NO ACTION prevents deletion (like RESTRICT)."""

        class BookWithNoAction(BaseDBModel):
            title: str
            author_id: int = ForeignKey(Author, on_delete="NO ACTION")

        db = SqliterDB(":memory:")
        db.create_table(Author)
        db.create_table(BookWithNoAction)

        author = db.insert(Author(name="John Doe", email="john@example.com"))
        db.insert(BookWithNoAction(title="My Book", author_id=author.pk))

        # Attempt to delete author should fail
        with pytest.raises(ForeignKeyConstraintError):
            db.delete(Author, str(author.pk))


class TestForeignKeyWithNonDictJsonSchemaExtra:
    """Test ForeignKey handles non-dict json_schema_extra correctly."""

    def test_non_dict_json_schema_extra_converted(self) -> None:
        """Test that non-dict json_schema_extra is handled properly."""

        class TestBook(BaseDBModel):
            title: str
            author_id: int = ForeignKey(
                Author,
                on_delete="CASCADE",
                json_schema_extra=["not", "a", "dict"],
            )

        field_info = TestBook.model_fields["author_id"]
        fk_info = get_foreign_key_info(field_info)

        # The ForeignKey should still be extractable
        assert fk_info is not None
        assert fk_info.to_model is Author


class TestGetForeignKeyInfoEdgeCases:
    """Test edge cases for get_foreign_key_info function."""

    def test_field_without_json_schema_extra_attribute(self, mocker) -> None:
        """Test get_foreign_key_info with field lacking json_schema_extra."""
        # Create a mock FieldInfo without json_schema_extra attribute
        mock_field_info = mocker.MagicMock(
            spec=[]
        )  # Empty spec = no attributes

        fk_info = get_foreign_key_info(mock_field_info)

        assert fk_info is None


class TestForeignKeyDatabaseErrors:
    """Test database error handling for FK operations."""

    def test_insert_general_database_error(self, mocker) -> None:
        """Test that general sqlite3.Error during insert raises properly."""
        db = SqliterDB(":memory:")
        db.create_table(Author)

        # Mock cursor.execute to raise a general sqlite3.Error
        mock_cursor = mocker.MagicMock()
        mock_cursor.execute.side_effect = sqlite3.Error(
            "General database error"
        )

        mock_conn = mocker.MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = mocker.MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = mocker.MagicMock(return_value=False)

        mocker.patch.object(db, "connect", return_value=mock_conn)

        with pytest.raises(RecordInsertionError):
            db.insert(Author(name="Test", email="test@example.com"))

    def test_delete_non_fk_integrity_error(self, mocker) -> None:
        """Test delete with IntegrityError that is not FK-related."""
        db = SqliterDB(":memory:")
        db.create_table(Author)

        # Insert an author first
        author = db.insert(Author(name="Test", email="test@example.com"))

        # Mock to raise IntegrityError with non-FK message
        mock_cursor = mocker.MagicMock()
        mock_cursor.execute.side_effect = sqlite3.IntegrityError(
            "UNIQUE constraint failed"
        )

        mock_conn = mocker.MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = mocker.MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = mocker.MagicMock(return_value=False)

        mocker.patch.object(db, "connect", return_value=mock_conn)

        with pytest.raises(RecordDeletionError):
            db.delete(Author, str(author.pk))
