"""Test the context-manager functionality."""

import sqlite3

import pytest

from sqliter.sqliter import SqliterDB
from tests.conftest import ExampleModel


class TestContextManager:
    """Test the context-manager functionality."""

    def test_transaction_commit_success(self, db_mock, mocker) -> None:
        """Test that the transaction commits successfully with no exceptions."""
        # Mock the connection's commit method to track the commit
        mock_commit = mocker.patch.object(db_mock, "conn", create=True)
        mock_commit.commit = mocker.MagicMock()

        # Run the context manager without errors
        with db_mock:
            """Dummy transaction."""

        # Ensure commit was called
        mock_commit.commit.assert_called_once()

    def test_transaction_closes_connection(self, db_mock, mocker) -> None:
        """Test the connection is closed after the transaction completes."""
        # Mock the connection object itself
        mock_conn = mocker.patch.object(db_mock, "conn", autospec=True)

        # Run the context manager
        with db_mock:
            """Dummy transaction."""

        # Ensure the connection is closed
        mock_conn.close.assert_called_once()

    def test_transaction_rollback_on_exception(self, db_mock, mocker) -> None:
        """Test that the transaction rolls back when an exception occurs."""
        # Mock the connection object and ensure it's set as db_mock.conn
        mock_conn = mocker.Mock()
        mocker.patch.object(db_mock, "conn", mock_conn)

        # Simulate an exception within the context manager
        message = "Simulated error"
        with pytest.raises(ValueError, match=message), db_mock:
            raise ValueError(message)

        # Ensure rollback was called on the mocked connection
        mock_conn.rollback.assert_called_once()
        mock_conn.commit.assert_not_called()

    def test_in_transaction_flag(self, db_mock) -> None:
        """Test that _in_transaction is set/unset inside a transaction."""
        assert not db_mock._in_transaction  # Initially, it should be False

        with db_mock:
            assert db_mock._in_transaction  # Should be True inside the context

        assert (
            not db_mock._in_transaction
        )  # Should be False again after exiting the context

    def test_rollback_resets_in_transaction_flag(self, db_mock, mocker) -> None:
        """Test that _in_transaction is reset after a rollback on exception."""

        def test_transaction() -> None:
            assert db_mock._in_transaction  # Should be True during transaction
            err_msg = "Simulated error"
            raise ValueError(err_msg)

        mock_conn = mocker.Mock()
        mocker.patch.object(db_mock, "conn", mock_conn)

        with pytest.raises(ValueError, match="Simulated error"), db_mock:
            test_transaction()

        assert (
            not db_mock._in_transaction
        )  # Should be reset to False after exception

    def test_maybe_commit_skips_in_transaction(self, db_mock, mocker) -> None:
        """Test that maybe_commit does not commit when inside a transaction."""
        mock_conn = mocker.Mock()
        mocker.patch.object(db_mock, "conn", mock_conn)

        with db_mock:
            db_mock._maybe_commit()
            mock_conn.commit.assert_not_called()

        db_mock._maybe_commit()
        mock_conn.commit.assert_called_once()

    def test_commit_called_once_in_transaction(self, mocker, tmp_path) -> None:
        """Ensure data is committed at the end of a transaction."""
        # Create a temporary database file
        db_file = tmp_path / "test.db"

        # Initialize the database with the file-based database
        db_mock = SqliterDB(db_filename=str(db_file), auto_commit=True)
        db_mock.create_table(ExampleModel)

        # Use the context manager to simulate a transaction
        with db_mock:
            db_mock.insert(
                ExampleModel(slug="test", name="Test", content="Test content")
            )

        # After the transaction, open a new connection to query the database
        new_conn = sqlite3.connect(str(db_file))
        result = new_conn.execute(
            "SELECT * FROM test_table WHERE slug = 'test'"
        ).fetchone()

        # Assert that the data was committed
        assert result is not None, "Data was not committed."
        assert (
            result[3] == "test"
        ), f"Expected slug to be 'test', but got {result[3]}"

        # Close the new connection
        new_conn.close()
