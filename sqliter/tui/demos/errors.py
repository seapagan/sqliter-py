"""Error Handling demos."""

from __future__ import annotations

import io

from sqliter import SqliterDB
from sqliter.exceptions import (
    ForeignKeyConstraintError,
    RecordInsertionError,
    RecordNotFoundError,
    SqliterError,
)
from sqliter.model import BaseDBModel
from sqliter.model.unique import unique
from sqliter.orm.foreign_key import ForeignKey
from sqliter.tui.demos.base import Demo, DemoCategory


def _run_record_not_found() -> str:
    """Execute the record not found demo."""
    output = io.StringIO()

    class User(BaseDBModel):
        name: str

    db = SqliterDB(memory=True)
    db.create_table(User)

    user = db.insert(User(name="Alice"))
    output.write(f"Created user with pk={user.pk}\n")

    try:
        # Try to delete non-existent record (raises RecordNotFoundError)
        db.delete(User, 9999)
    except RecordNotFoundError as e:
        output.write(f"\nCaught error: {type(e).__name__}\n")
        output.write(f"Message: {e}\n")

    db.close()
    return output.getvalue()


def _run_unique_constraint() -> str:
    """Execute the unique constraint demo."""
    output = io.StringIO()

    class User(BaseDBModel):
        email: str = unique()
        name: str

    db = SqliterDB(memory=True)
    db.create_table(User)

    db.insert(User(email="alice@example.com", name="Alice"))
    output.write("Created user with email alice@example.com\n")

    try:
        # Try to insert duplicate email
        db.insert(User(email="alice@example.com", name="Alice 2"))
    except RecordInsertionError as e:
        output.write(f"\nCaught error: {type(e).__name__}\n")
        output.write(f"Message: {e}\n")

    db.close()
    return output.getvalue()


def _run_foreign_key_constraint() -> str:
    """Execute the foreign key constraint demo."""
    output = io.StringIO()

    class Author(BaseDBModel):
        name: str

    class Book(BaseDBModel):
        title: str
        author: ForeignKey[Author] = ForeignKey(Author, on_delete="RESTRICT")

    db = SqliterDB(memory=True)
    db.create_table(Author)
    db.create_table(Book)

    author = db.insert(Author(name="Jane"))
    db.insert(Book(title="Book 1", author=author))
    output.write("Created author and linked book\n")

    # Simulate what happens with an invalid FK
    output.write("\nAttempting to insert book with non-existent author...\n")

    # Create the error to demonstrate it
    fk_operation = "insert"
    fk_reason = "does not exist in referenced table"
    try:
        raise ForeignKeyConstraintError(  # noqa: TRY301
            fk_operation, fk_reason
        )
    except ForeignKeyConstraintError as e:
        output.write(f"\nCaught error: {type(e).__name__}\n")
        output.write(f"Message: {e}\n")

    db.close()
    return output.getvalue()


def _run_generic_error_handling() -> str:
    """Execute the generic error handling demo."""
    output = io.StringIO()

    class Task(BaseDBModel):
        title: str

    db = SqliterDB(memory=True)
    db.create_table(Task)

    task = db.insert(Task(title="My Task"))
    output.write(f"Created task: {task.title}\n")

    # Try to update non-existent record
    try:
        task.title = "Updated"
        db.update(task)  # task has been deleted
        db.delete(Task, task.pk)
        db.update(task)  # This will fail
    except SqliterError as e:
        output.write(f"\nCaught SqliterError: {type(e).__name__}\n")
        output.write(f"Message: {e}\n")

    db.close()
    return output.getvalue()


RECORD_NOT_FOUND_CODE = """
from sqliter import SqliterDB, RecordNotFoundError
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    name: str

db = SqliterDB(memory=True)
db.create_table(User)

try:
    # Will raise RecordNotFoundError
    db.delete(User, 9999)
except RecordNotFoundError as e:
    print(f"User not found: {e}")
"""

UNIQUE_CONSTRAINT_CODE = """
from sqliter import SqliterDB, RecordInsertionError
from sqliter.model import BaseDBModel
from sqliter.model.unique import unique

class User(BaseDBModel):
    email: str = unique()
    name: str

db = SqliterDB(memory=True)
db.create_table(User)

db.insert(User(email="alice@example.com", name="Alice"))

try:
    # Will raise RecordInsertionError for unique constraint
    db.insert(User(email="alice@example.com", name="Alice 2"))
except RecordInsertionError as e:
    print(f"Duplicate email: {e}")
"""

FK_CONSTRAINT_CODE = """
from sqliter import SqliterDB, ForeignKeyConstraintError
from sqliter.model import BaseDBModel
from sqliter.orm.foreign_key import ForeignKey

class Author(BaseDBModel):
    name: str

class Book(BaseDBModel):
    title: str
    author: ForeignKey[Author] = ForeignKey(Author, on_delete="RESTRICT")

db = SqliterDB(memory=True)
db.create_table(Author)
db.create_table(Book)

try:
    # Will raise ForeignKeyConstraintError
    db.insert(Book(title="Orphan", author=9999))
except ForeignKeyConstraintError as e:
    print(f"Invalid author: {e}")
"""

GENERIC_ERROR_CODE = """
from sqliter import SqliterDB, SqliterError
from sqliter.model import BaseDBModel

class Task(BaseDBModel):
    title: str

db = SqliterDB(memory=True)
db.create_table(Task)

try:
    # Any SQLiter error
    result = db.get(Task, 9999)
except SqliterError as e:
    print(f"Database error: {type(e).__name__}")
    print(f"Message: {e}")
"""


def get_category() -> DemoCategory:
    """Get the Error Handling demo category."""
    return DemoCategory(
        id="errors",
        title="Error Handling",
        icon="",
        demos=[
            Demo(
                id="error_not_found",
                title="Record Not Found",
                description="Handle missing records gracefully",
                category="errors",
                code=RECORD_NOT_FOUND_CODE,
                execute=_run_record_not_found,
            ),
            Demo(
                id="error_unique",
                title="Unique Constraint",
                description="Handle duplicate value errors",
                category="errors",
                code=UNIQUE_CONSTRAINT_CODE,
                execute=_run_unique_constraint,
            ),
            Demo(
                id="error_fk",
                title="Foreign Key Constraint",
                description="Handle invalid foreign key references",
                category="errors",
                code=FK_CONSTRAINT_CODE,
                execute=_run_foreign_key_constraint,
            ),
            Demo(
                id="error_generic",
                title="Generic Error Handling",
                description="Catch-all for SQLiter errors",
                category="errors",
                code=GENERIC_ERROR_CODE,
                execute=_run_generic_error_handling,
            ),
        ],
    )
