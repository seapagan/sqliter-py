"""Connection & Setup demos."""

from __future__ import annotations

import io
import tempfile
from pathlib import Path

from sqliter.tui.demos.base import Demo, DemoCategory


def _run_memory_db() -> str:
    """Execute the in-memory database demo."""
    output = io.StringIO()

    from sqliter import SqliterDB

    db = SqliterDB(memory=True)
    output.write(f"Created database: {db}\n")
    output.write(f"Is memory: {db.is_memory}\n")
    output.write(f"Filename: {db.filename}\n")

    db.connect()
    output.write(f"Connected: {db.is_connected}\n")

    db.close()
    output.write(f"After close: {db.is_connected}\n")

    return output.getvalue()


def _run_file_db() -> str:
    """Execute the file-based database demo."""
    output = io.StringIO()

    from sqliter import SqliterDB

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        db = SqliterDB(db_path)
        output.write(f"Created file database\n")
        output.write(f"Filename: {db.filename}\n")
        output.write(f"Is memory: {db.is_memory}\n")

        db.connect()
        output.write(f"Connected to: {db_path}\n")
        db.close()
    finally:
        Path(db_path).unlink(missing_ok=True)
        output.write("Cleaned up database file\n")

    return output.getvalue()


def _run_debug_mode() -> str:
    """Execute the debug mode demo."""
    output = io.StringIO()

    output.write("Debug mode enables SQL query logging.\n")
    output.write("When debug=True, all SQL queries are logged.\n\n")

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel

    class User(BaseDBModel):
        name: str

    # Note: In real usage, debug output goes to logger
    db = SqliterDB(memory=True, debug=True)
    db.create_table(User)

    output.write("SQL queries would be logged to console:\n")
    output.write('  CREATE TABLE IF NOT EXISTS "users" (...)\n')

    db.close()
    return output.getvalue()


def _run_context_manager() -> str:
    """Execute the context manager demo."""
    output = io.StringIO()

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel

    class Task(BaseDBModel):
        title: str
        done: bool = False

    output.write("Using context manager for transactions:\n\n")

    db = SqliterDB(memory=True)

    with db:
        db.create_table(Task)
        task = db.insert(Task(title="Learn SQLiter", done=False))
        output.write(f"Inserted: {task.title} (pk={task.pk})\n")
        output.write("Transaction auto-commits on exit\n")

    output.write(f"\nAfter context: connected={db.is_connected}\n")
    return output.getvalue()


MEMORY_DB_CODE = """
from sqliter import SqliterDB

# Create an in-memory database
# Data is lost when connection closes
db = SqliterDB(memory=True)

# Check database properties
print(f"Is memory: {db.is_memory}")
print(f"Filename: {db.filename}")  # None for memory

# Connect and use
db.connect()
print(f"Connected: {db.is_connected}")

db.close()
"""

FILE_DB_CODE = """
from sqliter import SqliterDB

# Create a file-based database
# Data persists between sessions
db = SqliterDB("my_app.db")

# Or with explicit parameter
db = SqliterDB(db_filename="my_app.db")

print(f"Filename: {db.filename}")
print(f"Is memory: {db.is_memory}")  # False
"""

DEBUG_MODE_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    name: str

# Enable debug mode to see SQL queries
db = SqliterDB(memory=True, debug=True)
db.create_table(User)

# Console output:
# DEBUG Executing SQL: CREATE TABLE IF NOT EXISTS "users" (...)
"""

CONTEXT_MANAGER_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Task(BaseDBModel):
    title: str
    done: bool = False

db = SqliterDB(memory=True)

# Use as context manager for transactions
with db:
    db.create_table(Task)
    task = db.insert(Task(title="Learn SQLiter"))
    # Auto-commits on successful exit
    # Auto-rollback on exception

# Connection is closed after exiting
"""


def get_category() -> DemoCategory:
    """Get the Connection & Setup demo category."""
    return DemoCategory(
        id="connection",
        title="Connection & Setup",
        icon="",
        demos=[
            Demo(
                id="conn_memory",
                title="In-memory Database",
                description="Create a temporary in-memory database",
                category="connection",
                code=MEMORY_DB_CODE,
                execute=_run_memory_db,
            ),
            Demo(
                id="conn_file",
                title="File-based Database",
                description="Create a persistent file database",
                category="connection",
                code=FILE_DB_CODE,
                execute=_run_file_db,
            ),
            Demo(
                id="conn_debug",
                title="Debug Mode",
                description="Enable SQL query logging",
                category="connection",
                code=DEBUG_MODE_CODE,
                execute=_run_debug_mode,
            ),
            Demo(
                id="conn_context",
                title="Context Manager",
                description="Auto commit/rollback with 'with' statement",
                category="connection",
                code=CONTEXT_MANAGER_CODE,
                execute=_run_context_manager,
            ),
        ],
        expanded=True,  # First category starts expanded
    )
