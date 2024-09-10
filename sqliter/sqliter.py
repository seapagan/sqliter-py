"""This is the main module for the sqliter package."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING, Optional

from typing_extensions import Self

from sqliter.exceptions import DatabaseConnectionError
from sqliter.query.query import QueryBuilder

if TYPE_CHECKING:  # pragma: no cover
    from types import TracebackType

    from sqliter.model.model import BaseDBModel


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
            try:
                self.conn = sqlite3.connect(self.db_filename)
            except sqlite3.Error as exc:
                raise DatabaseConnectionError(self.db_filename) from exc
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
                    {primary_key} INTEGER PRIMARY KEY AUTOINCREMENT,
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
            self._maybe_commit(self.conn)
            self.conn.close()
            self.conn = None
