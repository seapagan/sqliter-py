"""Test cases for the custom exceptions in the sqliter module."""

import sqlite3

import pytest

from sqliter.exceptions import (
    DatabaseConnectionError,
    RecordDeletionError,
    RecordInsertionError,
    RecordNotFoundError,
    RecordUpdateError,
    SqliterError,
    TableCreationError,
)
from sqliter.sqliter import SqliterDB
from tests.conftest import ExampleModel


class TestExceptions:
    """Test class for the custom exceptions in the sqliter module."""

    def test_sqliter_error_with_template(self) -> None:
        """Test SqliterError formats the message correctly with a template."""

        class CustomError(SqliterError):
            message_template = "Custom error occurred with variable: '{}'"

        exc = CustomError("test_variable")

        assert (
            str(exc) == "Custom error occurred with variable: 'test_variable'"
        )

    def test_sqliter_error_without_template(self) -> None:
        """Test that SqliterError uses the default message if no template."""
        exc = SqliterError()

        assert str(exc) == "An error occurred in the SQLiter package."

    def test_database_connection_error(self, mocker) -> None:
        """Test that DatabaseConnectionError is raised when connection fails."""
        # Mock sqlite3.connect to raise an error
        mocker.patch("sqlite3.connect", side_effect=sqlite3.Error)

        # Create a SqliterDB instance
        db = SqliterDB("fake_db.db")

        # Assert that DatabaseConnectionError is raised when connecting
        with pytest.raises(DatabaseConnectionError) as exc_info:
            db.connect()

        # Verify the exception message contains the database file name
        assert "Failed to connect to the database: 'fake_db.db'" in str(
            exc_info.value
        )

    @pytest.mark.skip(reason="This is no longer a valid test case.")
    def test_insert_duplicate_primary_key(self, db_mock) -> None:
        """Test that exception raised when inserting duplicate primary key."""
        # Create a model instance with a unique primary key
        example_model = ExampleModel(
            slug="test", name="Test License", content="Test Content"
        )

        # Insert the record for the first time, should succeed
        db_mock.insert(example_model)

        # Try inserting the same record again, which should raise our exception
        with pytest.raises(RecordInsertionError) as exc_info:
            db_mock.insert(example_model)

        # Verify that the exception message contains the table name
        assert "Failed to insert record into table: 'test_table'" in str(
            exc_info.value
        )

    def test_create_table_error(self, db_mock, mocker) -> None:
        """Test exception is raised when creating table with invalid model."""
        # Mock sqlite3.connect to raise an error
        mocker.patch("sqliter.SqliterDB.connect", side_effect=sqlite3.Error)

        # Try creating the table, which should raise an exception
        with pytest.raises(TableCreationError) as exc_info:
            db_mock.create_table(ExampleModel)

        # Verify that the exception message contains the table name
        assert "Failed to create the table: 'test_table'" in str(exc_info.value)

    def test_update_not_found_error(self, db_mock) -> None:
        """Test exception raised when updating a record that does not exist."""
        # Create a model instance with a unique primary key
        example_model = ExampleModel(
            slug="test", name="Test License", content="Test Content"
        )

        # Try updating the record, which should raise an exception
        with pytest.raises(RecordNotFoundError) as exc_info:
            db_mock.update(example_model)

        # Verify that the exception message contains the table name
        assert "Failed to find that record in the table (key '0')" in str(
            exc_info.value
        )

    def test_update_exception_error(self, db_mock, mocker) -> None:
        """Test an exception is raised when updating a record with an error."""
        # Create a model instance with a unique primary key
        example_model = ExampleModel(
            slug="test", name="Test License", content="Test Content"
        )

        # Insert the record for the first time, should succeed
        db_mock.insert(example_model)

        # Mock sqlite3.connect to raise an error
        mocker.patch("sqliter.SqliterDB.connect", side_effect=sqlite3.Error)

        # Try updating the record, which should raise an exception
        with pytest.raises(RecordUpdateError) as exc_info:
            db_mock.update(example_model)

        # Verify that the exception message contains the table name
        assert "Failed to update record in table: 'test_table'" in str(
            exc_info.value
        )

    def test_delete_exception_error(self, db_mock, mocker) -> None:
        """Test that exception raised when deleting a record with an error."""
        # Create a model instance with a unique primary key
        example_model = ExampleModel(
            slug="test", name="Test License", content="Test Content"
        )

        # Insert the record for the first time, should succeed
        db_mock.insert(example_model)

        # Mock sqlite3.connect to raise an error
        mocker.patch("sqliter.SqliterDB.connect", side_effect=sqlite3.Error)

        # Try deleting the record, which should raise an exception
        with pytest.raises(RecordDeletionError) as exc_info:
            db_mock.delete(ExampleModel, "test")

        # Verify that the exception message contains the table name
        assert "Failed to delete record from table: 'test_table'" in str(
            exc_info.value
        )

    def test_root_exception_with_no_traceback(self) -> None:
        """Test the root exception message."""
        with pytest.raises(SqliterError) as exc:
            raise SqliterError

        assert str(exc.value) == "An error occurred in the SQLiter package."

    def test_exception_with_no_traceback(self) -> None:
        """Test custom exception with an original exception but no traceback."""

        def raise_original_exception() -> None:
            """Helper function to raise an original exception."""
            err = "Original error"
            raise ValueError(err)

        def trigger_sqliter_error_with_no_traceback() -> None:
            """Helper function to trigger SqliterError with no traceback."""
            try:
                # Simulate an original exception
                raise_original_exception()
            except ValueError as original_exc:
                # Manually clear the traceback from the exception
                original_exc.__traceback__ = None  # Remove the traceback

                # Raise the custom exception and chain it
                raise SqliterError from original_exc

        # Simulate the exception chain with no traceback using pytest.raises
        with pytest.raises(SqliterError) as exc_info:
            trigger_sqliter_error_with_no_traceback()

        # Access the raised exception instance
        exc = exc_info.value

        # Verify that the exception message contains "unknown location"
        assert "unknown location" in str(exc)
