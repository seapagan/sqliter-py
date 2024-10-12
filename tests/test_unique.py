"""Test the Unique constraint."""

from typing import Annotated

import pytest

from sqliter import SqliterDB
from sqliter.exceptions import SqliterError
from sqliter.model import BaseDBModel
from sqliter.model.unique import Unique


class TestUnique:
    """Test suite for the Unique constraint."""

    def test_unique_constraint(self) -> None:
        """Test that the Unique constraint is properly applied."""

        class User(BaseDBModel):
            name: str
            email: Annotated[str, Unique()]

        db = SqliterDB(":memory:")
        db.create_table(User)

        # Insert a user successfully
        user1 = User(name="Alice", email="alice@example.com")
        db.insert(user1)

        # Attempt to insert a user with the same email
        user2 = User(name="Bob", email="alice@example.com")

        with pytest.raises(SqliterError) as excinfo:
            db.insert(user2)

        assert "UNIQUE constraint failed: users.email" in str(excinfo.value)

        # Verify that only one user was inserted
        users = db.select(User).fetch_all()
        assert len(users) == 1
        assert users[0].name == "Alice"
        assert users[0].email == "alice@example.com"

        # Insert a user with a different email successfully
        user3 = User(name="Charlie", email="charlie@example.com")
        db.insert(user3)

        # Verify that two users are now in the database
        users = db.select(User).fetch_all()
        assert len(users) == 2
        assert {u.name for u in users} == {"Alice", "Charlie"}
        assert {u.email for u in users} == {
            "alice@example.com",
            "charlie@example.com",
        }
