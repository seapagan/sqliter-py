"""Core module for SQLiter, providing the main database interaction class.

This module defines the SqliterDB class, which serves as the primary
interface for all database operations in SQLiter. It handles connection
management, table creation, and CRUD operations, bridging the gap between
Pydantic models and SQLite database interactions.
"""

from __future__ import annotations

import logging
import sqlite3
from typing import TYPE_CHECKING, Any, Optional, TypeVar, Union

from typing_extensions import Self

from sqliter.exceptions import (
    DatabaseConnectionError,
    InvalidIndexError,
    RecordDeletionError,
    RecordFetchError,
    RecordInsertionError,
    RecordNotFoundError,
    RecordUpdateError,
    SqlExecutionError,
    TableCreationError,
    TableDeletionError,
)
from sqliter.helpers import infer_sqlite_type
from sqliter.model.unique import Unique
from sqliter.query.query import QueryBuilder

if TYPE_CHECKING:  # pragma: no cover
    from types import TracebackType

    from sqliter.model.model import BaseDBModel

T = TypeVar("T", bound="BaseDBModel")


class SqliterDB:
    """Main class for interacting with SQLite databases.

    This class provides methods for connecting to a SQLite database,
    creating tables, and performing CRUD operations.

    Arguements:
        db_filename (str): The filename of the SQLite database.
        auto_commit (bool): Whether to automatically commit transactions.
        debug (bool): Whether to enable debug logging.
        logger (Optional[logging.Logger]): Custom logger for debug output.
    """

    def __init__(
        self,
        db_filename: Optional[str] = None,
        *,
        memory: bool = False,
        auto_commit: bool = True,
        debug: bool = False,
        logger: Optional[logging.Logger] = None,
        reset: bool = False,
    ) -> None:
        """Initialize a new SqliterDB instance.

        Args:
            db_filename: The filename of the SQLite database.
            memory: If True, create an in-memory database.
            auto_commit: Whether to automatically commit transactions.
            debug: Whether to enable debug logging.
            logger: Custom logger for debug output.
            reset: Whether to reset the database on initialization. This will
                basically drop all existing tables.

        Raises:
            ValueError: If no filename is provided for a non-memory database.
        """
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
        self.reset = reset

        self._in_transaction = False

        if self.debug:
            self._setup_logger()

        if self.reset:
            self._reset_database()

    def _reset_database(self) -> None:
        """Drop all user-created tables in the database."""
        with self.connect() as conn:
            cursor = conn.cursor()

            # Get all table names, excluding SQLite system tables
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%';"
            )
            tables = cursor.fetchall()

            # Drop each user-created table
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")

            conn.commit()

        if self.debug and self.logger:
            self.logger.debug(
                "Database reset: %s user-created tables dropped.", len(tables)
            )

    def _setup_logger(self) -> None:
        """Set up the logger for debug output.

        This method configures a logger for the SqliterDB instance, either
        using an existing logger or creating a new one specifically for
        SQLiter.
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
        """Log the SQL query and its values if debug mode is enabled.

        The values are inserted into the SQL query string to replace the
        placeholders.

        Args:
            sql: The SQL query string.
            values: The list of values to be inserted into the query.
        """
        if self.debug and self.logger:
            formatted_sql = sql
            for value in values:
                if isinstance(value, str):
                    formatted_sql = formatted_sql.replace("?", f"'{value}'", 1)
                else:
                    formatted_sql = formatted_sql.replace("?", str(value), 1)

            self.logger.debug("Executing SQL: %s", formatted_sql)

    def connect(self) -> sqlite3.Connection:
        """Establish a connection to the SQLite database.

        Returns:
            The SQLite connection object.

        Raises:
            DatabaseConnectionError: If unable to connect to the database.
        """
        if not self.conn:
            try:
                self.conn = sqlite3.connect(self.db_filename)
            except sqlite3.Error as exc:
                raise DatabaseConnectionError(self.db_filename) from exc
        return self.conn

    def close(self) -> None:
        """Close the database connection.

        This method commits any pending changes if auto_commit is True,
        then closes the connection. If the connection is already closed or does
        not exist, this method silently does nothing.
        """
        if self.conn:
            self._maybe_commit()
            self.conn.close()
            self.conn = None

    def commit(self) -> None:
        """Commit the current transaction.

        This method explicitly commits any pending changes to the database.
        """
        if self.conn:
            self.conn.commit()

    def create_table(
        self,
        model_class: type[BaseDBModel],
        *,
        exists_ok: bool = True,
        force: bool = False,
    ) -> None:
        """Create a table in the database based on the given model class.

        Args:
            model_class: The Pydantic model class representing the table.
            exists_ok: If True, do not raise an error if the table already
                exists. Default is True which is the original behavior.
            force: If True, drop the table if it exists before creating.
                Defaults to False.

        Raises:
            TableCreationError: If there's an error creating the table.
            ValueError: If the primary key field is not found in the model.
        """
        table_name = model_class.get_table_name()
        primary_key = model_class.get_primary_key()

        if force:
            drop_table_sql = f"DROP TABLE IF EXISTS {table_name}"
            self._execute_sql(drop_table_sql)

        fields = [f'"{primary_key}" INTEGER PRIMARY KEY AUTOINCREMENT']

        # Add remaining fields
        for field_name, field_info in model_class.model_fields.items():
            if field_name != primary_key:
                sqlite_type = infer_sqlite_type(field_info.annotation)
                unique_constraint = (
                    "UNIQUE" if isinstance(field_info, Unique) else ""
                )
                fields.append(
                    f"{field_name} {sqlite_type} {unique_constraint}".strip()
                )

        create_str = (
            "CREATE TABLE IF NOT EXISTS" if exists_ok else "CREATE TABLE"
        )

        create_table_sql = f"""
        {create_str} {table_name} (
            {", ".join(fields)}
        )
        """

        if self.debug:
            self._log_sql(create_table_sql, [])

        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(create_table_sql)
                conn.commit()
        except sqlite3.Error as exc:
            raise TableCreationError(table_name) from exc

        # Create regular indexes
        if hasattr(model_class.Meta, "indexes"):
            self._create_indexes(
                model_class, model_class.Meta.indexes, unique=False
            )

        # Create unique indexes
        if hasattr(model_class.Meta, "unique_indexes"):
            self._create_indexes(
                model_class, model_class.Meta.unique_indexes, unique=True
            )

    def _create_indexes(
        self,
        model_class: type[BaseDBModel],
        indexes: list[Union[str, tuple[str]]],
        *,
        unique: bool = False,
    ) -> None:
        """Helper method to create regular or unique indexes.

        Args:
            model_class: The model class defining the table.
            indexes: List of fields or tuples of fields to create indexes for.
            unique: If True, creates UNIQUE indexes; otherwise, creates regular
                indexes.

        Raises:
            InvalidIndexError: If any fields specified for indexing do not exist
                in the model.
        """
        valid_fields = set(
            model_class.model_fields.keys()
        )  # Get valid fields from the model

        for index in indexes:
            # Handle multiple fields in tuple form
            fields = list(index) if isinstance(index, tuple) else [index]

            # Check if all fields exist in the model
            invalid_fields = [
                field for field in fields if field not in valid_fields
            ]
            if invalid_fields:
                raise InvalidIndexError(invalid_fields, model_class.__name__)

            # Build the SQL string
            index_name = "_".join(fields)
            index_postfix = "_unique" if unique else ""
            index_type = " UNIQUE " if unique else " "

            create_index_sql = (
                f"CREATE{index_type}INDEX IF NOT EXISTS "
                f"idx_{model_class.get_table_name()}"
                f"_{index_name}{index_postfix} "
                f"ON {model_class.get_table_name()} ({', '.join(fields)})"
            )
            self._execute_sql(create_index_sql)

    def _execute_sql(self, sql: str) -> None:
        """Execute an SQL statement.

        Args:
            sql: The SQL statement to execute.

        Raises:
            SqlExecutionError: If the SQL execution fails.
        """
        if self.debug:
            self._log_sql(sql, [])

        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(sql)
                conn.commit()
        except (sqlite3.Error, sqlite3.Warning) as exc:
            raise SqlExecutionError(sql) from exc

    def drop_table(self, model_class: type[BaseDBModel]) -> None:
        """Drop the table associated with the given model class.

        Args:
            model_class: The model class for which to drop the table.

        Raises:
            TableDeletionError: If there's an error dropping the table.
        """
        table_name = model_class.get_table_name()
        drop_table_sql = f"DROP TABLE IF EXISTS {table_name}"

        if self.debug:
            self._log_sql(drop_table_sql, [])

        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(drop_table_sql)
                self.commit()
        except sqlite3.Error as exc:
            raise TableDeletionError(table_name) from exc

    def _maybe_commit(self) -> None:
        """Commit changes if auto_commit is enabled.

        This method is called after operations that modify the database,
        committing changes only if auto_commit is set to True.
        """
        if not self._in_transaction and self.auto_commit and self.conn:
            self.conn.commit()

    def insert(self, model_instance: T) -> T:
        """Insert a new record into the database.

        Args:
            model_instance: The instance of the model class to insert.

        Returns:
            The updated model instance with the primary key (pk) set.

        Raises:
            RecordInsertionError: If an error occurs during the insertion.
        """
        model_class = type(model_instance)
        table_name = model_class.get_table_name()

        # Get the data from the model
        data = model_instance.model_dump()
        # remove the primary key field if it exists, otherwise we'll get
        # TypeErrors as multiple primary keys will exist
        if data.get("pk", None) == 0:
            data.pop("pk")

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
        else:
            data.pop("pk", None)
            return model_class(pk=cursor.lastrowid, **data)

    def get(
        self, model_class: type[BaseDBModel], primary_key_value: int
    ) -> BaseDBModel | None:
        """Retrieve a single record from the database by its primary key.

        Args:
            model_class: The Pydantic model class representing the table.
            primary_key_value: The value of the primary key to look up.

        Returns:
            An instance of the model class if found, None otherwise.

        Raises:
            RecordFetchError: If there's an error fetching the record.
        """
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
        """Update an existing record in the database.

        Args:
            model_instance: An instance of a Pydantic model to be updated.

        Raises:
            RecordUpdateError: If there's an error updating the record or if it
            is not found.
        """
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
        """Delete a record from the database by its primary key.

        Args:
            model_class: The Pydantic model class representing the table.
            primary_key_value: The value of the primary key of the record to
                delete.

        Raises:
            RecordDeletionError: If there's an error deleting the record.
            RecordNotFoundError: If the record to delete is not found.
        """
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
        """Create a QueryBuilder instance for selecting records.

        Args:
            model_class: The Pydantic model class representing the table.
            fields: Optional list of fields to include in the query.
            exclude: Optional list of fields to exclude from the query.

        Returns:
            A QueryBuilder instance for further query construction.
        """
        query_builder = QueryBuilder(self, model_class, fields)

        # If exclude is provided, apply the exclude method
        if exclude:
            query_builder.exclude(exclude)

        return query_builder

    # --- Context manager methods ---
    def __enter__(self) -> Self:
        """Enter the runtime context for the SqliterDB instance.

        This method is called when entering a 'with' statement. It ensures
        that a database connection is established.

        Note that this method should never be called explicitly, but will be
        called by the 'with' statement when entering the context.

        Returns:
            The SqliterDB instance.

        """
        self.connect()
        self._in_transaction = True
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Exit the runtime context for the SqliterDB instance.

        This method is called when exiting a 'with' statement. It handles
        committing or rolling back transactions based on whether an exception
        occurred, and closes the database connection.

        Args:
            exc_type: The type of the exception that caused the context to be
                exited, or None if no exception was raised.
            exc_value: The instance of the exception that caused the context
                to be exited, or None if no exception was raised.
            traceback: A traceback object encoding the stack trace, or None
                if no exception was raised.

        Note that this method should never be called explicitly, but will be
        called by the 'with' statement when exiting the context.

        """
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
                self._in_transaction = False
