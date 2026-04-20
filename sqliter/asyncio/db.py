"""Async database support for SQLiter."""

from __future__ import annotations

import sqlite3
import time
from contextlib import suppress
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
from sqliter.sqliter import (
    DeletePlan,
    GetPlan,
    InsertPlan,
    SqliterDB,
    UpdatePlan,
)

if TYPE_CHECKING:  # pragma: no cover
    import logging
    from collections.abc import Sequence
    from types import TracebackType

T = TypeVar("T", bound=BaseDBModel)


class AsyncSqliterDB:
    """Async SQLite database interface backed by aiosqlite."""

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
    def is_autocommit(self) -> bool:
        """Return whether auto-commit is enabled."""
        return self._sync.is_autocommit

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
    def in_transaction(self) -> bool:
        """Return whether the DB is in an explicit transaction."""
        return self._sync.in_transaction

    def now(self) -> int:
        """Return the current unix timestamp."""
        return int(time.time())

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
        return self._sync.cache_get(table_name, cache_key)

    def cache_get(
        self,
        table_name: str,
        cache_key: str,
    ) -> tuple[bool, Any]:
        """Return a cached value for a table/query key pair."""
        return self._cache_get(table_name, cache_key)

    def _cache_set(
        self,
        table_name: str,
        cache_key: str,
        result: Any,  # noqa: ANN401
        ttl: Optional[int] = None,
    ) -> None:
        """Delegate cache writes to the sync helper instance."""
        self._sync.cache_set(table_name, cache_key, result, ttl=ttl)

    def cache_set(
        self,
        table_name: str,
        cache_key: str,
        result: Any,  # noqa: ANN401
        ttl: Optional[int] = None,
    ) -> None:
        """Store a value in the query cache."""
        self._cache_set(table_name, cache_key, result, ttl=ttl)

    def _cache_invalidate_table(self, table_name: str) -> None:
        """Delegate cache invalidation to the sync helper instance."""
        self._sync.invalidate_table_cache(table_name)

    def invalidate_table_cache(self, table_name: str) -> None:
        """Invalidate all cache entries for a specific table."""
        self._cache_invalidate_table(table_name)

    def get_cache_stats(self) -> dict[str, int | float]:
        """Return query cache performance statistics."""
        return self._sync.get_cache_stats()

    def clear_cache(self) -> None:
        """Clear all cached query results."""
        self._sync.clear_cache()

    def reset_cache_stats(self) -> None:
        """Reset cache hit/miss performance statistics."""
        self._sync.reset_cache_stats()

    def _create_instance_from_data(
        self,
        model_class: type[T],
        data: dict[str, Any],
        pk: Optional[int] = None,
    ) -> T:
        """Create a model instance using the sync helper logic."""
        return self._sync.create_instance_from_data(
            model_class,
            data,
            pk=pk,
            db_context=self,
        )

    def _build_field_definitions(
        self,
        model_class: type[BaseDBModel],
        primary_key: str,
    ) -> tuple[list[str], list[str], list[str]]:
        """Delegate field definition generation to the sync helper instance."""
        return self._sync.build_field_definitions(model_class, primary_key)

    def _build_model_select_list(self, model_class: type[BaseDBModel]) -> str:
        """Delegate SELECT list construction to the sync helper instance."""
        return self._sync.build_model_select_list(model_class)

    def _map_data_to_db_columns(
        self,
        model_class: type[BaseDBModel],
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Delegate field-to-column mapping to the sync helper instance."""
        return self._sync.map_data_to_db_columns(model_class, data)

    def _model_field_to_db_column(
        self,
        model_class: type[BaseDBModel],
        field_name: str,
    ) -> str:
        """Delegate model-field column resolution to the sync helper."""
        return self._sync.model_field_to_db_column(model_class, field_name)

    def _set_insert_timestamps(
        self,
        model_instance: T,
        *,
        timestamp_override: bool,
    ) -> None:
        """Delegate insert timestamp handling to the sync helper instance."""
        self._sync.set_insert_timestamps(
            model_instance,
            timestamp_override=timestamp_override,
        )

    def _build_insert_plan(
        self,
        model_instance: T,
        *,
        timestamp_override: bool,
    ) -> InsertPlan:
        """Delegate insert SQL/value construction to the sync helper."""
        return self._sync._build_insert_plan(  # noqa: SLF001
            model_instance,
            timestamp_override=timestamp_override,
        )

    def _build_get_plan(
        self,
        model_class: type[BaseDBModel],
        primary_key_value: int,
    ) -> GetPlan:
        """Delegate single-record SELECT construction to the sync helper."""
        return self._sync._build_get_plan(  # noqa: SLF001
            model_class,
            primary_key_value,
        )

    def _build_update_plan(
        self,
        model_instance: BaseDBModel,
    ) -> UpdatePlan:
        """Delegate update SQL/value construction to the sync helper."""
        return self._sync._build_update_plan(  # noqa: SLF001
            model_instance,
            current_timestamp=self.now(),
        )

    def _build_delete_plan(
        self,
        model_class: type[BaseDBModel],
        primary_key_value: int | str,
    ) -> DeletePlan:
        """Delegate delete SQL/value construction to the sync helper."""
        return self._sync._build_delete_plan(  # noqa: SLF001
            model_class,
            primary_key_value,
        )

    async def _execute_async(
        self,
        cursor: aiosqlite.Cursor,
        sql: str,
        values: Sequence[Any] = (),
    ) -> aiosqlite.Cursor:
        """Execute SQL and preserve SQL debug logging."""
        self._sync.log_sql(sql, values)
        await cursor.execute(sql, values)
        return cursor

    async def execute_cursor(
        self,
        cursor: aiosqlite.Cursor,
        sql: str,
        values: Sequence[Any] = (),
    ) -> aiosqlite.Cursor:
        """Execute SQL on an existing async cursor."""
        return await self._execute_async(cursor, sql, values)

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

        if not was_connected and not self.is_memory:
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
        self._sync.reset_cache_stats()

    async def commit(self) -> None:
        """Commit the current transaction."""
        if self.conn is not None:
            await self.conn.commit()

    async def _maybe_commit(self) -> None:
        """Commit changes when auto-commit is enabled."""
        if (
            not self.in_transaction
            and self.auto_commit
            and self.conn is not None
        ):
            await self.conn.commit()

    async def _maybe_rollback(self) -> None:
        """Rollback changes when auto-commit is enabled."""
        if (
            not self.in_transaction
            and self.auto_commit
            and self.conn is not None
        ):
            await self.conn.rollback()

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
        if force:
            await self._execute_sql(f"DROP TABLE IF EXISTS {table_name}")

        table_name, create_table_sql, fk_columns = (
            self._sync._build_create_table_sql(  # noqa: SLF001
                model_class,
                exists_ok=exists_ok,
            )
        )

        try:
            conn = await self.connect()
            cursor = await conn.cursor()
            await self._execute_async(cursor, create_table_sql)
            await conn.commit()
        except sqlite3.Error as exc:
            raise TableCreationError(table_name) from exc

        for column_name in fk_columns:
            await self._execute_sql(
                self._sync._build_fk_index_sql(  # noqa: SLF001
                    table_name,
                    column_name,
                )
            )

        if hasattr(model_class.Meta, "indexes"):
            await self._create_indexes(
                model_class,
                model_class.Meta.indexes,
                unique=False,
            )

        if hasattr(model_class.Meta, "unique_indexes"):
            await self._create_indexes(
                model_class,
                model_class.Meta.unique_indexes,
                unique=True,
            )

        await self._create_m2m_junction_tables(model_class)

    async def _create_indexes(
        self,
        model_class: type[BaseDBModel],
        indexes: list[str | tuple[str]],
        *,
        unique: bool = False,
    ) -> None:
        """Create regular or unique indexes for a model."""
        for index in indexes:
            await self._execute_sql(
                self._sync._build_index_sql(  # noqa: SLF001
                    model_class,
                    index,
                    unique=unique,
                )
            )

    async def _create_m2m_junction_tables(
        self,
        model_class: type[BaseDBModel],
    ) -> None:
        """Create junction tables for M2M relationships on a model."""
        try:
            from sqliter.orm.registry import ModelRegistry  # noqa: PLC0415
        except ImportError:
            return

        table_name = model_class.get_table_name()
        m2m_rels = ModelRegistry.get_m2m_relationships(table_name)

        for rel in m2m_rels:
            junction_table = rel["junction_table"]
            to_model = rel["to_model"]
            to_table = to_model.get_table_name()
            sorted_tables = sorted([table_name, to_table])
            create_sql, index_sqls = self._sync._build_m2m_junction_sql(  # noqa: SLF001
                junction_table,
                sorted_tables[0],
                sorted_tables[1],
            )
            await self._execute_sql(create_sql)

            for index_sql in index_sqls:
                with suppress(SqlExecutionError):
                    await self._execute_sql(index_sql)

    async def _execute_sql(self, sql: str) -> None:
        """Execute a raw SQL statement."""
        try:
            conn = await self.connect()
            cursor = await conn.cursor()
            await self._execute_async(cursor, sql)
            await self._maybe_commit()
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
        insert_plan = self._build_insert_plan(
            model_instance,
            timestamp_override=timestamp_override,
        )

        try:
            conn = await self.connect()
            cursor = await conn.cursor()
            await self._execute_async(
                cursor,
                insert_plan.sql,
                insert_plan.values,
            )
            await self._maybe_commit()
        except sqlite3.IntegrityError as exc:
            await self._maybe_rollback()
            if "FOREIGN KEY constraint failed" in str(exc):
                operation = "insert"
                reason = "does not exist in referenced table"
                raise ForeignKeyConstraintError(operation, reason) from exc
            raise RecordInsertionError(insert_plan.table_name) from exc
        except sqlite3.Error as exc:
            await self._maybe_rollback()
            raise RecordInsertionError(insert_plan.table_name) from exc
        else:
            self._cache_invalidate_table(insert_plan.table_name)
            insert_data = dict(insert_plan.data)
            insert_data.pop("pk", None)
            return self._create_instance_from_data(
                cast("type[T]", insert_plan.model_class),
                insert_data,
                pk=cursor.lastrowid,
            )

    async def _insert_single_record_async(
        self,
        model_instance: T,
        cursor: aiosqlite.Cursor,
        *,
        timestamp_override: bool,
    ) -> T:
        """Insert one record on a shared cursor without committing."""
        insert_plan = self._build_insert_plan(
            model_instance,
            timestamp_override=timestamp_override,
        )
        await self._execute_async(cursor, insert_plan.sql, insert_plan.values)

        insert_data = dict(insert_plan.data)
        insert_data.pop("pk", None)
        return self._create_instance_from_data(
            cast("type[T]", insert_plan.model_class),
            insert_data,
            pk=cursor.lastrowid,
        )

    async def bulk_insert(
        self,
        instances: Sequence[T],
        *,
        timestamp_override: bool = False,
    ) -> list[T]:
        """Insert multiple records in a single transaction."""
        prepared = self._sync.prepare_bulk_insert(instances)
        if prepared is None:
            return []

        _, table_name = prepared

        try:
            conn = await self.connect()
            cursor = await conn.cursor()
            results = [
                await self._insert_single_record_async(
                    inst,
                    cursor,
                    timestamp_override=timestamp_override,
                )
                for inst in instances
            ]
            await self._maybe_commit()
        except sqlite3.IntegrityError as exc:
            await self._maybe_rollback()
            if "FOREIGN KEY constraint failed" in str(exc):
                operation = "insert"
                reason = "does not exist in referenced table"
                raise ForeignKeyConstraintError(operation, reason) from exc
            raise RecordInsertionError(table_name) from exc
        except sqlite3.Error as exc:
            await self._maybe_rollback()
            raise RecordInsertionError(table_name) from exc
        else:
            self._cache_invalidate_table(table_name)
            return results

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

        cache_key = f"pk:{primary_key_value}"
        get_plan = self._build_get_plan(model_class, primary_key_value)

        if not bypass_cache:
            hit, cached = self._cache_get(get_plan.table_name, cache_key)
            if hit:
                return cast("Optional[T]", cached)

        try:
            conn = await self.connect()
            cursor = await conn.cursor()
            await self._execute_async(cursor, get_plan.sql, get_plan.values)
            result = await cursor.fetchone()
        except sqlite3.Error as exc:
            raise RecordFetchError(get_plan.table_name) from exc

        if result:
            result_dict = {
                field: result[idx]
                for idx, field in enumerate(model_class.model_fields)
            }
            instance = self._create_instance_from_data(model_class, result_dict)
            if not bypass_cache:
                self._cache_set(
                    get_plan.table_name,
                    cache_key,
                    instance,
                    ttl=cache_ttl,
                )
            return instance

        if not bypass_cache and cache_ttl is not None:
            # Negative cache entries are opt-in because invalidation is local
            # to this instance and cannot observe cross-process inserts.
            self._cache_set(
                get_plan.table_name,
                cache_key,
                None,
                ttl=cache_ttl,
            )
        return None

    async def update(self, model_instance: BaseDBModel) -> None:
        """Update an existing model instance."""
        update_plan = self._build_update_plan(model_instance)

        try:
            conn = await self.connect()
            cursor = await conn.cursor()
            await self._execute_async(
                cursor,
                update_plan.sql,
                update_plan.values,
            )

            if cursor.rowcount == 0:
                raise RecordNotFoundError(update_plan.primary_key_value)

            await self._maybe_commit()
            self._cache_invalidate_table(update_plan.table_name)
        except RecordNotFoundError:
            await self._maybe_rollback()
            raise
        except sqlite3.Error as exc:
            await self._maybe_rollback()
            raise RecordUpdateError(update_plan.table_name) from exc

    async def delete(
        self,
        model_class: type[BaseDBModel],
        primary_key_value: int | str,
    ) -> None:
        """Delete a record by primary key."""
        delete_plan = self._build_delete_plan(model_class, primary_key_value)

        try:
            conn = await self.connect()
            cursor = await conn.cursor()
            await self._execute_async(
                cursor,
                delete_plan.sql,
                delete_plan.values,
            )

            if cursor.rowcount == 0:
                raise RecordNotFoundError(delete_plan.primary_key_value)

            await self._maybe_commit()
            self._cache_invalidate_table(delete_plan.table_name)
        except RecordNotFoundError:
            await self._maybe_rollback()
            raise
        except sqlite3.IntegrityError as exc:
            await self._maybe_rollback()
            if "FOREIGN KEY constraint failed" in str(exc):
                operation = "delete"
                reason = "is still referenced by other records"
                raise ForeignKeyConstraintError(operation, reason) from exc
            raise RecordDeletionError(delete_plan.table_name) from exc
        except sqlite3.Error as exc:
            await self._maybe_rollback()
            raise RecordDeletionError(delete_plan.table_name) from exc

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
        self._sync.set_in_transaction(value=True)
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
                self._sync.set_in_transaction(value=False)
        self._sync.clear_cache()
        self._sync.reset_cache_stats()
