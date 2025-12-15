"""Test the Unique constraint."""

from typing import Annotated, Union

import pytest

from sqliter import SqliterDB
from sqliter.exceptions import RecordInsertionError, RecordUpdateError
from sqliter.model import BaseDBModel, unique


class TestUnique:
    """Test suite for the Unique constraint."""

    def test_unique_constraint_single_field(self) -> None:
        """Test that the Unique constraint is applied to a single field."""

        class User(BaseDBModel):
            name: str
            email: Annotated[str, unique()]

        db = SqliterDB(":memory:")
        db.create_table(User)

        # Insert a user successfully
        user1 = User(name="Alice", email="alice@example.com")
        db.insert(user1)

        # Attempt to insert a user with the same email
        user2 = User(name="Bob", email="alice@example.com")

        with pytest.raises(RecordInsertionError) as excinfo:
            db.insert(user2)

        assert "UNIQUE constraint failed: users.email" in str(excinfo.value)

        # Verify that only one user was inserted
        users = db.select(User).fetch_all()
        assert len(users) == 1
        assert users[0].name == "Alice"
        assert users[0].email == "alice@example.com"

    def test_unique_constraint_multi_column(self) -> None:
        """Test the Unique constraint on multiple fields."""

        class User(BaseDBModel):
            name: Annotated[str, unique()]
            email: str

        db = SqliterDB(":memory:")
        db.create_table(User)

        # Insert a user successfully
        user1 = User(name="Alice", email="alice@example.com")
        db.insert(user1)

        # Insert another user with the same email but different name (no
        # conflict)
        user2 = User(name="Bob", email="alice@example.com")
        db.insert(user2)

        # Attempt to insert a user with the same name (should fail)
        user3 = User(name="Alice", email="charlie@example.com")

        with pytest.raises(RecordInsertionError) as excinfo:
            db.insert(user3)

        assert "UNIQUE constraint failed: users.name" in str(excinfo.value)

    def test_unique_constraint_sql_generation(self, mocker) -> None:
        """Test that the correct SQL for the Unique constraint is generated."""

        class User(BaseDBModel):
            name: Annotated[str, unique()]
            email: str

        # Mock the cursor to capture executed SQL
        mock_cursor = mocker.MagicMock()
        mocker.patch.object(
            SqliterDB, "connect"
        ).return_value.__enter__.return_value.cursor.return_value = mock_cursor

        db = SqliterDB(":memory:")
        db.create_table(User)

        # Capture the generated SQL statement for table creation
        sql = mock_cursor.execute.call_args[0][0]

        # Remove the primary key part from the SQL for easier assertion
        sql_without_pk = sql.replace(
            '"pk" INTEGER PRIMARY KEY AUTOINCREMENT, ', ""
        )

        # Assert that the correct UNIQUE syntax is present for the 'name' field
        assert "CREATE TABLE" in sql
        assert "name TEXT UNIQUE" in sql_without_pk  # Correct SQLite syntax

    def test_unique_constraint_across_records(self) -> None:
        """Test that unique constraints hold across multiple records."""

        class User(BaseDBModel):
            name: str
            email: Annotated[str, unique()]

        db = SqliterDB(":memory:")
        db.create_table(User)

        # Insert multiple users with unique emails
        user1 = User(name="Alice", email="alice@example.com")
        user2 = User(name="Bob", email="bob@example.com")
        db.insert(user1)
        db.insert(user2)

        # Insert another user with a duplicate email (should fail)
        user3 = User(name="Charlie", email="bob@example.com")
        with pytest.raises(RecordInsertionError) as excinfo:
            db.insert(user3)

        assert "UNIQUE constraint failed: users.email" in str(excinfo.value)

        # Verify that only two users are inserted
        users = db.select(User).fetch_all()
        assert len(users) == 2

    def test_unique_constraint_with_null(self) -> None:
        """Test that the Unique constraint allows null values if applicable."""

        class User(BaseDBModel):
            name: str
            email: Annotated[Union[str, None], unique()]

        db = SqliterDB(":memory:")
        db.create_table(User)

        # Insert a user with a null email
        user1 = User(name="Alice", email=None)
        db.insert(user1)

        # Insert another user with a null email (no conflict)
        user2 = User(name="Bob", email=None)
        db.insert(user2)

        # Verify that both users were inserted successfully
        users = db.select(User).fetch_all()
        assert len(users) == 2
        assert {u.name for u in users} == {"Alice", "Bob"}
        assert {u.email for u in users} == {None}

    def test_unique_constraint_with_different_values(self) -> None:
        """Test that Unique constraint allows different unique values."""

        class User(BaseDBModel):
            name: str
            email: Annotated[str, unique()]

        db = SqliterDB(":memory:")
        db.create_table(User)

        # Insert a user with a unique email
        user1 = User(name="Alice", email="alice@example.com")
        db.insert(user1)

        # Insert another user with a different email (no conflict)
        user2 = User(name="Bob", email="bob@example.com")
        db.insert(user2)

        # Verify that both users were inserted successfully
        users = db.select(User).fetch_all()
        assert len(users) == 2
        assert {u.email for u in users} == {
            "alice@example.com",
            "bob@example.com",
        }

    def test_unique_constraint_multiple_fields(self) -> None:
        """Test that multiple fields with unique constraints are respected."""

        class User(BaseDBModel):
            username: Annotated[str, unique()]
            email: Annotated[str, unique()]

        db = SqliterDB(":memory:")
        db.create_table(User)

        # Insert a user successfully
        user1 = User(username="Alice", email="alice@example.com")
        db.insert(user1)

        # Attempt to insert a user with the same username (should fail)
        user2 = User(username="Alice", email="bob@example.com")
        with pytest.raises(RecordInsertionError):
            db.insert(user2)

        # Attempt to insert a user with the same email (should fail)
        user3 = User(username="Bob", email="alice@example.com")
        with pytest.raises(RecordInsertionError):
            db.insert(user3)

    def test_unique_constraint_case_sensitivity(self) -> None:
        """Test that the unique constraint is case-sensitive for text fields."""

        class User(BaseDBModel):
            email: Annotated[str, unique()]

        db = SqliterDB(":memory:")
        db.create_table(User)

        # Insert user with lowercase email
        user1 = User(email="alice@example.com")
        db.insert(user1)

        # Attempt to insert user with same email but different case (should
        # pass)
        user2 = User(email="ALICE@example.com")
        db.insert(user2)

        users = db.select(User).fetch_all()
        assert len(users) == 2

    def test_unique_constraint_empty_string_vs_null(self) -> None:
        """Test SQLite diffs between empty strings & null for unique."""

        class User(BaseDBModel):
            email: Annotated[Union[str, None], unique()]

        db = SqliterDB(":memory:")
        db.create_table(User)

        # Insert user with a NULL email
        user1 = User(email=None)
        db.insert(user1)

        # Insert user with an empty string as email (should pass)
        user2 = User(email="")
        db.insert(user2)

        # Verify both users were inserted
        users = db.select(User).fetch_all()
        assert len(users) == 2

    def test_unique_constraint_on_update(self) -> None:
        """Test modifying a record to violate the unique constraint fails."""

        class User(BaseDBModel):
            email: Annotated[str, unique()]
            name: str

        db = SqliterDB(":memory:")
        db.create_table(User)

        # Insert two users
        user1 = User(name="Alice", email="alice@example.com")
        user2 = User(name="Bob", email="bob@example.com")
        db.insert(user1)
        user2 = db.insert(user2)

        # Attempt to update user2's email to match user1's email (should fail)
        user2.email = "alice@example.com"
        with pytest.raises(RecordUpdateError):
            db.update(user2)
