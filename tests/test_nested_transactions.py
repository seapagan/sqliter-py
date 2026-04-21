"""Regression tests for nested transaction contexts."""

from contextlib import suppress
from pathlib import Path

from sqliter.model import BaseDBModel
from sqliter.sqliter import SqliterDB


class Item(BaseDBModel):
    """Simple model for nested transaction tests."""

    name: str

    class Meta:
        """Configuration for the model."""

        table_name = "nested_items"


class TestNestedTransactions:
    """Verify nested `with db:` blocks share one transaction."""

    def test_nested_contexts_rollback_as_one_unit(self, tmp_path: Path) -> None:
        """Outer rollback should undo work done before and after inner exit."""
        db_file = tmp_path / "nested_transactions.db"
        db = SqliterDB(db_filename=str(db_file))
        db.create_table(Item)
        db.close()

        db = SqliterDB(db_filename=str(db_file))
        with suppress(RuntimeError), db:
            db.insert(Item(name="outer-before"))
            with db:
                db.insert(Item(name="inner"))

            assert db.in_transaction is True
            db.insert(Item(name="outer-after"))
            msg = "rollback nested transaction"
            raise RuntimeError(msg)

        db = SqliterDB(db_filename=str(db_file))
        result = db.select(Item).fetch_all()
        db.close()

        assert result == []
