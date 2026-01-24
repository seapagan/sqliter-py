"""Transaction demos."""

from __future__ import annotations

import io

from sqliter.tui.demos.base import Demo, DemoCategory


def _run_context_manager_transaction() -> str:
    """Execute the context manager transaction demo."""
    output = io.StringIO()

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel

    class Account(BaseDBModel):
        name: str
        balance: float

    db = SqliterDB(memory=True)
    db.create_table(Account)

    alice = db.insert(Account(name="Alice", balance=100.0))
    bob = db.insert(Account(name="Bob", balance=50.0))

    output.write(f"Before: Alice=${alice.balance}, Bob=${bob.balance}\n")

    # Transfer money using context manager
    with db:
        alice_updated = db.update(alice, balance=alice.balance - 20.0)
        bob_updated = db.update(bob, balance=bob.balance + 20.0)

    output.write(f"After: Alice=${alice_updated.balance}, Bob=${bob_updated.balance}\n")
    output.write("Transaction auto-committed on success\n")

    db.close()
    return output.getvalue()


def _run_rollback() -> str:
    """Execute the rollback demo."""
    output = io.StringIO()

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel

    class Item(BaseDBModel):
        name: str
        quantity: int

    db = SqliterDB(memory=True)
    db.create_table(Item)

    item = db.insert(Item(name="Widget", quantity=10))
    output.write(f"Initial quantity: {item.quantity}\n")

    try:
        with db:
            updated = db.update(item, quantity=5)
            output.write("Inside transaction: updated to 5\n")
            # Simulate error to trigger rollback
            msg = "Intentional error for rollback"
            raise RuntimeError(msg)
    except RuntimeError:
        output.write("Error occurred - transaction rolled back\n")

    # Check value was restored
    retrieved = db.get(Item, item.pk)
    output.write(f"After rollback: {retrieved.quantity}\n")

    db.close()
    return output.getvalue()


def _run_manual_commit() -> str:
    """Execute the manual commit demo."""
    output = io.StringIO()

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel

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

    log2 = db.insert(Log(message="Second entry"))
    db.commit()

    all_logs = db.select(Log).fetch_all()
    output.write(f"Total logs: {len(all_logs)}\n")

    db.close()
    return output.getvalue()


CONTEXT_MANAGER_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Account(BaseDBModel):
    name: str
    balance: float

db = SqliterDB(memory=True)
db.create_table(Account)

alice = db.insert(Account(name="Alice", balance=100.0))
bob = db.insert(Account(name="Bob", balance=50.0))

# Use context manager for atomic transactions
with db:
    db.update(alice, balance=alice.balance - 20.0)
    db.update(bob, balance=bob.balance + 20.0)

# Auto-commits on success, auto-rollback on error
"""

ROLLBACK_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Item(BaseDBModel):
    name: str
    quantity: int

db = SqliterDB(memory=True)
db.create_table(Item)

item = db.insert(Item(name="Widget", quantity=10))

try:
    with db:
        db.update(item, quantity=5)
        # If error occurs, changes are rolled back
        raise RuntimeError("Something went wrong")
except RuntimeError:
    pass

# Value is restored to 10
"""

MANUAL_COMMIT_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Log(BaseDBModel):
    message: str

db = SqliterDB(memory=True)
db.create_table(Log)

# Manual transaction control
db.connect()
log = db.insert(Log(message="Entry"))

# Make changes visible
db.commit()

db.close()
"""


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
                code=CONTEXT_MANAGER_CODE,
                execute=_run_context_manager_transaction,
            ),
            Demo(
                id="txn_rollback",
                title="Rollback",
                description="Automatic rollback on errors",
                category="transactions",
                code=ROLLBACK_CODE,
                execute=_run_rollback,
            ),
            Demo(
                id="txn_manual",
                title="Manual Commit",
                description="Manually control transactions",
                category="transactions",
                code=MANUAL_COMMIT_CODE,
                execute=_run_manual_commit,
            ),
        ],
    )
