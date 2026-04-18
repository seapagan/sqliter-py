"""Async database support for SQLiter."""

from __future__ import annotations

import sqlite3
import time
from typing import TYPE_CHECKING, Any, Optional, TypeVar, cast

import aiosqlite
from typing_extensions import Self

from sqliter.asyncio.query import AsyncQueryBuilder
from sqliter.exceptions import (
    DatabaseConnectionError,
    ForeignKeyConstraintError,
    RecordDeletionError,
    RecordFetchError,
    RecordInsertionError,
    RecordNotFoundError,
    RecordUpdateError,
    SqlExecutionError,
    TableCreationError,
    TableDeletionError,
)
from sqliter.model.model import BaseDBModel
from sqliter.sqliter import SqliterDB

if TYPE_CHECKING:  # pragma: no cover
    import logging
    from collections.abc import Sequence
    from types import TracebackType

T = TypeVar("T", bound=BaseDBModel)


class AsyncSqliterDB:
    """Async wrapper around SQLiter's sync helper logic."""

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
        """Initialize a new async database instance."""
        if reset:
            msg = (
                "reset=True is not supported in AsyncSqliterDB.__init__(). "
                "Use `await AsyncSqliterDB.create(..., reset=True)` instead."
            )
            raise ValueError(msg)

        self._sync = SqliterDB(
            db_filename,
            memory=memory,
            auto_commit=auto_commit,
            debug=debug,
            logger=logger,
            reset=False,
            return_local_time=return_local_time,
            cache_enabled=cache_enabled,
            cache_max_size=cache_max_size,
            cache_ttl=cache_ttl,
            cache_max_memory_mb=cache_max_memory_mb,
        )
        self.conn: aiosqlite.Connection | None = None

    @property
    def db_filename(self) -> str:
        """Return the configured database filename."""
        return self._sync.db_filename

    @property
    def auto_commit(self) -> bool:
        """Return whether auto-commit is enabled."""
        return self._sync.auto_commit

    @property
    def debug(self) -> bool:
        """Return whether debug logging is enabled."""
        return self._sync.debug

    @property
    def logger(self) -> logging.Logger | None:
        """Return the configured logger."""
        return self._sync.logger

    @property
    def return_local_time(self) -> bool:
        """Return whether datetime deserialization uses local time."""
        return self._sync.return_local_time

    @property
    def is_connected(self) -> bool:
        """Return whether an async connection is open."""
        return self.conn is not None

    @property
    def is_memory(self) -> bool:
        """Return whether the database uses the in-memory backend."""
        return self._sync.is_memory

    @property
    def filename(self) -> str | None:
        """Return the on-disk filename, if any."""
        return self._sync.filename

    @property
    def _in_transaction(self) -> bool:
        """Return the transaction flag."""
        return self._sync._in_transaction  # noqa: SLF001

    @_in_transaction.setter
    def _in_transaction(self, value: bool) -> None:
        """Set the transaction flag."""
        self._sync._in_transaction = value  # noqa: SLF001

    def now(self) -> int:
        """Return the current unix timestamp."""
        return int(time.time())

    @property
    def in_transaction(self) -> bool:
        """Return whether the DB is in an explicit transaction."""
        return self._in_transaction

    @classmethod
    async def create(  # noqa: PLR0913
        cls,
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
    ) -> AsyncSqliterDB:
        """Create an async DB instance and optionally reset the database."""
        db = cls(
            db_filename,
            memory=memory,
            auto_commit=auto_commit,
            debug=debug,
            logger=logger,
            return_local_time=return_local_time,
            cache_enabled=cache_enabled,
            cache_max_size=cache_max_size,
            cache_ttl=cache_ttl,
            cache_max_memory_mb=cache_max_memory_mb,
        )
        if reset:
            await db.reset_database()
        return db

    def _cache_get(
        self,
        table_name: str,
        cache_key: str,
    ) -> tuple[bool, Any]:
        """Delegate cache lookup to the sync helper instance."""
        return self._sync._cache_get(table_name, cache_key)  # noqa: SLF001

    def _cache_set(
        self,
        table_name: str,
        cache_key: str,
        result: Any,  # noqa: ANN401
        ttl: Optional[int] = None,
    ) -> None:
        """Delegate cache writes to the sync helper instance."""
        self._sync._cache_set(table_name, cache_key, result, ttl=ttl)  # noqa: SLF001

    def _cache_invalidate_table(self, table_name: str) -> None:
        """Delegate cache invalidation to the sync helper instance."""
        self._sync._cache_invalidate_table(table_name)  # noqa: SLF001

    def _create_instance_from_data(
        self,
        model_class: type[T],
        data: dict[str, Any],
        pk: Optional[int] = None,
    ) -> T:
        """Create a model instance using the sync helper logic."""
        instance = self._sync._create_instance_from_data(  # noqa: SLF001
            model_class,
            data,
            pk=pk,
        )
        if hasattr(instance, "db_context"):
            instance.db_context = self
        return instance

    def _build_field_definitions(
        self,
        model_class: type[BaseDBModel],
        primary_key: str,
    ) -> tuple[list[str], list[str], list[str]]:
        """Delegate field definition generation to the sync helper instance."""
        return self._sync._build_field_definitions(model_class, primary_key)  # noqa: SLF001

    def _build_model_select_list(self, model_class: type[BaseDBModel]) -> str:
        """Delegate SELECT list construction to the sync helper instance."""
        return self._sync._build_model_select_list(model_class)  # noqa: SLF001

    def _map_data_to_db_columns(
        self,
        model_class: type[BaseDBModel],
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Delegate field-to-column mapping to the sync helper instance."""
        return self._sync._map_data_to_db_columns(model_class, data)  # noqa: SLF001

    def _model_field_to_db_column(
        self,
        model_class: type[BaseDBModel],
        field_name: str,
    ) -> str:
        """Delegate model-field column resolution to the sync helper."""
        return self._sync._model_field_to_db_column(model_class, field_name)  # noqa: SLF001

    def _set_insert_timestamps(
        self,
        model_instance: T,
        *,
        timestamp_override: bool,
    ) -> None:
        """Delegate insert timestamp handling to the sync helper instance."""
        self._sync._set_insert_timestamps(  # noqa: SLF001
            model_instance,
            timestamp_override=timestamp_override,
        )

    async def _execute_async(
        self,
        cursor: aiosqlite.Cursor,
        sql: str,
        values: Sequence[Any] = (),
    ) -> aiosqlite.Cursor:
        """Execute SQL and preserve SQL debug logging."""
        self._sync._log_sql(sql, values)  # noqa: SLF001
        await cursor.execute(sql, values)
        return cursor

    async def connect(self) -> aiosqlite.Connection:
        """Establish a connection to the SQLite database."""
        if self.conn is None:
            try:
                self.conn = await aiosqlite.connect(self.db_filename)
                await self.conn.execute("PRAGMA foreign_keys = ON")
            except sqlite3.Error as exc:
                raise DatabaseConnectionError(self.db_filename) from exc
        return self.conn

    async def get_table_names(self) -> list[str]:
        """Return a list of all user-created table names."""
        was_connected = self.is_connected
        if not was_connected:
            await self.connect()

        if self.conn is None:
            err_msg = "Failed to establish a database connection."
            raise DatabaseConnectionError(err_msg)

        cursor = await self.conn.cursor()
        await self._execute_async(
            cursor,
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%';",
        )
        tables = [row[0] for row in await cursor.fetchall()]

        if not was_connected:
            await self.close()

        return tables

    async def reset_database(self) -> None:
        """Drop all user-created tables in the database."""
        conn = await self.connect()
        cursor = await conn.cursor()
        await self._execute_async(
            cursor,
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%';",
        )
        tables = list(await cursor.fetchall())

        for table in tables:
            await self._execute_async(
                cursor,
                f"DROP TABLE IF EXISTS {table[0]}",
            )

        await conn.commit()

        if self.debug and self.logger:
            self.logger.debug(
                "Database reset: %s user-created tables dropped.",
                len(tables),
            )

    async def close(self) -> None:
        """Close the current async database connection."""
        if self.conn is not None:
            await self._maybe_commit()
            await self.conn.close()
            self.conn = None
        self._sync.clear_cache()
        self._sync._cache_hits = 0  # noqa: SLF001
        self._sync._cache_misses = 0  # noqa: SLF001

    async def commit(self) -> None:
        """Commit the current transaction."""
        if self.conn is not None:
            await self.conn.commit()

    async def _maybe_commit(self) -> None:
        """Commit changes when auto-commit is enabled."""
        if (
            not self._in_transaction
            and self.auto_commit
            and self.conn is not None
        ):
            await self.conn.commit()

    async def maybe_commit(self) -> None:
        """Public wrapper for conditional commit behavior."""
        await self._maybe_commit()

    async def create_table(
        self,
        model_class: type[BaseDBModel],
        *,
        exists_ok: bool = True,
        force: bool = False,
    ) -> None:
        """Create a table from a SQLiter model class."""
        table_name = model_class.get_table_name()
        primary_key = model_class.get_primary_key()

        if force:
            await self._execute_sql(f"DROP TABLE IF EXISTS {table_name}")

        fields, foreign_keys, fk_columns = self._build_field_definitions(
            model_class,
            primary_key,
        )
        all_definitions = fields + foreign_keys
        create_str = (
            "CREATE TABLE IF NOT EXISTS" if exists_ok else "CREATE TABLE"
        )
        create_table_sql = f"""
        {create_str} "{table_name}" (
            {", ".join(all_definitions)}
        )
        """

        try:
            conn = await self.connect()
            cursor = await conn.cursor()
            await self._execute_async(cursor, create_table_sql)
            await conn.commit()
        except sqlite3.Error as exc:
            raise TableCreationError(table_name) from exc

        for column_name in fk_columns:
            index_sql = (
                f'CREATE INDEX IF NOT EXISTS "idx_{table_name}_{column_name}" '
                f'ON "{table_name}" ("{column_name}")'
            )
            await self._execute_sql(index_sql)

    async def _execute_sql(self, sql: str) -> None:
        """Execute a raw SQL statement."""
        try:
            conn = await self.connect()
            cursor = await conn.cursor()
            await self._execute_async(cursor, sql)
            await conn.commit()
        except (sqlite3.Error, sqlite3.Warning) as exc:
            raise SqlExecutionError(sql) from exc

    async def drop_table(self, model_class: type[BaseDBModel]) -> None:
        """Drop the table associated with the given model class."""
        table_name = model_class.get_table_name()
        drop_table_sql = f"DROP TABLE IF EXISTS {table_name}"

        try:
            conn = await self.connect()
            cursor = await conn.cursor()
            await self._execute_async(cursor, drop_table_sql)
            await self.commit()
        except sqlite3.Error as exc:
            raise TableDeletionError(table_name) from exc

    async def insert(
        self,
        model_instance: T,
        *,
        timestamp_override: bool = False,
    ) -> T:
        """Insert a model instance into the database."""
        model_class = type(model_instance)
        table_name = model_class.get_table_name()
        self._set_insert_timestamps(
            model_instance,
            timestamp_override=timestamp_override,
        )

        data = model_instance.model_dump()
        for field_name, value in list(data.items()):
            data[field_name] = model_instance.serialize_field(value)

        if data.get("pk", None) == 0:
            data.pop("pk")

        sql_data = self._map_data_to_db_columns(model_class, data)
        fields = ", ".join(f'"{field}"' for field in sql_data)
        placeholders = ", ".join(
            "?" if value is not None else "NULL" for value in sql_data.values()
        )
        values = tuple(
            value for value in sql_data.values() if value is not None
        )
        insert_sql = f"""
        INSERT INTO {table_name} ({fields})
        VALUES ({placeholders})
        """

        try:
            conn = await self.connect()
            cursor = await conn.cursor()
            await self._execute_async(cursor, insert_sql, values)
            await self._maybe_commit()
        except sqlite3.IntegrityError as exc:
            if not self._in_transaction and self.conn is not None:
                await self.conn.rollback()
            if "FOREIGN KEY constraint failed" in str(exc):
                operation = "insert"
                reason = "does not exist in referenced table"
                raise ForeignKeyConstraintError(operation, reason) from exc
            raise RecordInsertionError(table_name) from exc
        except sqlite3.Error as exc:
            if not self._in_transaction and self.conn is not None:
                await self.conn.rollback()
            raise RecordInsertionError(table_name) from exc
        else:
            self._cache_invalidate_table(table_name)
            data.pop("pk", None)
            return self._create_instance_from_data(
                model_class,
                data,
                pk=cursor.lastrowid,
            )

    async def bulk_insert(
        self,
        instances: Sequence[T],
        *,
        timestamp_override: bool = False,
    ) -> list[T]:
        """Insert multiple records in a single transaction."""
        if not instances:
            return []

        model_class = type(instances[0])
        for inst in instances[1:]:
            if type(inst) is not model_class:
                msg = (
                    "All instances must be the same model type. "
                    f"Expected {model_class.__name__}, "
                    f"got {type(inst).__name__}."
                )
                raise ValueError(msg)

        return [
            await self.insert(
                instance,
                timestamp_override=timestamp_override,
            )
            for instance in instances
        ]

    async def get(
        self,
        model_class: type[T],
        primary_key_value: int,
        *,
        bypass_cache: bool = False,
        cache_ttl: Optional[int] = None,
    ) -> T | None:
        """Fetch a single model instance by primary key."""
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

        fields = self._build_model_select_list(model_class)
        select_sql = f"""
            SELECT {fields} FROM {table_name} WHERE {primary_key} = ?
        """

        try:
            conn = await self.connect()
            cursor = await conn.cursor()
            await self._execute_async(cursor, select_sql, (primary_key_value,))
            result = await cursor.fetchone()
        except sqlite3.Error as exc:
            raise RecordFetchError(table_name) from exc

        if result:
            result_dict = {
                field: result[idx]
                for idx, field in enumerate(model_class.model_fields)
            }
            instance = self._create_instance_from_data(model_class, result_dict)
            if not bypass_cache:
                self._cache_set(table_name, cache_key, instance, ttl=cache_ttl)
            return instance

        if not bypass_cache:
            self._cache_set(table_name, cache_key, None, ttl=cache_ttl)
        return None

    async def update(self, model_instance: BaseDBModel) -> None:
        """Update an existing model instance."""
        model_class = type(model_instance)
        table_name = model_class.get_table_name()
        primary_key = model_class.get_primary_key()
        model_instance.updated_at = self.now()

        data = model_instance.model_dump()
        for field_name, value in list(data.items()):
            data[field_name] = model_instance.serialize_field(value)

        primary_key_value = data.pop(primary_key)
        sql_data = self._map_data_to_db_columns(model_class, data)
        fields = ", ".join(f'"{field}" = ?' for field in sql_data)
        values = tuple(sql_data.values())
        update_sql = f"""
            UPDATE {table_name}
            SET {fields}
            WHERE {primary_key} = ?
        """

        try:
            conn = await self.connect()
            cursor = await conn.cursor()
            await self._execute_async(
                cursor,
                update_sql,
                (*values, primary_key_value),
            )

            if cursor.rowcount == 0:
                raise RecordNotFoundError(primary_key_value)

            await self._maybe_commit()
            self._cache_invalidate_table(table_name)
        except RecordNotFoundError:
            if not self._in_transaction and self.conn is not None:
                await self.conn.rollback()
            raise
        except sqlite3.Error as exc:
            if not self._in_transaction and self.conn is not None:
                await self.conn.rollback()
            raise RecordUpdateError(table_name) from exc

    async def delete(
        self,
        model_class: type[BaseDBModel],
        primary_key_value: int | str,
    ) -> None:
        """Delete a record by primary key."""
        table_name = model_class.get_table_name()
        primary_key = model_class.get_primary_key()
        delete_sql = f"""
            DELETE FROM {table_name} WHERE {primary_key} = ?
        """

        try:
            conn = await self.connect()
            cursor = await conn.cursor()
            await self._execute_async(cursor, delete_sql, (primary_key_value,))

            if cursor.rowcount == 0:
                raise RecordNotFoundError(primary_key_value)

            await self._maybe_commit()
            self._cache_invalidate_table(table_name)
        except RecordNotFoundError:
            if not self._in_transaction and self.conn is not None:
                await self.conn.rollback()
            raise
        except sqlite3.IntegrityError as exc:
            if not self._in_transaction and self.conn is not None:
                await self.conn.rollback()
            if "FOREIGN KEY constraint failed" in str(exc):
                operation = "delete"
                reason = "is still referenced by other records"
                raise ForeignKeyConstraintError(operation, reason) from exc
            raise RecordDeletionError(table_name) from exc
        except sqlite3.Error as exc:
            if not self._in_transaction and self.conn is not None:
                await self.conn.rollback()
            raise RecordDeletionError(table_name) from exc

    async def update_where(
        self,
        model_class: type[T],
        where: dict[str, Any],
        values: dict[str, Any],
    ) -> int:
        """Update records matching the given filter conditions."""
        query_builder = self.select(model_class)
        query_builder.filter(**where)
        return await query_builder.update(values)

    def select(
        self,
        model_class: type[T],
        fields: Optional[list[str]] = None,
        exclude: Optional[list[str]] = None,
    ) -> AsyncQueryBuilder[T]:
        """Create an async query builder for the given model class."""
        query_builder = AsyncQueryBuilder(self, model_class, fields)
        if exclude:
            query_builder.exclude(exclude)
        return query_builder

    async def __aenter__(self) -> Self:
        """Enter the async transaction context."""
        await self.connect()
        self._in_transaction = True
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Exit the async transaction context."""
        if self.conn is not None:
            try:
                if exc_type:
                    await self.conn.rollback()
                else:
                    await self.conn.commit()
            finally:
                await self.conn.close()
                self.conn = None
                self._in_transaction = False
        self._sync.clear_cache()
        self._sync._cache_hits = 0  # noqa: SLF001
        self._sync._cache_misses = 0  # noqa: SLF001
