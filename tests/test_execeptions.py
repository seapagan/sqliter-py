"""Test cases for the custom exceptions in the sqliter module."""

import sqlite3

import pytest

from sqliter.exceptions import (
    DatabaseConnectionError,
    RecordInsertionError,
    SqliterError,
)
from sqliter.sqliter import SqliterDB
from tests.conftest import ExampleModel


def test_sqliter_error_with_template() -> None:
    """Test that SqliterError formats the message correctly with a template."""

    class CustomError(SqliterError):
        message_template = "Custom error occurred with variable: '{}'"

    exc = CustomError("test_variable")

    assert str(exc) == "Custom error occurred with variable: 'test_variable'"


def test_sqliter_error_without_template() -> None:
    """Test that SqliterError uses the default message if no template."""
    exc = SqliterError()

    assert str(exc) == "An error occurred in the SQLiter package."


def test_database_connection_error(mocker) -> None:
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


def test_insert_duplicate_primary_key(db_mock) -> None:
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
