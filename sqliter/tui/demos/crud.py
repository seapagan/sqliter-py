"""CRUD Operations demos."""

from __future__ import annotations

import io

from sqliter import SqliterDB
from sqliter.model import BaseDBModel
from sqliter.tui.demos.base import Demo, DemoCategory, extract_demo_code


def _run_insert() -> str:
    """Insert new records into the database.

    Use db.insert() to add new records, which returns the inserted
    object with auto-generated primary key.
    """
    output = io.StringIO()

    class User(BaseDBModel):
        name: str
        email: str

    db = SqliterDB(memory=True)
    db.create_table(User)

    user1 = db.insert(User(name="Alice", email="alice@example.com"))
    output.write(f"Inserted: {user1.name} (pk={user1.pk})\n")

    user2 = db.insert(User(name="Bob", email="bob@example.com"))
    output.write(f"Inserted: {user2.name} (pk={user2.pk})\n")

    db.close()
    return output.getvalue()


def _run_get_by_pk() -> str:
    """Retrieve a single record by primary key.

    Use db.get(Model, pk) to fetch a specific record quickly.
    """
    output = io.StringIO()

    class Task(BaseDBModel):
        title: str
        done: bool = False

    db = SqliterDB(memory=True)
    db.create_table(Task)

    task: Task = db.insert(Task(title="Buy groceries"))
    output.write(f"Created: {task.title} (pk={task.pk})\n")

    retrieved = db.get(Task, task.pk)
    if retrieved is not None:
        output.write(f"Retrieved: {retrieved.title}\n")
        output.write(f"Same object: {retrieved.pk == task.pk}\n")

    db.close()
    return output.getvalue()


def _run_update() -> str:
    """Update existing records in the database.

    Modify field values and call db.update() to persist changes.
    """
    output = io.StringIO()

    class Item(BaseDBModel):
        name: str
        quantity: int

    db = SqliterDB(memory=True)
    db.create_table(Item)

    item = db.insert(Item(name="Apples", quantity=5))
    output.write(f"Created: {item.name} x{item.quantity}\n")

    item.quantity = 10
    db.update(item)
    output.write(f"Updated: {item.name} x{item.quantity}\n")

    db.close()
    return output.getvalue()


def _run_delete() -> str:
    """Delete records from the database.

    Use db.delete(Model, pk) to permanently remove a record.
    """
    output = io.StringIO()

    class Note(BaseDBModel):
        content: str

    db = SqliterDB(memory=True)
    db.create_table(Note)

    note = db.insert(Note(content="Temporary note"))
    output.write(f"Created note (pk={note.pk})\n")

    db.delete(Note, note.pk)
    output.write(f"Deleted note with pk={note.pk}\n")

    all_notes = db.select(Note).fetch_all()
    output.write(f"Remaining notes: {len(all_notes)}\n")

    db.close()
    return output.getvalue()


def get_category() -> DemoCategory:
    """Get the CRUD Operations demo category."""
    return DemoCategory(
        id="crud",
        title="CRUD Operations",
        icon="",
        demos=[
            Demo(
                id="crud_insert",
                title="Insert Records",
                description="Create new records in the database",
                category="crud",
                code=extract_demo_code(_run_insert),
                execute=_run_insert,
            ),
            Demo(
                id="crud_get",
                title="Get by Primary Key",
                description="Retrieve a record by its primary key",
                category="crud",
                code=extract_demo_code(_run_get_by_pk),
                execute=_run_get_by_pk,
            ),
            Demo(
                id="crud_update",
                title="Update Records",
                description="Modify existing records",
                category="crud",
                code=extract_demo_code(_run_update),
                execute=_run_update,
            ),
            Demo(
                id="crud_delete",
                title="Delete Records",
                description="Remove records from the database",
                category="crud",
                code=extract_demo_code(_run_delete),
                execute=_run_delete,
            ),
        ],
    )
