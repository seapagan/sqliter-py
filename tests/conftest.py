"""Configuration for pytest."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Optional, Union

import pytest

from sqliter.model import BaseDBModel
from sqliter.sqliter import SqliterDB

if TYPE_CHECKING:
    from collections.abc import Generator

memory_db = ":memory:"


@contextmanager
def not_raises(exception) -> Generator[None, Any, None]:
    """Fake a pytest.raises context manager that does not raise an exception.

    Use: `with not_raises(Exception):`
    """
    try:
        yield
    except exception:
        err = f"DID RAISE {exception}"
        pytest.fail(err)


class ExampleModel(BaseDBModel):
    """Define a model to use in the tests."""

    slug: str
    name: str
    content: str

    class Meta:
        """Configuration for the model."""

        create_pk: bool = False
        primary_key: str = "slug"
        table_name: str = "test_table"


class PersonModel(BaseDBModel):
    """Model to test advanced filters."""

    name: Optional[str]
    age: Optional[int]

    class Meta:
        """Configuration for the model."""

        create_pk = False
        table_name = "person_table"
        primary_key = "name"


class DetailedPersonModel(BaseDBModel):
    """Model to test advanced field selection."""

    name: str
    age: int
    email: str
    address: str
    phone: str
    occupation: str

    class Meta:
        """Configuration for the model."""

        table_name = "detailed_person_table"
        primary_key = "name"
        create_pk = False


class ComplexModel(BaseDBModel):
    """Model to test complex field types."""

    id: int
    name: str
    age: float
    is_active: bool
    score: Union[int, float]
    nullable_field: Optional[str]

    class Meta:
        """Configuration for the model."""

        table_name = "complex_model"
        primary_key = "id"
        create_pk = False


@pytest.fixture
def db_mock() -> SqliterDB:
    """Fixture to create a SqliterDB class with an in-memory SQLite database."""
    db = SqliterDB(memory_db)
    db.create_table(ExampleModel)
    return db


@pytest.fixture
def db_mock_adv() -> SqliterDB:
    """Fixture to create a SqliterDB class with an in-memory SQLite database."""
    db = SqliterDB(memory_db)
    db.create_table(PersonModel)

    db.insert(PersonModel(name="Alice", age=25))
    db.insert(PersonModel(name="Bob", age=30))
    db.insert(PersonModel(name="Charlie", age=35))

    return db


@pytest.fixture
def db_mock_detailed() -> SqliterDB:
    """Fixture to create a SqliterDB class with detailed person data.

    This will be used to test advanced field selection.
    """
    db = SqliterDB(memory_db)
    db.create_table(DetailedPersonModel)

    db.insert(
        DetailedPersonModel(
            name="Alice",
            age=25,
            email="alice@example.com",
            address="123 Main St",
            phone="555-1234",
            occupation="Engineer",
        )
    )
    db.insert(
        DetailedPersonModel(
            name="Bob",
            age=30,
            email="bob@example.com",
            address="456 Elm St",
            phone="555-5678",
            occupation="Designer",
        )
    )
    db.insert(
        DetailedPersonModel(
            name="Charlie",
            age=35,
            email="charlie@example.com",
            address="789 Oak St",
            phone="555-9012",
            occupation="Manager",
        )
    )

    return db
