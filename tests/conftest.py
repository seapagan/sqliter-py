"""Configuration for pytest."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Optional

import pytest
from sqliter.model import BaseDBModel
from sqliter.sqliter import SqliterDB

if TYPE_CHECKING:
    from collections.abc import Generator


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

        create_id: bool = False
        primary_key: str = "slug"
        table_name: str = "test_table"


class PersonModel(BaseDBModel):
    """Model to test advanced filters."""

    name: Optional[str]
    age: Optional[int]

    class Meta:
        """Configuration for the model."""

        create_id = False
        table_name = "person_table"
        primary_key = "name"


@pytest.fixture
def db_mock() -> SqliterDB:
    """Fixture to create a SqliterDB class with an in-memory SQLite database."""
    db = SqliterDB(":memory:", auto_commit=True)
    db.create_table(ExampleModel)
    return db


@pytest.fixture
def db_mock_adv() -> SqliterDB:
    """Fixture to create a SqliterDB class with an in-memory SQLite database."""
    db = SqliterDB(":memory:", auto_commit=True)
    db.create_table(PersonModel)

    db.insert(PersonModel(name="Alice", age=25))
    db.insert(PersonModel(name="Bob", age=30))
    db.insert(PersonModel(name="Charlie", age=35))

    return db
