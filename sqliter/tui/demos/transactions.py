"""Transaction demos."""

from __future__ import annotations

import io
import tempfile
from pathlib import Path

from sqliter import SqliterDB
from sqliter.model import BaseDBModel
from sqliter.tui.demos.base import Demo, DemoCategory, extract_demo_code


def _run_context_manager_transaction() -> str:
    """Use context manager for automatic transaction management.

    The `with db:` block auto-commits on success and rolls back on error.
    """
    output = io.StringIO()

    class Account(BaseDBModel):
        name: str
        balance: float

    db = SqliterDB(memory=True)
    db.create_table(Account)

    alice: Account = db.insert(Account(name="Alice", balance=100.0))
    bob: Account = db.insert(Account(name="Bob", balance=50.0))

    output.write(f"Before: Alice=${alice.balance}, Bob=${bob.balance}\n")

    # Transfer money using context manager
    with db:
        alice.balance = alice.balance - 20.0
        bob.balance = bob.balance + 20.0
        db.update(alice)
        db.update(bob)
        alice_updated = alice
        bob_updated = bob

    output.write(
        f"After: Alice=${alice_updated.balance}, Bob=${bob_updated.balance}\n"
    )
    output.write("Transaction auto-committed on success\n")

    db.close()
    return output.getvalue()


def _run_rollback() -> str:
    """Demonstrate transaction rollback behavior.

    When an exception occurs inside a `with db:` block, all changes made
    within that transaction are automatically rolled back.
    """
    output = io.StringIO()

    class Item(BaseDBModel):
        name: str
        quantity: int

    # Use file database so we can reconnect after connection closes
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    db = None
    try:
        db = SqliterDB(db_filename=db_path)
        db.create_table(Item)

        item: Item = db.insert(Item(name="Widget", quantity=10))
        output.write(f"Initial quantity: {item.quantity}\n")

        # Use context manager for automatic rollback on error
        try:
            with db:
                item.quantity = 5
                db.update(item)
                output.write("Inside transaction: updated to 5\n")
                # If error occurs, changes are rolled back
                error_msg = "Intentional error for rollback"
                raise RuntimeError(error_msg)  # noqa: TRY301
        except RuntimeError:
            output.write("Error occurred - transaction rolled back\n")
            # Verify rollback with NEW connection
            db2 = SqliterDB(db_filename=db_path)
            try:
                restored = db2.get(Item, item.pk)
                if restored is not None:
                    qty_attr = "quantity"  # db.get returns BaseDBModel
                    restored_quantity = getattr(restored, qty_attr)
                    msg = f"Database value: {restored_quantity}\n"
                    output.write(msg)
                    expected_quantity = 10
                    if restored_quantity == expected_quantity:
                        output.write("✓ Rollback worked correctly\n")
                    else:
                        msg = (
                            f"✗ Rollback failed: expected {expected_quantity}, "
                            f"got {restored_quantity}\n"
                        )
                        output.write(msg)
            finally:
                db2.close()
    finally:
        if db is not None:
            db.close()
        Path(db_path).unlink(missing_ok=True)

    return output.getvalue()


def _run_manual_commit() -> str:
    """Manually control transactions with explicit commit.

    Call db.commit() to persist changes when not using context manager.
    """
    output = io.StringIO()

    class Log(BaseDBModel):
        message: str

    db = SqliterDB(memory=True)
    db.create_table(Log)

    # Manual transaction control
    db.connect()
    log1 = db.insert(Log(message="First entry"))
    output.write(f"Inserted: {log1.message}\n")
    output.write("Not committed yet\n")
    db.commit()
    output.write("Committed\n")

    db.insert(Log(message="Second entry"))
    db.commit()

    all_logs = db.select(Log).fetch_all()
    output.write(f"Total logs: {len(all_logs)}\n")

    db.close()
    return output.getvalue()


def get_category() -> DemoCategory:
    """Get the Transactions demo category."""
    return DemoCategory(
        id="transactions",
        title="Transactions",
        icon="",
        demos=[
            Demo(
                id="txn_context",
                title="Context Manager",
                description="Auto commit/rollback with 'with' statement",
                category="transactions",
                code=extract_demo_code(_run_context_manager_transaction),
                execute=_run_context_manager_transaction,
            ),
            Demo(
                id="txn_rollback",
                title="Rollback",
                description="Automatic rollback on errors",
                category="transactions",
                code=extract_demo_code(_run_rollback),
                execute=_run_rollback,
            ),
            Demo(
                id="txn_manual",
                title="Manual Commit",
                description="Manually control transactions",
                category="transactions",
                code=extract_demo_code(_run_manual_commit),
                execute=_run_manual_commit,
            ),
        ],
    )
