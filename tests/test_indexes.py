"""Test suite for index creation in the database."""

from typing import ClassVar

import pytest
from pytest_mock import MockerFixture

from sqliter.exceptions import InvalidIndexError
from sqliter.model import BaseDBModel
from sqliter.sqliter import SqliterDB


def get_index_names(db: SqliterDB) -> list[str]:
    """Helper function to fetch index names from sqlite_master."""
    conn = db.conn
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        return [row[0] for row in cursor.fetchall()]
    return []


class TestIndexes:
    """Test cases for index creation in the database."""

    def test_regular_index_creation(self, mocker: MockerFixture) -> None:
        """Test that regular indexes are created for valid fields."""
        mock_execute = mocker.patch.object(SqliterDB, "_execute_sql")

        db = SqliterDB(":memory:")

        # Define a test model with a regular index on 'email'
        class UserModel(BaseDBModel):
            slug: str
            email: str

            class Meta:
                table_name = "users"
                indexes: ClassVar[list[str]] = ["email"]  # Regular index

        # Create the table
        db.create_table(UserModel)

        # Assert the correct SQL for the index was executed
        expected_sql = (
            'CREATE INDEX IF NOT EXISTS idx_users_email ON "users" ("email")'
        )
        mock_execute.assert_any_call(expected_sql)

    def test_unique_index_creation(self, mocker: MockerFixture) -> None:
        """Test that unique indexes are created for valid fields."""
        mock_execute = mocker.patch.object(SqliterDB, "_execute_sql")

        db = SqliterDB(":memory:")

        # Define a test model with a unique index on 'email'
        class UserModel(BaseDBModel):
            slug: str
            email: str

            class Meta:
                table_name = "users"
                unique_indexes: ClassVar[list[str]] = ["email"]  # Unique index

        # Create the table
        db.create_table(UserModel)

        # Assert the correct SQL for the unique index was executed
        expected_sql = (
            "CREATE UNIQUE INDEX IF NOT EXISTS "
            'idx_users_email_unique ON "users" ("email")'
        )
        mock_execute.assert_any_call(expected_sql)

    def test_composite_index_creation(self, mocker: MockerFixture) -> None:
        """Test composite index creation for valid fields."""
        mock_execute = mocker.patch.object(SqliterDB, "_execute_sql")

        db = SqliterDB(":memory:")

        # Define a test model with a composite index on 'customer_id' and
        # 'order_id'
        class OrderModel(BaseDBModel):
            order_id: str
            customer_id: str

            class Meta:
                table_name = "orders"
                indexes: ClassVar[list[tuple[str, str]]] = [
                    ("customer_id", "order_id")
                ]  # Composite index

        # Create the table
        db.create_table(OrderModel)

        # Assert the correct SQL for the composite index was executed
        expected_sql = (
            "CREATE INDEX IF NOT EXISTS idx_orders_customer_id_order_id "
            'ON "orders" ("customer_id", "order_id")'
        )
        mock_execute.assert_any_call(expected_sql)

    def test_invalid_index_raises_error(self) -> None:
        """Test that an invalid index raises an InvalidIndexError."""
        db = SqliterDB(":memory:")

        # Define a test model with an invalid index field
        class UserModel(BaseDBModel):
            slug: str
            email: str

            class Meta:
                table_name = "users"
                indexes: ClassVar[list[str]] = [
                    "non_existent_field"
                ]  # Invalid field

        # Assert an InvalidIndexError is raised
        with pytest.raises(InvalidIndexError) as exc_info:
            db.create_table(UserModel)

        # Ensure the error message contains the invalid field and model class
        assert "Invalid fields for indexing in model 'UserModel'" in str(
            exc_info.value
        )

    def test_actual_regular_index_creation(self) -> None:
        """Test that the regular index is actually created in the database."""
        db = SqliterDB(":memory:")

        class UserModel(BaseDBModel):
            slug: str
            email: str

            class Meta:
                table_name = "users"
                indexes: ClassVar[list[str]] = ["email"]  # Regular index

        # Create the table and index
        db.create_table(UserModel)

        # Use helper to fetch index names
        index_names: list[str] = get_index_names(db)

        assert "idx_users_email" in index_names

    def test_actual_unique_index_creation(self) -> None:
        """Test that the unique index is actually created in the database."""
        db = SqliterDB(":memory:")

        class UserModel(BaseDBModel):
            slug: str
            email: str

            class Meta:
                table_name = "users"
                unique_indexes: ClassVar[list[str]] = ["email"]  # Unique index

        # Create the table and unique index
        db.create_table(UserModel)

        # Use helper to fetch index names
        index_names: list[str] = get_index_names(db)

        assert "idx_users_email_unique" in index_names

    def test_no_index_creation_with_empty_indexes(self) -> None:
        """Test no index created when indexes and unique_indexes are empty."""
        db = SqliterDB(":memory:")

        class UserModel(BaseDBModel):
            slug: str
            email: str

            class Meta:
                table_name = "users"
                indexes: ClassVar[list[str]] = []
                unique_indexes: ClassVar[list[str]] = []

        # Create the table with no indexes
        db.create_table(UserModel)

        # Use helper to fetch index names
        index_names: list[str] = get_index_names(db)

        assert len(index_names) == 0

    def test_invalid_index_with_bad_tuple(self) -> None:
        """Test InvalidIndexError is raised when tuple has invalid fields."""
        db = SqliterDB(":memory:")

        class UserModel(BaseDBModel):
            slug: str
            email: str
            name: str

            class Meta:
                table_name = "users"
                indexes: ClassVar[list[tuple[str, str]]] = [
                    ("email", "non_existent_field")
                ]  # Invalid tuple

        # Assert that InvalidIndexError is raised for the bad tuple
        with pytest.raises(InvalidIndexError) as exc_info:
            db.create_table(UserModel)

        error_message: str = str(exc_info.value)
        assert "non_existent_field" in error_message

    def test_good_index_followed_by_bad_index(self) -> None:
        """Test a good index followed by bad index raises InvalidIndexError."""
        db = SqliterDB(":memory:")

        class UserModel(BaseDBModel):
            slug: str
            email: str
            name: str

            class Meta:
                table_name = "users"
                indexes: ClassVar[list[str]] = [
                    "email",  # Good index
                    "non_existent_field",  # Bad index
                ]

        # Assert that InvalidIndexError is raised for the bad index
        with pytest.raises(InvalidIndexError) as exc_info:
            db.create_table(UserModel)

        error_message: str = str(exc_info.value)
        assert "non_existent_field" in error_message

    def test_multiple_valid_composite_indexes(self) -> None:
        """Test that multiple valid composite indexes are created."""
        db = SqliterDB(":memory:")

        class UserModel(BaseDBModel):
            slug: str
            email: str
            name: str

            class Meta:
                table_name = "users"
                indexes: ClassVar[list[tuple[str, str]]] = [
                    ("email", "name"),  # Valid composite index
                    ("slug", "email"),  # Another valid composite index
                ]

        db.create_table(UserModel)

        index_names: list[str] = get_index_names(db)
        assert "idx_users_email_name" in index_names
        assert "idx_users_slug_email" in index_names

    def test_index_with_empty_field_in_tuple(self) -> None:
        """Test that an index with an empty field in a tuple raises an error."""
        db = SqliterDB(":memory:")

        class UserModel(BaseDBModel):
            slug: str
            email: str

            class Meta:
                table_name = "users"
                indexes: ClassVar[list[tuple[str, str]]] = [
                    ("email", ""),  # Invalid composite index
                ]

        with pytest.raises(InvalidIndexError) as exc_info:
            db.create_table(UserModel)

        error_message: str = str(exc_info.value)
        assert "Invalid fields" in error_message

    def test_duplicate_index_fields(self) -> None:
        """Test that duplicate index fields are handled properly."""
        db = SqliterDB(":memory:")

        class UserModel(BaseDBModel):
            slug: str
            email: str

            class Meta:
                table_name = "users"
                indexes: ClassVar[list[str]] = [
                    "email",  # First occurrence
                    "email",  # Duplicate
                ]

        db.create_table(UserModel)

        # Check that only one index was created
        index_names: list[str] = get_index_names(db)
        assert index_names.count("idx_users_email") == 1

    def test_index_with_reserved_keyword_as_field_name(self) -> None:
        """Test that fields using reserved SQL keywords work when quoted."""
        db = SqliterDB(":memory:")

        class UserModel(BaseDBModel):
            select: str  # 'select' is a reserved SQL keyword
            email: str

            class Meta:
                table_name = "users"
                indexes: ClassVar[list[str]] = [
                    "select"
                ]  # Now valid due to quoting

        # Should succeed because field names are quoted
        db.create_table(UserModel)

        # Verify the index was created successfully
        assert "users" in db.table_names

    def test_mixed_valid_and_invalid_fields_in_composite_index(self) -> None:
        """Test an index with both valid and invalid fields raises an error."""
        db = SqliterDB(":memory:")

        class UserModel(BaseDBModel):
            slug: str
            email: str

            class Meta:
                table_name = "users"
                indexes: ClassVar[list[tuple[str, str]]] = [
                    ("email", "invalid_field")  # Mixed valid and invalid
                ]

        with pytest.raises(InvalidIndexError) as exc_info:
            db.create_table(UserModel)

        error_message: str = str(exc_info.value)
        assert "invalid_field" in error_message
