"""This is the main module for the sqliter package."""

from __future__ import annotations

import logging
import sqlite3
from typing import TYPE_CHECKING, Any, Optional

from typing_extensions import Self

from sqliter.exceptions import (
    DatabaseConnectionError,
    RecordDeletionError,
    RecordFetchError,
    RecordInsertionError,
    RecordNotFoundError,
    RecordUpdateError,
    TableCreationError,
)
from sqliter.helpers import infer_sqlite_type
from sqliter.query.query import QueryBuilder

if TYPE_CHECKING:  # pragma: no cover
    from types import TracebackType

    from sqliter.model.model import BaseDBModel


class SqliterDB:
    """Class to manage SQLite database interactions."""

    def __init__(
        self,
        db_filename: Optional[str] = None,
        *,
        memory: bool = False,
        auto_commit: bool = True,
        debug: bool = False,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Initialize the class and options."""
        if memory:
            self.db_filename = ":memory:"
        elif db_filename:
            self.db_filename = db_filename
        else:
            err = (
                "Database name must be provided if not using an in-memory "
                "database."
            )
            raise ValueError(err)
        self.auto_commit = auto_commit
        self.debug = debug
        self.logger = logger
        self.conn: Optional[sqlite3.Connection] = None

        if self.debug:
            self._setup_logger()

    def _setup_logger(self) -> None:
        """Sets up the logger for SQL debugging.

        This uses any existing logger if it has handlers, otherwise it creates a
        new logger with a custom handler and formatter.
        """
        # Check if the root logger is already configured
        root_logger = logging.getLogger()

        if root_logger.hasHandlers():
            # If the root logger has handlers, use it without modifying the root
            # configuration
            self.logger = root_logger.getChild("sqliter")
        else:
            # If no root logger is configured, set up a new logger specific to
            # SqliterDB
            self.logger = logging.getLogger("sqliter")

            handler = logging.StreamHandler()  # Output to console
            formatter = logging.Formatter(
                "%(levelname)-8s%(message)s"
            )  # Custom format
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

            self.logger.setLevel(logging.DEBUG)
            self.logger.propagate = False

    def _log_sql(self, sql: str, values: list[Any]) -> None:
        """Logs the SQL query and values if debugging is enabled."""
        if self.debug and self.logger:
            formatted_sql = sql
            for value in values:
                if isinstance(value, str):
                    formatted_sql = formatted_sql.replace("?", f"'{value}'", 1)
                else:
                    formatted_sql = formatted_sql.replace("?", str(value), 1)

            self.logger.debug("Executing SQL: %s", formatted_sql)

    def connect(self) -> sqlite3.Connection:
        """Create or return a connection to the SQLite database."""
        if not self.conn:
            try:
                self.conn = sqlite3.connect(self.db_filename)
            except sqlite3.Error as exc:
                raise DatabaseConnectionError(self.db_filename) from exc
        return self.conn

    def close(self) -> None:
        """Close the connection to the SQLite database."""
        if self.conn:
            self._maybe_commit()
            self.conn.close()
            self.conn = None

    def commit(self) -> None:
        """Commit any pending transactions."""
        if self.conn:
            self.conn.commit()

    def create_table(self, model_class: type[BaseDBModel]) -> None:
        """Create a table based on the Pydantic model."""
        table_name = model_class.get_table_name()
        primary_key = model_class.get_primary_key()
        create_pk = model_class.should_create_pk()

        fields = []

        # Always add the primary key field first
        if create_pk:
            fields.append(f"{primary_key} INTEGER PRIMARY KEY AUTOINCREMENT")
        else:
            field_info = model_class.model_fields.get(primary_key)
            if field_info is not None:
                sqlite_type = infer_sqlite_type(field_info.annotation)
                fields.append(f"{primary_key} {sqlite_type} PRIMARY KEY")
            else:
                err = (
                    f"Primary key field '{primary_key}' not found in model "
                    "fields."
                )
                raise ValueError(err)

        # Add remaining fields
        for field_name, field_info in model_class.model_fields.items():
            if field_name != primary_key:
                sqlite_type = infer_sqlite_type(field_info.annotation)
                fields.append(f"{field_name} {sqlite_type}")

        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {", ".join(fields)}
        )
        """

        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(create_table_sql)
                conn.commit()
        except sqlite3.Error as exc:
            raise TableCreationError(table_name) from exc

    def _maybe_commit(self) -> None:
        """Commit changes if auto_commit is True."""
        if self.auto_commit and self.conn:
            self.conn.commit()

    def insert(self, model_instance: BaseDBModel) -> None:
        """Insert a new record into the table defined by the Pydantic model."""
        model_class = type(model_instance)
        table_name = model_class.get_table_name()

        data = model_instance.model_dump()
        fields = ", ".join(data.keys())
        placeholders = ", ".join(
            ["?" if value is not None else "NULL" for value in data.values()]
        )
        values = tuple(value for value in data.values() if value is not None)

        insert_sql = f"""
        INSERT INTO {table_name} ({fields})
        VALUES ({placeholders})
        """  # noqa: S608

        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(insert_sql, values)
                self._maybe_commit()
        except sqlite3.Error as exc:
            raise RecordInsertionError(table_name) from exc

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

        try:
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
        except sqlite3.Error as exc:
            raise RecordFetchError(table_name) from exc
        else:
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
            UPDATE {table_name}
            SET {fields}
            WHERE {primary_key} = ?
        """  # noqa: S608

        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(update_sql, (*values, primary_key_value))

                # Check if any rows were updated
                if cursor.rowcount == 0:
                    raise RecordNotFoundError(primary_key_value)

                self._maybe_commit()

        except sqlite3.Error as exc:
            raise RecordUpdateError(table_name) from exc

    def delete(
        self, model_class: type[BaseDBModel], primary_key_value: str
    ) -> None:
        """Delete a record by its primary key."""
        table_name = model_class.get_table_name()
        primary_key = model_class.get_primary_key()

        delete_sql = f"""
            DELETE FROM {table_name} WHERE {primary_key} = ?
        """  # noqa: S608

        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(delete_sql, (primary_key_value,))

                if cursor.rowcount == 0:
                    raise RecordNotFoundError(primary_key_value)
                self._maybe_commit()
        except sqlite3.Error as exc:
            raise RecordDeletionError(table_name) from exc

    def select(
        self,
        model_class: type[BaseDBModel],
        fields: Optional[list[str]] = None,
        exclude: Optional[list[str]] = None,
    ) -> QueryBuilder:
        """Start a query for the given model.

        Args:
            model_class: The model class to query.
            fields: Optional list of field names to select. If None, all fields
                are selected.
            exclude: Optional list of field names to exclude from the query
                output.

        Returns:
            QueryBuilder: An instance of QueryBuilder for the given model and
            fields.
        """
        query_builder = QueryBuilder(self, model_class, fields)

        # If exclude is provided, apply the exclude method
        if exclude:
            query_builder.exclude(exclude)

        return query_builder

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
            try:
                if exc_type:
                    # Roll back the transaction if there was an exception
                    self.conn.rollback()
                else:
                    self.conn.commit()
            finally:
                # Close the connection and reset the instance variable
                self.conn.close()
                self.conn = None
