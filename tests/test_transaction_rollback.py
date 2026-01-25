"""Test transaction rollback functionality.

These tests verify that the `with db:` context manager correctly rolls back
changes when an exception occurs inside the transaction block.
"""

import sqlite3
from contextlib import suppress

import pytest

from sqliter.model import BaseDBModel
from sqliter.sqliter import SqliterDB


class Item(BaseDBModel):
    """Simple model for testing transactions."""

    name: str
    quantity: int

    class Meta:
        """Configuration for the model."""

        table_name = "items"


def _raise_error() -> None:
    """Helper function to raise a RuntimeError for testing rollback."""
    err_msg = "Simulated error"
    raise RuntimeError(err_msg)


class TestTransactionRollback:
    """Test transaction rollback behavior."""

    def test_insert_rollback_on_exception(self, tmp_path) -> None:
        """Verify that insert is rolled back when an exception occurs."""
        db_file = tmp_path / "test_rollback.db"
        db = SqliterDB(db_filename=str(db_file))
        db.create_table(Item)
        db.close()

        # Try to insert within a transaction that fails
        db = SqliterDB(db_filename=str(db_file))
        with suppress(RuntimeError), db:
            db.insert(Item(name="Widget", quantity=10))
            _raise_error()

        # Verify the insert was rolled back
        db = SqliterDB(db_filename=str(db_file))
        result = db.select(Item).fetch_all()
        db.close()

        assert len(result) == 0, "Insert should have been rolled back"

    def test_update_rollback_on_exception(self, tmp_path) -> None:
        """Verify that update is rolled back when an exception occurs."""
        db_file = tmp_path / "test_rollback.db"
        db = SqliterDB(db_filename=str(db_file))
        db.create_table(Item)
        item = db.insert(Item(name="Widget", quantity=10))
        original_pk = item.pk
        db.close()

        # Try to update within a transaction that fails
        db = SqliterDB(db_filename=str(db_file))
        with suppress(RuntimeError), db:
            fetched = db.get(Item, original_pk)
            assert fetched is not None
            fetched.quantity = 5
            db.update(fetched)
            _raise_error()

        # Verify the update was rolled back
        db = SqliterDB(db_filename=str(db_file))
        result = db.get(Item, original_pk)
        db.close()

        assert result is not None
        assert result.quantity == 10, (
            f"Update should have been rolled back, got {result.quantity}"
        )

    def test_delete_rollback_on_exception(self, tmp_path) -> None:
        """Verify that delete is rolled back when an exception occurs."""
        db_file = tmp_path / "test_rollback.db"
        db = SqliterDB(db_filename=str(db_file))
        db.create_table(Item)
        item = db.insert(Item(name="Widget", quantity=10))
        original_pk = item.pk
        db.close()

        # Try to delete within a transaction that fails
        db = SqliterDB(db_filename=str(db_file))
        with suppress(RuntimeError), db:
            db.delete(Item, original_pk)
            _raise_error()

        # Verify the delete was rolled back
        db = SqliterDB(db_filename=str(db_file))
        result = db.get(Item, original_pk)
        db.close()

        assert result is not None, "Delete should have been rolled back"

    def test_query_builder_delete_rollback_on_exception(self, tmp_path) -> None:
        """Verify that QueryBuilder.delete is rolled back on exception."""
        db_file = tmp_path / "test_rollback.db"
        db = SqliterDB(db_filename=str(db_file))
        db.create_table(Item)
        db.insert(Item(name="Widget", quantity=10))
        db.insert(Item(name="Gadget", quantity=20))
        db.close()

        # Try to delete via query builder within a transaction that fails
        db = SqliterDB(db_filename=str(db_file))
        with suppress(RuntimeError), db:
            db.select(Item).filter(name="Widget").delete()
            _raise_error()

        # Verify the delete was rolled back
        db = SqliterDB(db_filename=str(db_file))
        result = db.select(Item).fetch_all()
        db.close()

        assert len(result) == 2, (
            "QueryBuilder delete should have been rolled back"
        )

    def test_multiple_operations_rollback(self, tmp_path) -> None:
        """Verify that multiple operations all rollback together."""
        db_file = tmp_path / "test_rollback.db"
        db = SqliterDB(db_filename=str(db_file))
        db.create_table(Item)
        item1 = db.insert(Item(name="Widget", quantity=10))
        item2 = db.insert(Item(name="Gadget", quantity=20))
        db.close()

        # Perform multiple operations in a failing transaction
        db = SqliterDB(db_filename=str(db_file))
        with suppress(RuntimeError), db:
            # Insert a new item
            db.insert(Item(name="Sprocket", quantity=30))

            # Update an existing item
            fetched = db.get(Item, item1.pk)
            assert fetched is not None
            fetched.quantity = 5
            db.update(fetched)

            # Delete another item
            db.delete(Item, item2.pk)

            # Raise an exception
            _raise_error()

        # Verify all operations were rolled back
        db = SqliterDB(db_filename=str(db_file))
        all_items = db.select(Item).order("pk").fetch_all()
        db.close()

        assert len(all_items) == 2, "Should still have 2 items"
        assert all_items[0].name == "Widget"
        assert all_items[0].quantity == 10, (
            "Widget quantity should be unchanged"
        )
        assert all_items[1].name == "Gadget"
        assert all_items[1].quantity == 20, "Gadget should not be deleted"

    def test_transaction_commit_success(self, tmp_path) -> None:
        """Verify that successful transaction commits all changes."""
        db_file = tmp_path / "test_rollback.db"
        db = SqliterDB(db_filename=str(db_file))
        db.create_table(Item)
        db.close()

        # Perform operations in a successful transaction
        db = SqliterDB(db_filename=str(db_file))
        with db:
            db.insert(Item(name="Widget", quantity=10))
            db.insert(Item(name="Gadget", quantity=20))

        # Verify all changes were committed
        db = SqliterDB(db_filename=str(db_file))
        result = db.select(Item).fetch_all()
        db.close()

        assert len(result) == 2, "Both inserts should have been committed"

    def test_no_intermediate_commits_in_transaction(self, tmp_path) -> None:
        """Verify that data isn't committed before transaction ends."""
        db_file = tmp_path / "test_rollback.db"
        db = SqliterDB(db_filename=str(db_file))
        db.create_table(Item)
        db.close()

        # Start a transaction and check from another connection
        db = SqliterDB(db_filename=str(db_file))
        with db:
            db.insert(Item(name="Widget", quantity=10))

            # Open a separate connection to check if data is visible
            separate_conn = sqlite3.connect(str(db_file))
            cursor = separate_conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM items")
            count = cursor.fetchone()[0]
            separate_conn.close()

            # Data should NOT be visible to other connections yet
            assert count == 0, "Data not visible during transaction"

        # After transaction commits, data should be visible
        separate_conn = sqlite3.connect(str(db_file))
        cursor = separate_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM items")
        count = cursor.fetchone()[0]
        separate_conn.close()

        assert count == 1, "Data should be visible after transaction commits"

    def test_context_manager_sets_transaction_flag(self, tmp_path) -> None:
        """Verify that context manager correctly sets _in_transaction flag."""
        db_file = tmp_path / "test_rollback.db"
        db = SqliterDB(db_filename=str(db_file))
        db.create_table(Item)
        db.close()

        db = SqliterDB(db_filename=str(db_file))
        # Verify the context manager sets the transaction flag correctly
        with db:
            db.insert(Item(name="Widget", quantity=10))
            # The flag is already set, but operations should still work
            assert db._in_transaction

        db = SqliterDB(db_filename=str(db_file))
        result = db.select(Item).fetch_all()
        db.close()
        assert len(result) == 1

    def test_autocommit_false_still_rolls_back(self, tmp_path) -> None:
        """Verify rollback works even with auto_commit=False."""
        db_file = tmp_path / "test_rollback.db"
        db = SqliterDB(db_filename=str(db_file), auto_commit=False)
        db.create_table(Item)
        db.commit()
        db.close()

        # Try to insert within a transaction that fails
        db = SqliterDB(db_filename=str(db_file), auto_commit=False)
        with suppress(RuntimeError), db:
            db.insert(Item(name="Widget", quantity=10))
            _raise_error()

        # Verify the insert was rolled back
        db = SqliterDB(db_filename=str(db_file))
        result = db.select(Item).fetch_all()
        db.close()

        assert len(result) == 0, "Insert should have been rolled back"

    def test_read_operation_in_transaction(self, tmp_path) -> None:
        """Verify read operations work inside a transaction."""
        db_file = tmp_path / "test_rollback.db"
        db = SqliterDB(db_filename=str(db_file))
        db.create_table(Item)
        db.insert(Item(name="Widget", quantity=10))
        db.close()

        # Read within a transaction
        db = SqliterDB(db_filename=str(db_file))
        with db:
            result = db.select(Item).fetch_all()
            assert len(result) == 1
            assert result[0].name == "Widget"

    def test_exception_type_preserved(self, tmp_path) -> None:
        """Verify that the original exception is re-raised after rollback."""
        db_file = tmp_path / "test_rollback.db"
        db = SqliterDB(db_filename=str(db_file))
        db.create_table(Item)
        db.close()

        def failing_transaction(database: SqliterDB) -> None:
            """Helper to run a transaction that raises ValueError."""
            with database:
                database.insert(Item(name="Widget", quantity=10))
                msg = "Custom error"
                raise ValueError(msg)

        db = SqliterDB(db_filename=str(db_file))
        with pytest.raises(ValueError, match="Custom error"):
            failing_transaction(db)
