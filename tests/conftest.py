"""Configuration for pytest."""

import pytest
from sqliter.model import BaseDBModel
from sqliter.sqliter import SqliterDB


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

    name: str
    age: int

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
    return db
