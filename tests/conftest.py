"""Configuration for pytest."""

import pytest
from sqliter.sqliter import SqliterDB

from tests.test_sqliter import ExampleModel


@pytest.fixture
def db_mock(mocker) -> SqliterDB:
    """Fixture to mock the SqliterDB class with an in-memory SQLite database."""
    db = SqliterDB(":memory:", auto_commit=True)
    db.create_table(ExampleModel)
    return db
