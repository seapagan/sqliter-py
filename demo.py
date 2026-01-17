"""Demonstration script showcasing basic SQLiter functionality.

This script provides a practical example of using SQLiter in a
simple application scenario. It demonstrates setting up models,
establishing a database connection, and performing various database
operations including inserts, queries, and updates. This serves as
both a functional test and a usage guide for the SQLiter library.
"""

from __future__ import annotations

import logging
import time
from typing import Annotated, Optional

from sqliter import SqliterDB
from sqliter.exceptions import ForeignKeyConstraintError, RecordInsertionError
from sqliter.model import BaseDBModel, ForeignKey, unique


# User model inheriting from the 'BaseDBModel' class
class UserModel(BaseDBModel):
    """This subclass represents a User model for the database."""

    slug: str
    name: str
    content: Optional[str]
    admin: bool = False
    list_of_str: list[str]
    a_set: set[str]

    class Meta:
        """Override the table name for the UserModel."""

        table_name: str = "users"  # Explicitly define the table name


# Account model demonstrating unique constraint
class AccountModel(BaseDBModel):
    """Model demonstrating unique constraint on email field."""

    username: str
    email: Annotated[str, unique()]  # Email must be unique

    class Meta:
        """Override the table name for the AccountModel."""

        table_name: str = "accounts"


# Models demonstrating foreign key relationships
class Author(BaseDBModel):
    """Author model for FK demonstration."""

    name: str
    email: str


class Book(BaseDBModel):
    """Book model with FK to Author - demonstrates CASCADE delete."""

    title: str
    author_id: int = ForeignKey(Author, on_delete="CASCADE")


def main() -> None:  # noqa: PLR0915
    """Simple example to demonstrate the usage of the 'sqliter' package."""
    # set up logging
    logging.basicConfig(
        level=logging.DEBUG, format="%(levelname)-8s%(message)s"
    )
    logger = logging.getLogger(__name__)

    db = SqliterDB(
        "demo.db", memory=False, auto_commit=True, debug=True, reset=True
    )
    with db:
        logger.info("=== Creating and inserting users ===")
        db.create_table(UserModel)  # Create the users table
        user1 = UserModel(
            slug="jdoe",
            name="John Doe",
            content="This is information about John Doe.",
            admin=True,
            list_of_str=["a", "b", "c"],
            a_set={"x", "y", "z"},
        )
        user2 = UserModel(
            slug="jdoe2",
            name="Jane Doe",
            content="This is information about Jane Doe.",
            list_of_str=["x", "y", "z"],
            a_set={"linux", "mac", "windows"},
        )
        user3 = UserModel(
            slug="jb",
            name="Yogie Bear",
            content=None,
            list_of_str=[],
            a_set={"apple", "banana", "cherry"},
        )
        try:
            db.insert(user1)
            user2_instance = db.insert(user2)
            db.insert(user3)
        except RecordInsertionError as exc:
            logger.error(exc)  # noqa: TRY400

        logger.info("=== Querying users ===")
        # Example queries
        users = db.select(UserModel).filter(name="John Doe").fetch_all()
        logger.info(users)

        all_users = db.select(UserModel).fetch_all()
        logger.info(all_users)

        all_reversed = (
            db.select(UserModel).order("name", reverse=True).fetch_all()
        )
        logger.info(all_reversed)

        logger.info("=== Fetching specific user ===")
        if user2_instance is None:
            logger.error("User2 ID not found.")
        else:
            fetched_user = db.get(UserModel, user2_instance.pk)
            logger.info("Fetched (%s)", fetched_user)

        logger.info("=== Counting users ===")
        count = db.select(UserModel).count()
        logger.info("Total Users: %s", count)

        # Demonstrate unique constraint
        logger.info("=== Demonstrating unique constraint ===")
        db.create_table(AccountModel)

        # Insert first account - should succeed
        account1 = AccountModel(username="alice", email="alice@example.com")
        db.insert(account1)
        logger.info("✓ Inserted account with unique email: alice@example.com")

        # Insert second account with different email - should succeed
        account2 = AccountModel(username="bob", email="bob@example.com")
        db.insert(account2)
        logger.info("✓ Inserted account with unique email: bob@example.com")

        # Try to insert account with duplicate email - should fail
        try:
            account3 = AccountModel(
                username="charlie", email="alice@example.com"
            )
            db.insert(account3)
            logger.error("✗ Should have failed - duplicate email!")
        except RecordInsertionError as exc:
            logger.info("✓ Correctly prevented duplicate email: %s", exc)

    # Demonstrate foreign key relationships
    logger.info("=== Demonstrating foreign keys ===")
    fk_db = SqliterDB("demo.db", debug=True)
    with fk_db:
        # Create tables (parent table must be created first)
        fk_db.create_table(Author, force=True)
        fk_db.create_table(Book, force=True)

        # Insert authors
        author1 = fk_db.insert(
            Author(name="Jane Austen", email="jane@example.com")
        )
        author2 = fk_db.insert(
            Author(name="Mark Twain", email="mark@example.com")
        )
        logger.info("Inserted authors: %s, %s", author1.name, author2.name)

        # Insert books with FK references
        book1 = fk_db.insert(
            Book(title="Pride and Prejudice", author_id=author1.pk)
        )
        book2 = fk_db.insert(Book(title="Emma", author_id=author1.pk))
        book3 = fk_db.insert(Book(title="Tom Sawyer", author_id=author2.pk))
        logger.info(
            "Inserted books: %s, %s, %s", book1.title, book2.title, book3.title
        )

        # Query books by author
        jane_books = fk_db.select(Book).filter(author_id=author1.pk).fetch_all()
        logger.info("Books by Jane Austen: %s", [b.title for b in jane_books])

        # Try to insert book with invalid FK - should fail
        try:
            fk_db.insert(Book(title="Ghost Book", author_id=999))
            logger.error("Should have failed - invalid FK!")
        except ForeignKeyConstraintError as exc:
            logger.info("Correctly prevented invalid FK: %s", exc)

        # Demonstrate CASCADE delete
        logger.info("Deleting Jane Austen (CASCADE should delete her books)...")
        books_before = fk_db.select(Book).count()
        fk_db.delete(Author, str(author1.pk))
        books_after = fk_db.select(Book).count()
        logger.info(
            "Books before: %d, after: %d (CASCADE deleted %d)",
            books_before,
            books_after,
            books_before - books_after,
        )

    logger.info("=== Demonstrating caching ===")
    # Create a new connection with caching enabled
    cached_db = SqliterDB("demo.db", cache_enabled=True, debug=True)
    try:
        # Cache miss - hits database
        start = time.perf_counter()
        _ = cached_db.select(UserModel).fetch_all()
        miss_time = time.perf_counter() - start

        # Cache hit - from cache
        start = time.perf_counter()
        _ = cached_db.select(UserModel).fetch_all()
        hit_time = time.perf_counter() - start

        logger.info("Cache miss: %.3fms (query executed)", miss_time * 1000)
        logger.info("Cache hit:  %.3fms (from cache)", hit_time * 1000)
        if hit_time > 0:
            speedup = miss_time / hit_time
            logger.info("Speedup:   %.1fx faster", speedup)

        # Show cache statistics
        stats = cached_db.get_cache_stats()
        logger.info("Cache stats: %s", stats)

        # Demonstrate cache invalidation
        logger.info("=== Demonstrating cache invalidation ===")
        # Insert new user using the same connection - this invalidates the cache
        new_user = UserModel(
            slug="test",
            name="Test User",
            content="Testing cache invalidation",
            list_of_str=[],
            a_set=set(),
        )
        cached_db.insert(new_user)

        # This query should hit the database again (cache was invalidated)
        start = time.perf_counter()
        _ = cached_db.select(UserModel).fetch_all()
        post_invalidation_time = time.perf_counter() - start
        logger.info("Query after write: %.3fms", post_invalidation_time * 1000)

        # Final cache stats
        stats = cached_db.get_cache_stats()
        logger.info("Final cache stats: %s", stats)
    finally:
        cached_db.close()


if __name__ == "__main__":
    main()
