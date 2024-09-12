"""Test class for the database model and query builder."""

from __future__ import annotations

import logging

from sqliter import SqliterDB
from sqliter.exceptions import RecordInsertionError
from sqliter.model import BaseDBModel


# License model inheriting from the 'BaseDBModel' class
class LicenseModel(BaseDBModel):
    """This subclass represents a license model for the database."""

    slug: str
    name: str
    content: str

    class Meta:
        """Override the default options for the LicenseModel."""

        create_id: bool = False  # Disable auto-increment ID
        primary_key: str = "slug"  # Use 'slug' as the primary key
        table_name: str = "licenses"  # Explicitly define the table name


def main() -> None:
    """Simple example to demonstrate the usage of the 'sqliter' package."""
    db = SqliterDB("demo.db", auto_commit=True)
    with db:
        db.create_table(LicenseModel)  # Create the licenses table
        license1 = LicenseModel(
            slug="mit",
            name="MIT License",
            content="This is the MIT license content.",
        )
        license2 = LicenseModel(
            slug="gpl",
            name="GPL License",
            content="This is the GPL license content.",
        )
        try:
            db.insert(license1)
            db.insert(license2)
        except RecordInsertionError as exc:
            logging.error(exc)  # noqa: TRY400

        # set up logging
        logging.basicConfig(
            level=logging.INFO, format="%(levelname)s:  %(message)s"
        )

        # Example queries
        licenses = (
            db.select(LicenseModel).filter(name="MIT License").fetch_all()
        )
        logging.info(licenses)

        all_licenses = db.select(LicenseModel).fetch_all()
        logging.info(all_licenses)

        fetched_license = db.get(LicenseModel, "mit")
        logging.info(fetched_license)

        count = db.select(LicenseModel).count()
        logging.info("Total licenses: %s", count)


if __name__ == "__main__":
    main()
