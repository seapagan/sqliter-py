"""Error Handling demos."""

from __future__ import annotations

import io
from typing import Annotated

from pydantic import ValidationError

from sqliter import SqliterDB
from sqliter.exceptions import (
    ForeignKeyConstraintError,
    RecordInsertionError,
    RecordNotFoundError,
    SqliterError,
)
from sqliter.model import BaseDBModel
from sqliter.model.unique import unique
from sqliter.orm import BaseDBModel as ORMBaseDBModel
from sqliter.orm import ForeignKey
from sqliter.tui.demos.base import Demo, DemoCategory, extract_demo_code


def _run_record_not_found() -> str:
    """Handle attempts to access non-existent records.

    RecordNotFoundError is raised when trying to get/update/delete
    a record that doesn't exist.
    """
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
    """Handle violations of unique field constraints.

    RecordInsertionError is raised when inserting a duplicate value
    into a field marked as unique().
    """
    output = io.StringIO()

    class User(BaseDBModel):
        email: Annotated[str, unique()]
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


def _run_validation_error() -> str:
    """Handle Pydantic validation errors.

    ValidationError occurs when data doesn't match the field type
    or constraints defined in the model.
    """
    output = io.StringIO()

    class Product(BaseDBModel):
        name: str
        price: float
        quantity: int

    db = SqliterDB(memory=True)
    db.create_table(Product)

    product = db.insert(Product(name="Widget", price=19.99, quantity=100))
    output.write(f"Created product: {product.name}, price: ${product.price}\n")

    # Try to create product with invalid data (wrong types)
    output.write("\nAttempting to create product with invalid data...\n")

    try:
        # Wrong types: price should be float, quantity should be int
        # ValidationError is raised by Pydantic during model instantiation
        Product(name="Invalid Widget", price="free", quantity="lots")
    except ValidationError as e:
        output.write(f"\nCaught error: {type(e).__name__}\n")
        output.write(f"Message: {e}\n")

    db.close()
    return output.getvalue()


def _run_foreign_key_constraint() -> str:
    """Handle foreign key constraint violations.

    ForeignKeyConstraintError occurs when referencing a non-existent
    related record or violating referential integrity.
    """
    output = io.StringIO()

    class Author(ORMBaseDBModel):
        name: str

    class Book(ORMBaseDBModel):
        title: str
        author: ForeignKey[Author] = ForeignKey(Author, on_delete="RESTRICT")

    db = SqliterDB(memory=True)
    db.create_table(Author)
    db.create_table(Book)

    author = db.insert(Author(name="Jane"))
    db.insert(Book(title="Book 1", author=author))
    output.write("Created author and linked book\n")

    # Attempt to insert book with non-existent author
    output.write("\nAttempting to insert book with non-existent author...\n")

    try:
        # Create book with invalid author_id (doesn't exist in database)
        invalid_book = Book(title="Orphan Book", author_id=9999)
        db.insert(invalid_book)
    except ForeignKeyConstraintError as e:
        output.write(f"\nCaught error: {type(e).__name__}\n")
        output.write(f"Message: {e}\n")

    db.close()
    return output.getvalue()


def _run_generic_error_handling() -> str:
    """Catch all SQLiter errors with the base SqliterError class.

    Use SqliterError for generic error handling when you don't need
    to distinguish between specific error types.
    """
    output = io.StringIO()

    class Task(BaseDBModel):
        title: str

    db = SqliterDB(memory=True)
    db.create_table(Task)

    task = db.insert(Task(title="My Task"))
    output.write(f"Created task: {task.title}\n")

    # Try to update a deleted record
    try:
        task.title = "Updated"
        db.delete(Task, task.pk)
        db.update(task)  # This will fail
    except SqliterError as e:
        output.write(f"\nCaught SqliterError: {type(e).__name__}\n")
        output.write(f"Message: {e}\n")

    db.close()
    return output.getvalue()


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
                code=extract_demo_code(_run_record_not_found),
                execute=_run_record_not_found,
            ),
            Demo(
                id="error_unique",
                title="Unique Constraint",
                description="Handle duplicate value errors",
                category="errors",
                code=extract_demo_code(_run_unique_constraint),
                execute=_run_unique_constraint,
            ),
            Demo(
                id="error_validation",
                title="Validation Error",
                description="Handle Pydantic validation errors",
                category="errors",
                code=extract_demo_code(_run_validation_error),
                execute=_run_validation_error,
            ),
            Demo(
                id="error_fk",
                title="Foreign Key Constraint",
                description="Handle invalid foreign key references",
                category="errors",
                code=extract_demo_code(_run_foreign_key_constraint),
                execute=_run_foreign_key_constraint,
            ),
            Demo(
                id="error_generic",
                title="Generic Error Handling",
                description="Catch-all for SQLiter errors",
                category="errors",
                code=extract_demo_code(_run_generic_error_handling),
                execute=_run_generic_error_handling,
            ),
        ],
    )
