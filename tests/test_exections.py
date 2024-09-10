"""Test cases for the custom exceptions in the sqliter module."""

import sqlite3

import pytest
from sqliter.exceptions import DatabaseConnectionError, SqliterError
from sqliter.sqliter import SqliterDB


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
