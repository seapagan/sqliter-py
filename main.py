"""Test class for the database model and query builder."""

from __future__ import annotations

import logging
import sqlite3
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel
from typing_extensions import Self

if TYPE_CHECKING:
    from types import TracebackType


# Custom Base Model for all database models
class BaseDBModel(BaseModel):
    """Custom base model for database models."""

    class Meta:
        """Configure the base model with default options."""

        create_id: bool = True  # Whether to create an auto-increment ID
        primary_key: str = "id"  # Default primary key field
        table_name: Optional[str] = (
            None  # Table name, defaults to class name if not set
        )

    @classmethod
    def get_table_name(cls) -> str:
        """Get the table name from the Meta, or default to the classname."""
        table_name: str | None = getattr(cls.Meta, "table_name", None)
        if table_name is not None:
            return table_name
        return cls.__name__.lower()  # Default to class name in lowercase

    @classmethod
    def get_primary_key(cls) -> str:
        """Get the primary key from the Meta class or default to 'id'."""
        return getattr(cls.Meta, "primary_key", "id")

    @classmethod
    def should_create_id(cls) -> bool:
        """Check whether the model should create an auto-increment ID."""
        return getattr(cls.Meta, "create_id", True)


# License model inheriting from the custom base model
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


# QueryBuilder class for chained filtering and fetching
class QueryBuilder:
    """Functions to build and execute queries for a given model."""

    def __init__(self, db: SqliterDB, model_class: type[BaseDBModel]) -> None:
        """Initialize the query builder with the database, model class, etc."""
        self.db = db
        self.model_class = model_class
        self.table_name = model_class.get_table_name()  # Use model_class method
        self.filters: list[tuple[str, Any]] = []

    def filter(self, **conditions: str | float | None) -> Self:
        """Add filter conditions to the query."""
        for field, value in conditions.items():
            self.filters.append((field, value))
        return self

    def _execute_query(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None,
        *,
        fetch_one: bool = False,
    ) -> list[tuple[Any, ...]] | Optional[tuple[Any, ...]]:
        """Helper function to execute the query with filters."""
        fields = ", ".join(self.model_class.model_fields)
        where_clause = " AND ".join(
            [f"{field} = ?" for field, _ in self.filters]
        )
        sql = f"SELECT {fields} FROM {self.table_name}"  # noqa: S608

        if self.filters:
            sql += f" WHERE {where_clause}"

        if order_by:
            sql += f" ORDER BY {order_by}"

        if limit is not None:
            sql += f" LIMIT {limit}"

        if offset is not None:
            sql += f" OFFSET {offset}"

        values = [value for _, value in self.filters]

        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, values)
            return cursor.fetchall() if not fetch_one else cursor.fetchone()

    def fetch_all(self) -> list[BaseDBModel]:
        """Fetch all results matching the filters."""
        results = self._execute_query()

        if results is None:
            return []

        return [
            self.model_class(
                **{
                    field: row[idx]
                    for idx, field in enumerate(self.model_class.model_fields)
                }
            )
            for row in results
        ]

    def fetch_one(self) -> BaseDBModel | None:
        """Fetch exactly one result."""
        result = self._execute_query(fetch_one=True)
        if not result:
            return None
        return self.model_class(
            **{
                field: result[idx]
                for idx, field in enumerate(self.model_class.model_fields)
            }
        )

    def fetch_first(self) -> BaseDBModel | None:
        """Fetch the first result of the query."""
        result = self._execute_query(limit=1)
        if not result:
            return None
        return self.model_class(
            **{
                field: result[0][idx]
                for idx, field in enumerate(self.model_class.model_fields)
            }
        )

    def fetch_last(self) -> BaseDBModel | None:
        """Fetch the last result of the query (based on the primary key)."""
        primary_key = self.model_class.get_primary_key()
        result = self._execute_query(limit=1, order_by=f"{primary_key} DESC")
        if not result:
            return None
        return self.model_class(
            **{
                field: result[0][idx]
                for idx, field in enumerate(self.model_class.model_fields)
            }
        )

    def count(self) -> int:
        """Return the count of records matching the filters."""
        where_clause = " AND ".join(
            [f"{field} = ?" for field, _ in self.filters]
        )
        sql = f"SELECT COUNT(*) FROM {self.table_name}"  # noqa: S608

        if self.filters:
            sql += f" WHERE {where_clause}"

        values = [value for _, value in self.filters]

        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, values)
            result = cursor.fetchone()

        return int(result[0]) if result else 0

    def exists(self) -> bool:
        """Return True if any record matches the filters."""
        return self.count() > 0


# LicenseDB class to manage database interactions
class SqliterDB:
    """Class to manage SQLite database interactions."""

    def __init__(self, db_filename: str, *, auto_commit: bool = False) -> None:
        """Initialize the class and options."""
        self.db_filename = db_filename
        self.auto_commit = auto_commit
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """Create or return a connection to the SQLite database."""
        if not self.conn:
            self.conn = sqlite3.connect(self.db_filename)
        return self.conn

    def create_table(self, model_class: type[BaseDBModel]) -> None:
        """Create a table based on the Pydantic model."""
        table_name = model_class.get_table_name()
        primary_key = model_class.get_primary_key()
        create_id = model_class.should_create_id()

        fields = ", ".join(
            f"{field_name} TEXT" for field_name in model_class.model_fields
        )

        if create_id:
            create_table_sql = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    {fields}
                )
            """
        else:
            create_table_sql = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    {fields},
                    PRIMARY KEY ({primary_key})
                )
            """

        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(create_table_sql)
            conn.commit()

    def _maybe_commit(self, conn: sqlite3.Connection) -> None:
        """Commit changes if auto_commit is True."""
        if self.auto_commit:
            conn.commit()

    def insert(self, model_instance: BaseDBModel) -> None:
        """Insert a new record into the table defined by the Pydantic model."""
        model_class = type(model_instance)
        table_name = model_class.get_table_name()

        fields = ", ".join(model_class.model_fields)
        placeholders = ", ".join(["?"] * len(model_class.model_fields))
        values = tuple(
            getattr(model_instance, field) for field in model_class.model_fields
        )

        insert_sql = f"""
        INSERT OR REPLACE INTO {table_name} ({fields})
        VALUES ({placeholders})
    """  # noqa: S608

        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(insert_sql, values)
            self._maybe_commit(conn)

    def get(
        self, model_class: type[BaseDBModel], primary_key_value: str
    ) -> BaseDBModel | None:
        """Retrieve a record by its PK and return a Pydantic instance."""
        table_name = model_class.get_table_name()
        primary_key = model_class.get_primary_key()

        fields = ", ".join(model_class.model_fields)

        select_sql = f"""
            SELECT {fields} FROM {table_name} WHERE {primary_key} = ?
        """  # noqa: S608

        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(select_sql, (primary_key_value,))
            result = cursor.fetchone()

        if result:
            result_dict = {
                field: result[idx]
                for idx, field in enumerate(model_class.model_fields)
            }
            return model_class(**result_dict)
        return None

    def update(self, model_instance: BaseDBModel) -> None:
        """Update an existing record using the Pydantic model."""
        model_class = type(model_instance)
        table_name = model_class.get_table_name()
        primary_key = model_class.get_primary_key()

        fields = ", ".join(
            f"{field} = ?"
            for field in model_class.model_fields
            if field != primary_key
        )
        values = tuple(
            getattr(model_instance, field)
            for field in model_class.model_fields
            if field != primary_key
        )
        primary_key_value = getattr(model_instance, primary_key)

        update_sql = f"""
            UPDATE {table_name} SET {fields} WHERE {primary_key} = ?
        """  # noqa: S608

        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(update_sql, (*values, primary_key_value))
            self._maybe_commit(conn)

    def delete(
        self, model_class: type[BaseDBModel], primary_key_value: str
    ) -> None:
        """Delete a record by its primary key."""
        table_name = model_class.get_table_name()
        primary_key = model_class.get_primary_key()

        delete_sql = f"""
            DELETE FROM {table_name} WHERE {primary_key} = ?
        """  # noqa: S608

        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(delete_sql, (primary_key_value,))
            self._maybe_commit(conn)

    def select(self, model_class: type[BaseDBModel]) -> QueryBuilder:
        """Start a query for the given model."""
        return QueryBuilder(self, model_class)

    # --- Context manager methods ---
    def __enter__(self) -> Self:
        """Enter the runtime context for the 'with' statement."""
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Exit the runtime context and close the connection."""
        if self.conn:
            if not self.auto_commit:
                self.conn.commit()
            self.conn.close()
            self.conn = None


# Example usage
db = SqliterDB("lice.db", auto_commit=True)
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
    db.insert(license1)
    db.insert(license2)

    # set up logging
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s:  %(message)s"
    )

    # Example queries
    licenses = db.select(LicenseModel).filter(name="MIT License").fetch_all()
    logging.info(licenses)

    all_licenses = db.select(LicenseModel).fetch_all()
    logging.info(all_licenses)

    fetched_license = db.get(LicenseModel, "mit")
    logging.info(fetched_license)

    count = db.select(LicenseModel).count()
    logging.info("Total licenses: %s", count)
