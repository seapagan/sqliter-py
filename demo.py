"""Test class for the database model and query builder."""

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

        create_id: bool = False  # Disable auto-increment ID
        primary_key: str = "slug"  # Use 'slug' as the primary key
        table_name: str = "users"  # Explicitly define the table name


def main() -> None:
    """Simple example to demonstrate the usage of the 'sqliter' package."""
    db = SqliterDB("./demo-db/demo.db", auto_commit=True)
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

        # set up logging
        logging.basicConfig(
            level=logging.INFO, format="%(levelname)s:  %(message)s"
        )

        # Example queries
        users = db.select(UserModel).filter(name="John Doe").fetch_all()
        logging.info(users)

        all_users = db.select(UserModel).fetch_all()
        logging.info(all_users)

        fetched_user = db.get(UserModel, "jdoe2")
        logging.info(fetched_user)

        count = db.select(UserModel).count()
        logging.info("Total Users: %s", count)


if __name__ == "__main__":
    main()
