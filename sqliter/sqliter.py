"""Core module for SQLiter, providing the main database interaction class.

This module defines the SqliterDB class, which serves as the primary
interface for all database operations in SQLiter. It handles connection
management, table creation, and CRUD operations, bridging the gap between
Pydantic models and SQLite database interactions.
"""

from __future__ import annotations

import logging
import sqlite3
import sys
import time
from collections import OrderedDict
from typing import TYPE_CHECKING, Any, Optional, TypeVar, Union, cast

from typing_extensions import Self

from sqliter.exceptions import (
    DatabaseConnectionError,
    ForeignKeyConstraintError,
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
from sqliter.model.foreign_key import ForeignKeyInfo, get_foreign_key_info
from sqliter.model.model import BaseDBModel
from sqliter.query.query import QueryBuilder

if TYPE_CHECKING:  # pragma: no cover
    from types import TracebackType

    from pydantic.fields import FieldInfo

T = TypeVar("T", bound=BaseDBModel)


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

    MEMORY_DB = ":memory:"

    def __init__(  # noqa: PLR0913
        self,
        db_filename: Optional[str] = None,
        *,
        memory: bool = False,
        auto_commit: bool = True,
        debug: bool = False,
        logger: Optional[logging.Logger] = None,
        reset: bool = False,
        return_local_time: bool = True,
        cache_enabled: bool = False,
        cache_max_size: int = 1000,
        cache_ttl: Optional[int] = None,
        cache_max_memory_mb: Optional[int] = None,
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
            return_local_time: Whether to return local time for datetime fields.
            cache_enabled: Whether to enable query result caching. Default is
                False.
            cache_max_size: Maximum number of cached queries per table (LRU).
            cache_ttl: Optional time-to-live for cache entries in seconds.
            cache_max_memory_mb: Optional maximum memory usage for cache in
                megabytes. When exceeded, oldest entries are evicted.

        Raises:
            ValueError: If no filename is provided for a non-memory database.
        """
        if memory:
            self.db_filename = self.MEMORY_DB
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
        self.return_local_time = return_local_time

        self._in_transaction = False

        # Initialize cache
        self._cache_enabled = cache_enabled
        self._cache_max_size = cache_max_size
        self._cache_ttl = cache_ttl
        self._cache_max_memory_mb = cache_max_memory_mb

        # Validate cache parameters
        if self._cache_max_size <= 0:
            msg = "cache_max_size must be greater than 0"
            raise ValueError(msg)
        if self._cache_ttl is not None and self._cache_ttl < 0:
            msg = "cache_ttl must be non-negative"
            raise ValueError(msg)
        if (
            self._cache_max_memory_mb is not None
            and self._cache_max_memory_mb <= 0
        ):
            msg = "cache_max_memory_mb must be greater than 0"
            raise ValueError(msg)
        self._cache: OrderedDict[
            str,
            OrderedDict[
                str,
                tuple[
                    Union[BaseDBModel, list[BaseDBModel], None],
                    Optional[float],
                ],
            ],
        ] = OrderedDict()  # {table: {cache_key: (result, expiration)}}
        self._cache_hits = 0
        self._cache_misses = 0

        if self.debug:
            self._setup_logger()

        if self.reset:
            self._reset_database()

    @property
    def filename(self) -> Optional[str]:
        """Returns the filename of the current database or None if in-memory."""
        return None if self.db_filename == self.MEMORY_DB else self.db_filename

    @property
    def is_memory(self) -> bool:
        """Returns True if the database is in-memory."""
        return self.db_filename == self.MEMORY_DB

    @property
    def is_autocommit(self) -> bool:
        """Returns True if auto-commit is enabled."""
        return self.auto_commit

    @property
    def is_connected(self) -> bool:
        """Returns True if the database is connected, False otherwise."""
        return self.conn is not None

    @property
    def table_names(self) -> list[str]:
        """Returns a list of all table names in the database.

        Temporarily connects to the database if not connected and restores
        the connection state afterward.
        """
        was_connected = self.is_connected
        if not was_connected:
            self.connect()

        if self.conn is None:
            err_msg = "Failed to establish a database connection."
            raise DatabaseConnectionError(err_msg)

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%';"
        )
        tables = [row[0] for row in cursor.fetchall()]

        # Restore the connection state
        if not was_connected:
            self.close()

        return tables

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
                # Enable foreign key constraint enforcement
                self.conn.execute("PRAGMA foreign_keys = ON")
            except sqlite3.Error as exc:
                raise DatabaseConnectionError(self.db_filename) from exc
        return self.conn

    def _cache_get(
        self,
        table_name: str,
        cache_key: str,
    ) -> tuple[bool, Any]:
        """Get cached result if valid and not expired.

        Args:
            table_name: The name of the table.
            cache_key: The cache key for the query.

        Returns:
            A tuple of (hit, result) where hit is True if cache hit,
            False if miss. Result is the cached value (which may be None
            or an empty list) on a hit, or None on a miss.
        """
        if not self._cache_enabled:
            return False, None
        if table_name not in self._cache:
            self._cache_misses += 1
            return False, None
        if cache_key not in self._cache[table_name]:
            self._cache_misses += 1
            return False, None

        result, expiration = self._cache[table_name][cache_key]

        # Check TTL expiration
        if expiration is not None and time.time() > expiration:
            self._cache_misses += 1
            del self._cache[table_name][cache_key]
            return False, None

        # Mark as recently used (LRU)
        self._cache[table_name].move_to_end(cache_key)
        self._cache_hits += 1
        return True, result

    def _cache_set(
        self,
        table_name: str,
        cache_key: str,
        result: Any,  # noqa: ANN401
        ttl: Optional[int] = None,
    ) -> None:
        """Store result in cache with optional expiration.

        Args:
            table_name: The name of the table.
            cache_key: The cache key for the query.
            result: The result to cache.
            ttl: Optional TTL override for this specific entry.
        """
        if not self._cache_enabled:
            return

        if table_name not in self._cache:
            self._cache[table_name] = OrderedDict()

        # Calculate expiration (use query-specific TTL if provided)
        expiration = None
        effective_ttl = ttl if ttl is not None else self._cache_ttl
        if effective_ttl is not None:
            expiration = time.time() + effective_ttl

        self._cache[table_name][cache_key] = (result, expiration)
        # Mark as most-recently-used
        self._cache[table_name].move_to_end(cache_key)

        # Enforce memory limit if set
        if self._cache_max_memory_mb is not None:
            max_bytes = self._cache_max_memory_mb * 1024 * 1024
            # Evict LRU entries until under the memory limit
            while (
                table_name in self._cache
                and self._get_table_memory_usage(table_name) > max_bytes
            ):
                self._cache[table_name].popitem(last=False)

        # Enforce LRU by size
        if len(self._cache[table_name]) > self._cache_max_size:
            self._cache[table_name].popitem(last=False)

    def _cache_invalidate_table(self, table_name: str) -> None:
        """Clear all cached queries for a specific table.

        Args:
            table_name: The name of the table to invalidate.
        """
        if not self._cache_enabled:
            return
        self._cache.pop(table_name, None)

    def _get_table_memory_usage(  # noqa: C901
        self, table_name: str
    ) -> int:
        """Calculate the actual memory usage for a table's cache.

        This method recalculates memory usage on-demand by measuring the
        size of all cached entries including tuple and dict overhead.

        Args:
            table_name: The name of the table.

        Returns:
            The memory usage in bytes.
        """
        if table_name not in self._cache:
            return 0

        total = 0
        seen: dict[int, int] = {}

        for key, (result, _expiration) in self._cache[table_name].items():
            # Measure the tuple (result, expiration)
            total += sys.getsizeof((result, _expiration))

            # Measure the dict key (cache_key string)
            total += sys.getsizeof(key)

            # Dict entry overhead (approximately 72 bytes for a dict entry)
            total += 72

            # Recursively measure the result object
            def measure_size(obj: Any) -> int:  # noqa: C901, ANN401
                """Recursively measure object size with memoization."""
                obj_id = id(obj)
                if obj_id in seen:
                    return 0  # Already counted

                size = sys.getsizeof(obj)
                seen[obj_id] = size

                # Handle lists
                if isinstance(obj, list):
                    for item in obj:
                        size += measure_size(item)

                # Handle Pydantic models - measure their fields
                elif hasattr(type(obj), "model_fields"):
                    for field_name in type(obj).model_fields:
                        field_value = getattr(obj, field_name, None)
                        if field_value is not None:
                            size += measure_size(field_value)
                    # Also measure __dict__ if present
                    if hasattr(obj, "__dict__"):
                        size += measure_size(obj.__dict__)

                # Handle dicts
                elif isinstance(obj, dict):
                    for k, v in obj.items():
                        size += measure_size(k)
                        size += measure_size(v)

                # Handle sets and tuples
                elif isinstance(obj, (set, tuple)):
                    for item in obj:
                        size += measure_size(item)

                return size

            total += measure_size(result)

        return total

    def get_cache_stats(self) -> dict[str, int | float]:
        """Get cache performance statistics.

        Returns:
            A dictionary containing cache statistics with keys:
            - hits: Number of cache hits
            - misses: Number of cache misses
            - total: Total number of cache lookups
            - hit_rate: Cache hit rate as a percentage (0-100)
        """
        total = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total * 100) if total > 0 else 0.0
        return {
            "hits": self._cache_hits,
            "misses": self._cache_misses,
            "total": total,
            "hit_rate": round(hit_rate, 2),
        }

    def clear_cache(self) -> None:
        """Clear all cached query results.

        This method removes all cached data from memory, freeing up resources
        and forcing subsequent queries to fetch fresh data from the database.

        Use this when you want to:
        - Free memory used by the cache
        - Force fresh queries after external data changes

        Note:
            Cache statistics (hits/misses) are preserved. To reset statistics,
            create a new database connection.

        Example:
            >>> db.clear_cache()
        """
        self._cache.clear()

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
        self._cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0

    def commit(self) -> None:
        """Commit the current transaction.

        This method explicitly commits any pending changes to the database.
        """
        if self.conn:
            self.conn.commit()

    def _build_field_definitions(
        self,
        model_class: type[BaseDBModel],
        primary_key: str,
    ) -> tuple[list[str], list[str], list[str]]:
        """Build SQL field definitions for table creation.

        Args:
            model_class: The Pydantic model class.
            primary_key: The name of the primary key field.

        Returns:
            A tuple of (fields, foreign_keys, fk_columns) where:
            - fields: List of column definitions
            - foreign_keys: List of FK constraint definitions
            - fk_columns: List of FK column names for index creation
        """
        fields = [f'"{primary_key}" INTEGER PRIMARY KEY AUTOINCREMENT']
        foreign_keys: list[str] = []
        fk_columns: list[str] = []

        for field_name, field_info in model_class.model_fields.items():
            if field_name == primary_key:
                continue

            fk_info = get_foreign_key_info(field_info)
            if fk_info is not None:
                col, constraint = self._build_fk_field(field_name, fk_info)
                fields.append(col)
                foreign_keys.append(constraint)
                fk_columns.append(fk_info.db_column or field_name)
            else:
                fields.append(self._build_regular_field(field_name, field_info))

        return fields, foreign_keys, fk_columns

    def _build_fk_field(
        self, field_name: str, fk_info: ForeignKeyInfo
    ) -> tuple[str, str]:
        """Build FK column definition and constraint.

        Args:
            field_name: The name of the field.
            fk_info: The ForeignKeyInfo metadata.

        Returns:
            A tuple of (column_def, fk_constraint).
        """
        column_name = fk_info.db_column or field_name
        null_str = "" if fk_info.null else "NOT NULL"
        unique_str = "UNIQUE" if fk_info.unique else ""

        field_def = f'"{column_name}" INTEGER {null_str} {unique_str}'
        column_def = " ".join(field_def.split())

        target_table = fk_info.to_model.get_table_name()
        fk_constraint = (
            f'FOREIGN KEY ("{column_name}") '
            f'REFERENCES "{target_table}"("pk") '
            f"ON DELETE {fk_info.on_delete} "
            f"ON UPDATE {fk_info.on_update}"
        )

        return column_def, fk_constraint

    def _build_regular_field(
        self, field_name: str, field_info: FieldInfo
    ) -> str:
        """Build a regular (non-FK) column definition.

        Args:
            field_name: The name of the field.
            field_info: The Pydantic field info.

        Returns:
            The column definition string.
        """
        sqlite_type = infer_sqlite_type(field_info.annotation)
        unique_constraint = ""
        if (
            hasattr(field_info, "json_schema_extra")
            and field_info.json_schema_extra
            and isinstance(field_info.json_schema_extra, dict)
            and field_info.json_schema_extra.get("unique", False)
        ):
            unique_constraint = "UNIQUE"
        return f'"{field_name}" {sqlite_type} {unique_constraint}'.strip()

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

        fields, foreign_keys, fk_columns = self._build_field_definitions(
            model_class, primary_key
        )

        # Combine field definitions and FK constraints
        all_definitions = fields + foreign_keys

        create_str = (
            "CREATE TABLE IF NOT EXISTS" if exists_ok else "CREATE TABLE"
        )

        create_table_sql = f"""
        {create_str} "{table_name}" (
            {", ".join(all_definitions)}
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

        # Create indexes for FK columns
        for column_name in fk_columns:
            index_sql = (
                f'CREATE INDEX IF NOT EXISTS "idx_{table_name}_{column_name}" '
                f'ON "{table_name}" ("{column_name}")'
            )
            self._execute_sql(index_sql)

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

            # Quote field names for index creation
            quoted_fields = ", ".join(f'"{field}"' for field in fields)

            create_index_sql = (
                f"CREATE{index_type}INDEX IF NOT EXISTS "
                f"idx_{model_class.get_table_name()}"
                f"_{index_name}{index_postfix} "
                f'ON "{model_class.get_table_name()}" ({quoted_fields})'
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

    def _set_insert_timestamps(
        self, model_instance: T, *, timestamp_override: bool
    ) -> None:
        """Set created_at and updated_at timestamps for insert.

        Args:
            model_instance: The model instance to update.
            timestamp_override: If True, respect provided non-zero values.
        """
        current_timestamp = int(time.time())

        if not timestamp_override:
            model_instance.created_at = current_timestamp
            model_instance.updated_at = current_timestamp
        else:
            if model_instance.created_at == 0:
                model_instance.created_at = current_timestamp
            if model_instance.updated_at == 0:
                model_instance.updated_at = current_timestamp

    def _create_instance_from_data(
        self,
        model_class: type[T],
        data: dict[str, Any],
        pk: Optional[int] = None,
    ) -> T:
        """Create a model instance from deserialized data.

        Handles ORM-specific field exclusions and db_context setup.

        Args:
            model_class: The model class to instantiate.
            data: Raw data dictionary from the database.
            pk: Optional primary key value to set.

        Returns:
            A new model instance with db_context set if applicable.
        """
        # Deserialize each field before creating the model instance
        deserialized_data: dict[str, Any] = {}
        for field_name, value in data.items():
            deserialized_data[field_name] = model_class.deserialize_field(
                field_name, value, return_local_time=self.return_local_time
            )
        # For ORM mode, exclude FK descriptor fields from data
        for fk_field in getattr(model_class, "fk_descriptors", {}):
            deserialized_data.pop(fk_field, None)

        if pk is not None:
            instance = model_class(pk=pk, **deserialized_data)
        else:
            instance = model_class(**deserialized_data)

        # Set db_context for ORM lazy loading and reverse relationships
        if hasattr(instance, "db_context"):
            instance.db_context = self
        return instance

    def insert(
        self, model_instance: T, *, timestamp_override: bool = False
    ) -> T:
        """Insert a new record into the database.

        Args:
            model_instance: The instance of the model class to insert.
            timestamp_override: If True, override the created_at and updated_at
                timestamps with provided values. Default is False. If the values
                are not provided, they will be set to the current time as
                normal. Without this flag, the timestamps will always be set to
                the current time, even if provided.

        Returns:
            The updated model instance with the primary key (pk) set.

        Raises:
            RecordInsertionError: If an error occurs during the insertion.
        """
        model_class = type(model_instance)
        table_name = model_class.get_table_name()

        self._set_insert_timestamps(
            model_instance, timestamp_override=timestamp_override
        )

        # Get the data from the model
        data = model_instance.model_dump()

        # Serialize the data
        for field_name, value in list(data.items()):
            data[field_name] = model_instance.serialize_field(value)

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
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute(insert_sql, values)
            self._maybe_commit()

        except sqlite3.IntegrityError as exc:
            # Rollback implicit transaction if not in user-managed transaction
            if not self._in_transaction and self.conn:
                self.conn.rollback()
            # Check for foreign key constraint violation
            if "FOREIGN KEY constraint failed" in str(exc):
                fk_operation = "insert"
                fk_reason = "does not exist in referenced table"
                raise ForeignKeyConstraintError(
                    fk_operation, fk_reason
                ) from exc
            raise RecordInsertionError(table_name) from exc
        except sqlite3.Error as exc:
            # Rollback implicit transaction if not in user-managed transaction
            if not self._in_transaction and self.conn:
                self.conn.rollback()
            raise RecordInsertionError(table_name) from exc
        else:
            self._cache_invalidate_table(table_name)
            data.pop("pk", None)
            return self._create_instance_from_data(
                model_class, data, pk=cursor.lastrowid
            )

    def get(
        self,
        model_class: type[T],
        primary_key_value: int,
        *,
        bypass_cache: bool = False,
        cache_ttl: Optional[int] = None,
    ) -> T | None:
        """Retrieve a single record from the database by its primary key.

        Args:
            model_class: The Pydantic model class representing the table.
            primary_key_value: The value of the primary key to look up.
            bypass_cache: If True, skip reading/writing cache for this call.
            cache_ttl: Optional TTL override for this specific lookup.

        Returns:
            An instance of the model class if found, None otherwise.

        Raises:
            RecordFetchError: If there's an error fetching the record.
        """
        if cache_ttl is not None and cache_ttl < 0:
            msg = "cache_ttl must be non-negative"
            raise ValueError(msg)

        table_name = model_class.get_table_name()
        primary_key = model_class.get_primary_key()
        cache_key = f"pk:{primary_key_value}"

        if not bypass_cache:
            hit, cached = self._cache_get(table_name, cache_key)
            if hit:
                return cast("Optional[T]", cached)

        fields = ", ".join(model_class.model_fields)

        select_sql = f"""
            SELECT {fields} FROM {table_name} WHERE {primary_key} = ?
        """  # noqa: S608

        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute(select_sql, (primary_key_value,))
            result = cursor.fetchone()

            if result:
                result_dict = {
                    field: result[idx]
                    for idx, field in enumerate(model_class.model_fields)
                }
                instance = self._create_instance_from_data(
                    model_class, result_dict
                )
                if not bypass_cache:
                    self._cache_set(
                        table_name, cache_key, instance, ttl=cache_ttl
                    )
                return instance
        except sqlite3.Error as exc:
            raise RecordFetchError(table_name) from exc
        else:
            if not bypass_cache:
                self._cache_set(table_name, cache_key, None, ttl=cache_ttl)
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

        # Set updated_at timestamp
        current_timestamp = int(time.time())
        model_instance.updated_at = current_timestamp

        # Get the data and serialize any datetime/date fields
        data = model_instance.model_dump()

        for field_name, value in list(data.items()):
            data[field_name] = model_instance.serialize_field(value)

        # Remove the primary key from the update data
        primary_key_value = data.pop(primary_key)

        # Create the SQL using the processed data
        fields = ", ".join(f"{field} = ?" for field in data)
        values = tuple(data.values())

        update_sql = f"""
            UPDATE {table_name}
            SET {fields}
            WHERE {primary_key} = ?
        """  # noqa: S608

        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute(update_sql, (*values, primary_key_value))

            # Check if any rows were updated
            if cursor.rowcount == 0:
                raise RecordNotFoundError(primary_key_value)  # noqa: TRY301

            self._maybe_commit()
            self._cache_invalidate_table(table_name)

        except RecordNotFoundError:
            # Rollback implicit transaction if not in user-managed transaction
            if not self._in_transaction and self.conn:
                self.conn.rollback()
            raise
        except sqlite3.Error as exc:
            # Rollback implicit transaction if not in user-managed transaction
            if not self._in_transaction and self.conn:
                self.conn.rollback()
            raise RecordUpdateError(table_name) from exc

    def delete(
        self, model_class: type[BaseDBModel], primary_key_value: Union[int, str]
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
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute(delete_sql, (primary_key_value,))

            if cursor.rowcount == 0:
                raise RecordNotFoundError(primary_key_value)  # noqa: TRY301
            self._maybe_commit()
            self._cache_invalidate_table(table_name)
        except RecordNotFoundError:
            # Rollback implicit transaction if not in user-managed transaction
            if not self._in_transaction and self.conn:
                self.conn.rollback()
            raise
        except sqlite3.IntegrityError as exc:
            # Rollback implicit transaction if not in user-managed transaction
            if not self._in_transaction and self.conn:
                self.conn.rollback()
            # Check for foreign key constraint violation (RESTRICT)
            if "FOREIGN KEY constraint failed" in str(exc):
                fk_operation = "delete"
                fk_reason = "is still referenced by other records"
                raise ForeignKeyConstraintError(
                    fk_operation, fk_reason
                ) from exc
            raise RecordDeletionError(table_name) from exc
        except sqlite3.Error as exc:
            # Rollback implicit transaction if not in user-managed transaction
            if not self._in_transaction and self.conn:
                self.conn.rollback()
            raise RecordDeletionError(table_name) from exc

    def select(
        self,
        model_class: type[T],
        fields: Optional[list[str]] = None,
        exclude: Optional[list[str]] = None,
    ) -> QueryBuilder[T]:
        """Create a QueryBuilder instance for selecting records.

        Args:
            model_class: The Pydantic model class representing the table.
            fields: Optional list of fields to include in the query.
            exclude: Optional list of fields to exclude from the query.

        Returns:
            A QueryBuilder instance for further query construction.
        """
        query_builder: QueryBuilder[T] = QueryBuilder(self, model_class, fields)

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
        # Clear cache when exiting context
        self._cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
