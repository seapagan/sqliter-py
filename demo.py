"""Demonstration script showcasing basic SQLiter functionality.

This script provides a practical example of using SQLiter in a
simple application scenario. It demonstrates setting up models,
establishing a database connection, and performing various database
operations including inserts, queries, and updates. This serves as
both a functional test and a usage guide for the SQLiter library.
"""

from __future__ import annotations

import logging
from typing import Optional

from sqliter import SqliterDB
from sqliter.exceptions import RecordInsertionError
from sqliter.model import BaseDBModel


# User model inheriting from the 'BaseDBModel' class
class UserModel(BaseDBModel):
    """This subclass represents a User model for the database."""

    slug: str
    name: str
    content: Optional[str]
    admin: bool = False

    class Meta:
        """Override the default options for the UserModel."""

        create_pk: bool = False  # Disable auto-increment ID
        primary_key: str = "slug"  # Use 'slug' as the primary key
        table_name: str = "users"  # Explicitly define the table name


def main() -> None:
    """Simple example to demonstrate the usage of the 'sqliter' package."""
    # set up logging
    logging.basicConfig(
        level=logging.DEBUG, format="%(levelname)-8s%(message)s"
    )

    db = SqliterDB(memory=True, auto_commit=True, debug=True)
    with db:
        db.create_table(UserModel)  # Create the users table
        user1 = UserModel(
            slug="jdoe",
            name="John Doe",
            content="This is information about John Doe.",
            admin=True,
        )
        user2 = UserModel(
            slug="jdoe2",
            name="Jane Doe",
            content="This is information about Jane Doe.",
        )
        user3 = UserModel(
            slug="jb",
            name="Yogie Bear",
            content=None,
        )
        try:
            db.insert(user1)
            db.insert(user2)
            db.insert(user3)
        except RecordInsertionError as exc:
            logging.error(exc)  # noqa: TRY400

        # Example queries
        users = db.select(UserModel).filter(name="John Doe").fetch_all()
        logging.info(users)

        all_users = db.select(UserModel).fetch_all()
        logging.info(all_users)

        all_reversed = (
            db.select(UserModel).order("name", reverse=True).fetch_all()
        )
        logging.info(all_reversed)

        fetched_user = db.get(UserModel, "jdoe2")
        logging.info(fetched_user)

        count = db.select(UserModel).count()
        logging.info("Total Users: %s", count)


if __name__ == "__main__":
    main()
