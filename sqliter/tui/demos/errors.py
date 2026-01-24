"""Error Handling demos."""

from __future__ import annotations

import io

from sqliter import ForeignKeyConstraintError, RecordNotFoundError, UniqueConstraintError
from sqliter.tui.demos.base import Demo, DemoCategory


def _run_record_not_found() -> str:
    """Execute the record not found demo."""
    output = io.StringIO()

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel

    class User(BaseDBModel):
        name: str

    db = SqliterDB(memory=True)
    db.create_table(User)

    user = db.insert(User(name="Alice"))
    output.write(f"Created user with pk={user.pk}\n")

    try:
        # Try to get non-existent record
        db.get(User, 9999)
    except RecordNotFoundError as e:
        output.write(f"\nCaught error: {type(e).__name__}\n")
        output.write(f"Message: {e}\n")

    db.close()
    return output.getvalue()


def _run_unique_constraint() -> str:
    """Execute the unique constraint demo."""
    output = io.StringIO()

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel
    from sqliter.model.unique import unique

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
    except UniqueConstraintError as e:
        output.write(f"\nCaught error: {type(e).__name__}\n")
        output.write(f"Message: {e}\n")

    db.close()
    return output.getvalue()


def _run_foreign_key_constraint() -> str:
    """Execute the foreign key constraint demo."""
    output = io.StringIO()

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel
    from sqliter.orm.foreign_key import ForeignKey

    class Author(BaseDBModel):
        name: str

    class Book(BaseDBModel):
        title: str
        author: Author = ForeignKey(Author, on_delete="RESTRICT")

    db = SqliterDB(memory=True)
    db.create_table(Author)
    db.create_table(Book)

    author = db.insert(Author(name="Jane"))
    db.insert(Book(title="Book 1", author_id=author.pk))
    output.write("Created author and linked book\n")

    try:
        # Try to insert book with invalid author_id
        db.insert(Book(title="Book 2", author_id=9999))
    except ForeignKeyConstraintError as e:
        output.write(f"\nCaught error: {type(e).__name__}\n")
        output.write(f"Message: {e}\n")

    db.close()
    return output.getvalue()


def _run_generic_error_handling() -> str:
    """Execute the generic error handling demo."""
    output = io.StringIO()

    from sqliter import SqliterDB, SqliterError
    from sqliter.model import BaseDBModel

    class Task(BaseDBModel):
        title: str

    db = SqliterDB(memory=True)
    db.create_table(Task)

    task = db.insert(Task(title="My Task"))
    output.write(f"Created task: {task.title}\n")

    # Try to update non-existent record
    try:
        db.update(task, title="Updated")  # task has been deleted
        db.delete(task)
        db.update(task, title="This will fail")
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
    user = db.get(User, 9999)
except RecordNotFoundError as e:
    print(f"User not found: {e}")
"""

UNIQUE_CONSTRAINT_CODE = """
from sqliter import SqliterDB, UniqueConstraintError
from sqliter.model import BaseDBModel
from sqliter.model.unique import unique

class User(BaseDBModel):
    email: str = unique()
    name: str

db = SqliterDB(memory=True)
db.create_table(User)

db.insert(User(email="alice@example.com", name="Alice"))

try:
    # Will raise UniqueConstraintError
    db.insert(User(email="alice@example.com", name="Alice 2"))
except UniqueConstraintError as e:
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
    author: Author = ForeignKey(Author, on_delete="RESTRICT")

db = SqliterDB(memory=True)
db.create_table(Author)
db.create_table(Book)

try:
    # Will raise ForeignKeyConstraintError
    db.insert(Book(title="Orphan", author_id=9999))
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
