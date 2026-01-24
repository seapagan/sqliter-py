"""CRUD Operations demos."""

from __future__ import annotations

import io

from sqliter.tui.demos.base import Demo, DemoCategory


def _run_insert() -> str:
    """Execute the insert demo."""
    output = io.StringIO()

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel

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
    """Execute the get by primary key demo."""
    output = io.StringIO()

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel

    class Task(BaseDBModel):
        title: str
        done: bool = False

    db = SqliterDB(memory=True)
    db.create_table(Task)

    task = db.insert(Task(title="Buy groceries"))
    output.write(f"Created: {task.title} (pk={task.pk})\n")

    retrieved = db.get(Task, task.pk)
    output.write(f"Retrieved: {retrieved.title}\n")
    output.write(f"Same object: {retrieved.pk == task.pk}\n")

    db.close()
    return output.getvalue()


def _run_update() -> str:
    """Execute the update demo."""
    output = io.StringIO()

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel

    class Item(BaseDBModel):
        name: str
        quantity: int

    db = SqliterDB(memory=True)
    db.create_table(Item)

    item = db.insert(Item(name="Apples", quantity=5))
    output.write(f"Created: {item.name} x{item.quantity}\n")

    updated = db.update(item, quantity=10)
    output.write(f"Updated: {updated.name} x{updated.quantity}\n")

    db.close()
    return output.getvalue()


def _run_delete() -> str:
    """Execute the delete demo."""
    output = io.StringIO()

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel

    class Note(BaseDBModel):
        content: str

    db = SqliterDB(memory=True)
    db.create_table(Note)

    note = db.insert(Note(content="Temporary note"))
    output.write(f"Created note (pk={note.pk})\n")

    deleted = db.delete(note)
    output.write(f"Deleted: {deleted}\n")

    all_notes = db.select(Note).fetch_all()
    output.write(f"Remaining notes: {len(all_notes)}\n")

    db.close()
    return output.getvalue()


INSERT_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    name: str
    email: str

db = SqliterDB(memory=True)
db.create_table(User)

user = db.insert(User(name="Alice", email="alice@example.com"))
print(f"Inserted: {user.name} with pk={user.pk}")
"""

GET_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Task(BaseDBModel):
    title: str
    done: bool = False

db = SqliterDB(memory=True)
db.create_table(Task)

task = db.insert(Task(title="Buy groceries"))
retrieved = db.get(Task, task.pk)

print(f"Retrieved: {retrieved.title}")
"""

UPDATE_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Item(BaseDBModel):
    name: str
    quantity: int

db = SqliterDB(memory=True)
db.create_table(Item)

item = db.insert(Item(name="Apples", quantity=5))
updated = db.update(item, quantity=10)

print(f"Updated quantity: {updated.quantity}")
"""

DELETE_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Note(BaseDBModel):
    content: str

db = SqliterDB(memory=True)
db.create_table(Note)

note = db.insert(Note(content="Temporary note"))
deleted = db.delete(note)

print(f"Deleted: {deleted}")
"""


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
                code=INSERT_CODE,
                execute=_run_insert,
            ),
            Demo(
                id="crud_get",
                title="Get by Primary Key",
                description="Retrieve a record by its primary key",
                category="crud",
                code=GET_CODE,
                execute=_run_get_by_pk,
            ),
            Demo(
                id="crud_update",
                title="Update Records",
                description="Modify existing records",
                category="crud",
                code=UPDATE_CODE,
                execute=_run_update,
            ),
            Demo(
                id="crud_delete",
                title="Delete Records",
                description="Remove records from the database",
                category="crud",
                code=DELETE_CODE,
                execute=_run_delete,
            ),
        ],
    )
