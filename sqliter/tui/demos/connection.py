"""Connection & Setup demos."""

from __future__ import annotations

import io
import tempfile
from pathlib import Path

from sqliter import SqliterDB
from sqliter.model import BaseDBModel
from sqliter.tui.demos.base import Demo, DemoCategory, extract_demo_code


def _run_memory_db() -> str:
    """Create an in-memory SQLite database.

    Use memory=True for fast, temporary databases that don't persist.
    """
    output = io.StringIO()

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
    """Create a file-based SQLite database for persistent storage.

    Provide a file path to store data that persists across sessions.
    """
    output = io.StringIO()

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        db = SqliterDB(db_path)
        output.write("Created file database\n")
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
    """Enable debug mode to see SQL queries being executed.

    Set debug=True to log all SQL queries to the console for debugging.
    """
    output = io.StringIO()

    output.write("Debug mode enables SQL query logging.\n")
    output.write("When debug=True, all SQL queries are logged.\n\n")

    class User(BaseDBModel):
        name: str

    db = SqliterDB(memory=True, debug=True)
    db.create_table(User)

    output.write("SQL queries would be logged to console:\n")
    output.write('  CREATE TABLE IF NOT EXISTS "users" (...)\n')

    db.close()
    return output.getvalue()


def _run_context_manager() -> str:
    """Use context manager for automatic connection management.

    The `with db:` block handles connection, transactions, and cleanup.
    """
    output = io.StringIO()

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
                code=extract_demo_code(_run_memory_db),
                execute=_run_memory_db,
            ),
            Demo(
                id="conn_file",
                title="File-based Database",
                description="Create a persistent file database",
                category="connection",
                code=extract_demo_code(_run_file_db),
                execute=_run_file_db,
            ),
            Demo(
                id="conn_debug",
                title="Debug Mode",
                description="Enable SQL query logging",
                category="connection",
                code=extract_demo_code(_run_debug_mode),
                execute=_run_debug_mode,
            ),
            Demo(
                id="conn_context",
                title="Context Manager",
                description="Auto commit/rollback with 'with' statement",
                category="connection",
                code=extract_demo_code(_run_context_manager),
                execute=_run_context_manager,
            ),
        ],
        expanded=True,  # First category starts expanded
    )
