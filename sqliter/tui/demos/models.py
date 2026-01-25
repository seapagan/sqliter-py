"""Models & Tables demos."""

from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Optional, Union

from sqliter import SqliterDB
from sqliter.model import BaseDBModel
from sqliter.tui.demos.base import Demo, DemoCategory, extract_demo_code


def _run_basic_model() -> str:
    """Define a simple model with automatic primary key generation.

    BaseDBModel provides an auto-incrementing 'pk' field and handles
    all the database table creation.
    """
    output = io.StringIO()

    class User(BaseDBModel):
        name: str
        age: int
        email: str

    db = SqliterDB(memory=True)
    db.create_table(User)

    user = db.insert(User(name="Alice", age=30, email="alice@example.com"))
    output.write(f"Created user: {user.name}\n")
    output.write(f"Primary key: {user.pk}\n")
    output.write(f"Age: {user.age}\n")
    output.write(f"Email: {user.email}\n")

    db.close()
    return output.getvalue()


def _run_custom_table_name() -> str:
    """Override the auto-generated table name.

    Set __tablename__ to use a custom table name instead of the
    auto-pluralized model class name.
    """
    output = io.StringIO()

    class Person(BaseDBModel):
        """Person model with custom table name."""

        __tablename__ = "people"
        name: str

    db = SqliterDB(memory=True)
    db.create_table(Person)

    output.write(f"Table created: {Person.__tablename__}\n")
    output.write("The model uses 'people' instead of 'persons'\n")

    person = db.insert(Person(name="Bob"))
    output.write(f"Inserted: {person.name} (pk={person.pk})\n")

    db.close()
    return output.getvalue()


def _run_field_types() -> str:
    """Use various field types in your models.

    BaseDBModel supports str, int, float, bool, and more with automatic
    type conversion and validation.
    """
    output = io.StringIO()

    class Product(BaseDBModel):
        name: str
        price: float
        in_stock: bool
        quantity: int
        created_at: int

    db = SqliterDB(memory=True)
    db.create_table(Product)

    product = db.insert(
        Product(
            name="Widget",
            price=19.99,
            in_stock=True,
            quantity=100,
            created_at=int(datetime.now(timezone.utc).timestamp()),
        ),
    )
    output.write(f"Product: {product.name}\n")
    output.write(f"Price: ${product.price}\n")
    output.write(f"In stock: {product.in_stock}\n")
    output.write(f"Quantity: {product.quantity}\n")
    output.write(f"Created: {product.created_at}\n")

    db.close()
    return output.getvalue()


def _run_optional_fields() -> str:
    """Define fields that can be NULL (optional) in the database.

    Use Optional[T] or Union[T, None] for nullable fields, with
    optional default values.
    """
    output = io.StringIO()

    class Article(BaseDBModel):
        title: str
        content: Optional[str]
        author: Optional[str] = "Anonymous"

    db = SqliterDB(memory=True)
    db.create_table(Article)

    article1 = db.insert(Article(title="First Post", content=None))
    output.write(f"Article 1: {article1.title}\n")
    output.write(f"Content: {article1.content}\n")
    output.write(f"Author: {article1.author}\n")

    article2 = db.insert(
        Article(title="Second Post", content="Hello world!", author="Bob"),
    )
    output.write(f"\nArticle 2: {article2.title}\n")
    output.write(f"Content: {article2.content}\n")
    output.write(f"Author: {article2.author}\n")

    db.close()
    return output.getvalue()


def _run_default_values() -> str:
    """Set default values for fields.

    Assign default values in the model definition to use when
    inserting records without specifying those fields.
    """
    output = io.StringIO()

    class Task(BaseDBModel):
        title: str
        completed: bool = False
        priority: int = 1

    db = SqliterDB(memory=True)
    db.create_table(Task)

    task = db.insert(Task(title="New task"))
    output.write(f"Task: {task.title}\n")
    output.write(f"Completed: {task.completed} (default)\n")
    output.write(f"Priority: {task.priority} (default)\n")

    db.close()
    return output.getvalue()


def _run_complex_types() -> str:
    """Store complex data types like lists and dicts.

    BaseDBModel automatically serializes lists, dicts, sets, and tuples
    to BLOBs for SQLite storage, and deserializes them back.
    """
    output = io.StringIO()

    class Document(BaseDBModel):
        title: str
        tags: list[str]
        metadata: dict[str, Union[str, int]]

    db = SqliterDB(memory=True)
    db.create_table(Document)

    doc = db.insert(
        Document(
            title="Guide",
            tags=["python", "database", "tutorial"],
            metadata={"views": 1000, "rating": 4},
        ),
    )
    output.write(f"Document: {doc.title}\n")
    output.write(f"Tags: {doc.tags}\n")
    output.write(f"Metadata: {doc.metadata}\n")

    db.close()
    return output.getvalue()


def get_category() -> DemoCategory:
    """Get the Models & Tables demo category."""
    return DemoCategory(
        id="models",
        title="Models & Tables",
        icon="",
        demos=[
            Demo(
                id="model_basic",
                title="Basic Model",
                description="Define a simple model with fields",
                category="models",
                code=extract_demo_code(_run_basic_model),
                execute=_run_basic_model,
            ),
            Demo(
                id="model_custom_table",
                title="Custom Table Name",
                description="Specify a custom table name",
                category="models",
                code=extract_demo_code(_run_custom_table_name),
                execute=_run_custom_table_name,
            ),
            Demo(
                id="model_field_types",
                title="Field Types",
                description="Various field type examples",
                category="models",
                code=extract_demo_code(_run_field_types),
                execute=_run_field_types,
            ),
            Demo(
                id="model_optional",
                title="Optional Fields",
                description="Fields with None values and defaults",
                category="models",
                code=extract_demo_code(_run_optional_fields),
                execute=_run_optional_fields,
            ),
            Demo(
                id="model_defaults",
                title="Default Values",
                description="Fields with default values",
                category="models",
                code=extract_demo_code(_run_default_values),
                execute=_run_default_values,
            ),
            Demo(
                id="model_complex",
                title="Complex Types",
                description="Lists and dicts (stored as BLOBs)",
                category="models",
                code=extract_demo_code(_run_complex_types),
                execute=_run_complex_types,
            ),
        ],
    )
