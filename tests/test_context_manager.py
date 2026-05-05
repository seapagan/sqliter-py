"""Test the context-manager functionality."""

import sqlite3
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from sqliter.sqliter import SqliterDB
from tests.conftest import ExampleModel


class TestContextManager:
    """Test the context-manager functionality."""

    def test_transaction_commit_success(
        self, db_mock: SqliterDB, mocker: MockerFixture
    ) -> None:
        """Test that the transaction commits successfully with no exceptions."""
        # Mock the connection's commit method to track the commit
        mock_commit = mocker.patch.object(db_mock, "conn", create=True)
        mock_commit.commit = mocker.MagicMock()

        # Run the context manager without errors
        with db_mock:
            """Dummy transaction."""

        # Ensure commit was called
        mock_commit.commit.assert_called_once()

    def test_transaction_keeps_connection_open(
        self, db_mock: SqliterDB, mocker: MockerFixture
    ) -> None:
        """Test the connection stays open after the transaction completes."""
        # Mock the connection object itself
        mock_conn = mocker.patch.object(db_mock, "conn", autospec=True)

        # Run the context manager
        with db_mock:
            """Dummy transaction."""

        # Ensure the connection is not closed
        mock_conn.close.assert_not_called()

    def test_transaction_rollback_on_exception(
        self, db_mock: SqliterDB, mocker: MockerFixture
    ) -> None:
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

    def test_in_transaction_flag(self, db_mock: SqliterDB) -> None:
        """Test that _in_transaction is set/unset inside a transaction."""
        assert not db_mock._in_transaction  # Initially, it should be False

        with db_mock:
            assert db_mock._in_transaction  # Should be True inside the context

        assert (
            not db_mock._in_transaction
        )  # Should be False again after exiting the context

    def test_rollback_resets_in_transaction_flag(
        self, db_mock: SqliterDB, mocker: MockerFixture
    ) -> None:
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

    def test_maybe_commit_skips_in_transaction(
        self, db_mock: SqliterDB, mocker: MockerFixture
    ) -> None:
        """Test that maybe_commit does not commit when inside a transaction."""
        mock_conn = mocker.Mock()
        mocker.patch.object(db_mock, "conn", mock_conn)

        with db_mock:
            db_mock._maybe_commit()
            mock_conn.commit.assert_not_called()

        mock_conn.commit.assert_called_once()
        mock_conn.commit.reset_mock()
        db_mock._maybe_commit()
        mock_conn.commit.assert_called_once()

    def test_commit_called_once_in_transaction(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
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
        assert result[3] == "test", (
            f"Expected slug to be 'test', but got {result[3]}"
        )

        # Close the new connection
        new_conn.close()

    def test_context_manager_keeps_memory_database_available(self) -> None:
        """In-memory DB data survives after leaving the transaction context."""
        db = SqliterDB(memory=True)

        with db:
            db.create_table(ExampleModel)
            inserted = db.insert(
                ExampleModel(slug="persist", name="Persist", content="context")
            )

        fetched = db.get(ExampleModel, inserted.pk)

        assert fetched is not None
        assert fetched.slug == "persist"
        assert db.conn is not None
        db.close()

    def test_set_in_transaction_updates_state(self, db_mock: SqliterDB) -> None:
        """set_in_transaction should preserve nested depth and reset state."""
        db_mock.set_in_transaction(value=True)

        assert db_mock._transaction_depth == 1
        assert db_mock._in_transaction is True
        assert db_mock.in_transaction is True

        db_mock._transaction_depth = 2
        db_mock.set_in_transaction(value=True)

        assert db_mock._transaction_depth == 2
        assert db_mock._in_transaction is True
        assert db_mock.in_transaction is True

        db_mock._rollback_requested = True
        db_mock.set_in_transaction(value=False)

        assert db_mock._transaction_depth == 0
        assert db_mock._in_transaction is False
        assert db_mock.in_transaction is False
        assert db_mock._rollback_requested is False

    def test_close_resets_transaction_scope(self, db_mock: SqliterDB) -> None:
        """Close should clear stale transaction bookkeeping."""
        db_mock.set_in_transaction(value=True)
        db_mock._transaction_depth = 2
        db_mock._rollback_requested = True

        db_mock.close()

        assert db_mock.conn is None
        assert db_mock._transaction_depth == 0
        assert db_mock._in_transaction is False
        assert db_mock.in_transaction is False
        assert db_mock._rollback_requested is False
