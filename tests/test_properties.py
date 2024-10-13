"""Test the read-only properties in the SqliterDB class."""

import tempfile

import pytest

from sqliter.exceptions import DatabaseConnectionError
from sqliter.model.model import BaseDBModel
from sqliter.sqliter import SqliterDB


class TestSqliterDBProperties:
    """Test suite for the read-only properties in the SqliterDB class."""

    def test_filename_property_memory_db(self) -> None:
        """Test the 'filename' property for an in-memory database."""
        db = SqliterDB(memory=True)
        assert db.filename is None, "Expected None for in-memory database"

    def test_filename_property_file_db(self) -> None:
        """Test the 'filename' property for a file-based database."""
        db = SqliterDB(db_filename="test.db")
        assert db.filename == "test.db", "Expected 'test.db' as filename"

    def test_is_memory_property_true(self) -> None:
        """Test the 'is_memory' property returns True for in-memory database."""
        db = SqliterDB(memory=True)
        assert db.is_memory is True, "Expected True for in-memory database"

    def test_is_memory_property_false(self) -> None:
        """Test 'is_memory' property returns False for file-based database."""
        db = SqliterDB(db_filename="test.db")
        assert db.is_memory is False, "Expected False for file-based database"

    def test_is_autocommit_property_true(self) -> None:
        """Test 'is_autocommit' prop returns True when auto-commit enabled."""
        db = SqliterDB(memory=True, auto_commit=True)
        assert db.is_autocommit is True, "Expected True for auto-commit enabled"

    def test_is_autocommit_property_false(self) -> None:
        """Test 'is_autocommit' prop returns False when auto-commit disabled."""
        db = SqliterDB(memory=True, auto_commit=False)
        assert (
            db.is_autocommit is False
        ), "Expected False for auto-commit disabled"

    def test_is_connected_property_when_connected(self) -> None:
        """Test the 'is_connected' property when the database is connected."""
        db = SqliterDB(memory=True)
        with db.connect():
            assert db.is_connected is True, "Expected True when connected"

    def test_is_connected_property_when_disconnected(self) -> None:
        """Test 'is_connected' property when the database is disconnected."""
        db = SqliterDB(memory=True)
        assert db.is_connected is False, "Expected False when not connected"

    def test_table_names_property(self) -> None:
        """Test the 'table_names' property returns correct tables."""

        # Define a simple model for the test
        class TestTableModel(BaseDBModel):
            id: int

            class Meta:
                table_name = "test_table"

        # Create the database without using the context manager
        db = SqliterDB(memory=True)
        db.create_table(TestTableModel)  # ORM-based table creation

        # Verify that the table exists while the connection is still open
        table_names = db.table_names
        assert (
            "test_table" in table_names
        ), f"Expected 'test_table', got {table_names}"

        # Explicitly close the connection afterwards
        db.close()

    def test_table_names_property_when_disconnected(self) -> None:
        """Test the 'table_names' property with no active connection."""

        # Define a simple model for the test
        class AnotherTableModel(BaseDBModel):
            id: int

            class Meta:
                table_name = "another_table"

        # Create the database without the context manager
        db = SqliterDB(memory=True)
        db.create_table(AnotherTableModel)  # ORM-based table creation

        # Check the table names while the connection is still open
        table_names = db.table_names
        assert (
            "another_table" in table_names
        ), f"Expected 'another_table', got {table_names}"

        # Close the connection explicitly after the check
        db.close()

    def test_table_names_property_no_connection_error(self) -> None:
        """Test the 'table_names' property reconnects after disconnection.

        This test uses a real temp database file since sqlite3 seems to bypass
        the 'pyfakefs' filesystem.
        """
        with tempfile.NamedTemporaryFile(suffix=".sqlite") as temp_db:
            db_filename = temp_db.name

            # Define a simple model for the test
            class TestTableModel(BaseDBModel):
                id: int

                class Meta:
                    table_name = "test_table"

            # Create the database using the temporary file
            db = SqliterDB(db_filename=db_filename)
            db.create_table(TestTableModel)

            # Close the connection
            db.close()

            # Ensure that accessing table_names does NOT raise an error Since
            # it's file-based, the table should still exist after reconnecting
            table_names = db.table_names
            assert (
                "test_table" in table_names
            ), f"Expected 'test_table', got {table_names}"

    def test_table_names_connection_failure(self, mocker) -> None:
        """Test 'table_names' raises exception if the connection fails."""
        # Create an instance of the database
        db = SqliterDB(memory=True)

        # Mock the connect method to simulate a failed connection
        mocker.patch.object(db, "connect", return_value=None)

        # Close any existing connection to ensure db.conn is None
        db.close()

        # Attempt to access table_names and expect DatabaseConnectionError
        with pytest.raises(DatabaseConnectionError):
            _ = db.table_names
