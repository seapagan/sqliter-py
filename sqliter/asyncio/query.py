"""Async query execution for SQLiter."""

from __future__ import annotations

import re
import sqlite3
from typing import TYPE_CHECKING, Any, Generic, Optional, TypeVar, cast

from sqliter.exceptions import (
    InvalidProjectionError,
    RecordDeletionError,
    RecordFetchError,
    RecordUpdateError,
)
from sqliter.query.query import QueryBuilder

if TYPE_CHECKING:  # pragma: no cover
    from sqliter.asyncio.db import AsyncSqliterDB
    from sqliter.model import BaseDBModel

T = TypeVar("T", bound="BaseDBModel")


class AsyncQueryBuilder(Generic[T]):
    """Async wrapper around SQLiter's sync query-building logic."""

    def __init__(
        self,
        db: AsyncSqliterDB,
        model_class: type[T],
        fields: Optional[list[str]] = None,
    ) -> None:
        """Initialize the async query builder."""
        self.db = db
        self._query = QueryBuilder(cast("Any", db), model_class, fields)

    @property
    def model_class(self) -> type[T]:
        """Return the model class for this query."""
        return self._query.model_class

    @property
    def table_name(self) -> str:
        """Return the table name for this query."""
        return self._query.table_name

    def filter(self, **conditions: Any) -> AsyncQueryBuilder[T]:  # noqa: ANN401
        """Apply filter conditions to the query."""
        self._query.filter(**conditions)
        return self

    def limit(self, limit_value: int) -> AsyncQueryBuilder[T]:
        """Limit the number of rows returned."""
        self._query.limit(limit_value)
        return self

    def offset(self, offset_value: int) -> AsyncQueryBuilder[T]:
        """Set the row offset for the query."""
        self._query.offset(offset_value)
        return self

    def order(
        self,
        order_by_field: Optional[str] = None,
        direction: Optional[str] = None,
        *,
        reverse: bool = False,
    ) -> AsyncQueryBuilder[T]:
        """Order the query results."""
        self._query.order(
            order_by_field,
            direction,
            reverse=reverse,
        )
        return self

    def exclude(self, fields: list[str]) -> AsyncQueryBuilder[T]:
        """Exclude fields from the query."""
        self._query.exclude(fields)
        return self

    def only(self, *fields: str) -> AsyncQueryBuilder[T]:
        """Include only specific fields in the query."""
        self._query.only(*fields)
        return self

    def bypass_cache(self) -> AsyncQueryBuilder[T]:
        """Bypass the cache for this query."""
        self._query.bypass_cache()
        return self

    def cache_ttl(self, ttl: int) -> AsyncQueryBuilder[T]:
        """Set a custom TTL for the query cache entry."""
        self._query.cache_ttl(ttl)
        return self

    def group_by(self, *fields: str) -> AsyncQueryBuilder[T]:
        """Enable projection mode with GROUP BY fields."""
        self._query.group_by(*fields)
        return self

    def annotate(self, **aggregates: Any) -> AsyncQueryBuilder[T]:  # noqa: ANN401
        """Add aggregate projections to the query."""
        self._query.annotate(**aggregates)
        return self

    def with_count(
        self,
        path: str,
        alias: str = "count",
        *,
        distinct: bool = False,
    ) -> AsyncQueryBuilder[T]:
        """Add a relationship count projection."""
        self._query.with_count(path, alias=alias, distinct=distinct)
        return self

    def select_related(self, *paths: str) -> AsyncQueryBuilder[T]:
        """Eager-load forward FK relationships via JOIN."""
        self._query.select_related(*paths)
        return self

    async def _execute_projection_query(self) -> list[tuple[Any, ...]]:
        """Execute a projection query and return raw rows."""
        sql, values, projection_columns = self._query._build_projection_sql()
        self._query._projection_columns = projection_columns

        try:
            conn = await self.db.connect()
            cursor = await conn.cursor()
            await self.db._execute_async(cursor, sql, values)
            rows = await cursor.fetchall()
        except sqlite3.Error as exc:
            raise RecordFetchError(self.table_name) from exc
        else:
            return cast("list[tuple[Any, ...]]", rows)

    async def _fetch_projection_result(self) -> list[dict[str, Any]]:
        """Fetch projection rows as dictionaries with query caching."""
        if not self._query._projection_mode:
            msg = "fetch_dicts() requires projection mode."
            raise InvalidProjectionError(msg)

        cache_key: Optional[str] = None
        if not self._query._bypass_cache:
            cache_key = self._query._make_cache_key(fetch_one=False)
            hit, cached = self.db._cache_get(self.table_name, cache_key)
            if hit:
                return cast("list[dict[str, Any]]", cached)

        rows = await self._execute_projection_query()
        results = [
            self._query._convert_projection_row_to_dict(row) for row in rows
        ]

        if not self._query._bypass_cache and cache_key is not None:
            self.db._cache_set(
                self.table_name,
                cache_key,
                results,
                ttl=self._query._query_cache_ttl,
            )

        return results

    async def _execute_query(
        self,
        *,
        fetch_one: bool = False,
        count_only: bool = False,
    ) -> tuple[
        list[tuple[Any, ...]] | tuple[Any, ...] | None,
        list[tuple[str, str, type[BaseDBModel]]],
    ]:
        """Execute the constructed SQL query."""
        needs_join_for_filters = False
        if self._query._join_info and (count_only or self._query._fields):
            _values, where_clause = self._query._parse_filter()
            if re.search(r"\bt\d+\.", where_clause):
                needs_join_for_filters = True

        if self._query._join_info and (
            not (count_only or self._query._fields) or needs_join_for_filters
        ):
            join_clause, select_clause, column_names = (
                self._query._build_join_sql()
            )

            if count_only and needs_join_for_filters:
                sql = (
                    f'SELECT COUNT(*) FROM "{self.table_name}" AS t0 '
                    f"{join_clause}"
                )
            elif self._query._fields:
                field_list = ", ".join(
                    self._query._column_sql(field, table_alias="t0")
                    for field in self._query._fields
                )
                sql = (
                    f'SELECT {field_list} FROM "{self.table_name}" AS t0 '
                    f"{join_clause}"
                )
                column_names = [
                    ("t0", field, self.model_class)
                    for field in self._query._fields
                ]
            else:
                sql = (
                    f'SELECT {select_clause} FROM "{self.table_name}" AS t0 '
                    f"{join_clause}"
                )

            values, where_clause = self._query._parse_filter(
                qualify_base_fields=True
            )

            if self._query.filters:
                sql += f" WHERE {where_clause}"

            if self._query._order_by:
                match = re.match(r'"([^"]+)"\s+(.*)', self._query._order_by)
                if match:
                    field_name = match.group(1)
                    direction = match.group(2)
                    field_sql = self._query._column_sql(
                        field_name,
                        table_alias="t0",
                    )
                    sql += f" ORDER BY {field_sql} {direction}"
                elif self._query._order_by.lower().startswith("rowid"):
                    sql += f" ORDER BY t0.{self._query._order_by}"

            if self._query._limit is not None:
                sql += " LIMIT ?"
                values.append(self._query._limit)

            if self._query._offset is not None:
                sql += " OFFSET ?"
                values.append(self._query._offset)

            try:
                conn = await self.db.connect()
                cursor = await conn.cursor()
                await self.db._execute_async(cursor, sql, values)
                results = (
                    await cursor.fetchone()
                    if fetch_one
                    else await cursor.fetchall()
                )
            except sqlite3.Error as exc:
                raise RecordFetchError(self.table_name) from exc
            else:
                return (cast("Any", results), column_names)

        if count_only:
            fields = "COUNT(*)"
        elif self._query._fields:
            if "pk" not in self._query._fields:
                self._query._fields.append("pk")
            fields = ", ".join(
                self._query._column_sql(field) for field in self._query._fields
            )
        else:
            fields = ", ".join(
                self._query._column_sql(field)
                for field in self.model_class.model_fields
            )

        sql = f'SELECT {fields} FROM "{self.table_name}"'
        values, where_clause = self._query._parse_filter()

        if self._query.filters:
            sql += f" WHERE {where_clause}"

        if self._query._order_by:
            match = re.match(r'"([^"]+)"\s+(ASC|DESC)', self._query._order_by)
            if match:
                field_name = match.group(1)
                direction = match.group(2)
                field_sql = self._query._column_sql(field_name)
                sql += f" ORDER BY {field_sql} {direction}"
            else:
                sql += f" ORDER BY {self._query._order_by}"

        if self._query._limit is not None:
            sql += " LIMIT ?"
            values.append(self._query._limit)

        if self._query._offset is not None:
            sql += " OFFSET ?"
            values.append(self._query._offset)

        try:
            conn = await self.db.connect()
            cursor = await conn.cursor()
            await self.db._execute_async(cursor, sql, values)
            if fetch_one:
                results = await cursor.fetchone()
            else:
                results = await cursor.fetchall()
        except sqlite3.Error as exc:
            raise RecordFetchError(self.table_name) from exc
        else:
            return (cast("Any", results), [])

    async def _fetch_result(
        self,
        *,
        fetch_one: bool = False,
    ) -> list[T] | Optional[T]:
        """Fetch and convert query results to model instances."""
        if not self._query._bypass_cache:
            cache_key = self._query._make_cache_key(fetch_one=fetch_one)
            hit, cached = self.db._cache_get(self.table_name, cache_key)
            if hit:
                return cast("list[T] | Optional[T]", cached)

        result, column_names = await self._execute_query(fetch_one=fetch_one)

        if not result:
            if not self._query._bypass_cache:
                cache_key = self._query._make_cache_key(fetch_one=fetch_one)
                if fetch_one:
                    self.db._cache_set(
                        self.table_name,
                        cache_key,
                        None,
                        ttl=self._query._query_cache_ttl,
                    )
                    return None
                self.db._cache_set(
                    self.table_name,
                    cache_key,
                    [],
                    ttl=self._query._query_cache_ttl,
                )
                return []
            return None if fetch_one else []

        if column_names:
            if fetch_one:
                single_row = cast("tuple[Any, ...]", result)
                single_result = self._query._convert_joined_row_to_model(
                    single_row,
                    column_names,
                )
                if not self._query._bypass_cache:
                    cache_key = self._query._make_cache_key(fetch_one=True)
                    self.db._cache_set(
                        self.table_name,
                        cache_key,
                        single_result,
                        ttl=self._query._query_cache_ttl,
                    )
                return single_result

            row_list = cast("list[tuple[Any, ...]]", result)
            list_results = [
                self._query._convert_joined_row_to_model(row, column_names)
                for row in row_list
            ]
            if not self._query._bypass_cache:
                cache_key = self._query._make_cache_key(fetch_one=False)
                self.db._cache_set(
                    self.table_name,
                    cache_key,
                    list_results,
                    ttl=self._query._query_cache_ttl,
                )
            return list_results

        if fetch_one:
            std_single_row = cast("tuple[Any, ...]", result)
            single_result = self._query._convert_row_to_model(std_single_row)
            if not self._query._bypass_cache:
                cache_key = self._query._make_cache_key(fetch_one=True)
                self.db._cache_set(
                    self.table_name,
                    cache_key,
                    single_result,
                    ttl=self._query._query_cache_ttl,
                )
            return single_result

        std_row_list = cast("list[tuple[Any, ...]]", result)
        list_results = [
            self._query._convert_row_to_model(row) for row in std_row_list
        ]
        if not self._query._bypass_cache:
            cache_key = self._query._make_cache_key(fetch_one=False)
            self.db._cache_set(
                self.table_name,
                cache_key,
                list_results,
                ttl=self._query._query_cache_ttl,
            )
        return list_results

    async def fetch_all(self) -> list[T]:
        """Fetch all query results."""
        self._query._ensure_projection_method_allowed(
            "fetch_all",
            hint="Use fetch_dicts() instead.",
        )
        return cast("list[T]", await self._fetch_result(fetch_one=False))

    async def fetch_one(self) -> Optional[T]:
        """Fetch a single query result."""
        self._query._ensure_projection_method_allowed(
            "fetch_one",
            hint="Use fetch_dicts() instead.",
        )
        return cast("Optional[T]", await self._fetch_result(fetch_one=True))

    async def fetch_first(self) -> Optional[T]:
        """Fetch the first query result."""
        self._query._ensure_projection_method_allowed(
            "fetch_first",
            hint="Use fetch_dicts() instead.",
        )
        self._query._limit = 1
        return cast("Optional[T]", await self._fetch_result(fetch_one=True))

    async def fetch_last(self) -> Optional[T]:
        """Fetch the last query result."""
        self._query._ensure_projection_method_allowed(
            "fetch_last",
            hint="Use fetch_dicts() instead.",
        )
        self._query._limit = 1
        self._query._order_by = "rowid DESC"
        return cast("Optional[T]", await self._fetch_result(fetch_one=True))

    async def fetch_dicts(self) -> list[dict[str, Any]]:
        """Fetch projection rows as dictionaries."""
        return await self._fetch_projection_result()

    async def count(self) -> int:
        """Count rows matching the current query."""
        self._query._ensure_projection_method_allowed(
            "count",
            hint="Use len(fetch_dicts()) instead.",
        )
        result, _column_names = await self._execute_query(count_only=True)
        row_list = cast("list[tuple[Any, ...]]", result)
        return int(row_list[0][0]) if row_list else 0

    async def exists(self) -> bool:
        """Return whether the query matches any rows."""
        self._query._ensure_projection_method_allowed(
            "exists",
            hint="Use len(fetch_dicts()) > 0 instead.",
        )
        return await self.count() > 0

    async def delete(self) -> int:
        """Delete rows matching the current query."""
        self._query._ensure_projection_method_allowed("delete")
        sql = f'DELETE FROM "{self.table_name}"'
        values, where_clause = self._query._parse_filter()

        if self._query.filters:
            sql += f" WHERE {where_clause}"

        try:
            conn = await self.db.connect()
            cursor = await conn.cursor()
            await self.db._execute_async(cursor, sql, values)
            deleted_count = int(cursor.rowcount)
            await self.db.maybe_commit()
            self.db._cache_invalidate_table(self.table_name)
        except sqlite3.Error as exc:
            if not self.db.in_transaction and self.db.conn is not None:
                await self.db.conn.rollback()
            raise RecordDeletionError(self.table_name) from exc
        else:
            return deleted_count

    async def update(self, values: dict[str, Any]) -> int:
        """Update rows matching the current query."""
        self._query._ensure_projection_method_allowed("update")
        if not values:
            return 0

        pk_field = self.model_class.get_primary_key()
        if pk_field in values:
            msg = f"Cannot update the primary key '{pk_field}' via bulk update"
            raise RecordUpdateError(msg)

        valid_fields = set(self.model_class.model_fields.keys())
        invalid_fields = set(values.keys()) - valid_fields
        if invalid_fields:
            invalid_names = ", ".join(sorted(invalid_fields))
            raise RecordUpdateError(invalid_names)

        set_clauses: list[str] = []
        set_values: list[Any] = []

        if "updated_at" in valid_fields and "updated_at" not in values:
            set_clauses.append('"updated_at" = ?')
            set_values.append(self.db.now())

        for field_name, value in values.items():
            serialized = self.model_class.serialize_field(value)
            db_column = self.db._model_field_to_db_column(
                self.model_class,
                field_name,
            )
            set_clauses.append(f'"{db_column}" = ?')
            set_values.append(serialized)

        sql = f'UPDATE "{self.table_name}" SET {", ".join(set_clauses)}'
        where_values, where_clause = self._query._parse_filter()
        if self._query.filters:
            sql += f" WHERE {where_clause}"
        all_values = set_values + where_values

        try:
            conn = await self.db.connect()
            cursor = await conn.cursor()
            await self.db._execute_async(cursor, sql, all_values)
            updated_count = int(cursor.rowcount)
            await self.db.maybe_commit()
            self.db._cache_invalidate_table(self.table_name)
        except sqlite3.Error as exc:
            if not self.db.in_transaction and self.db.conn is not None:
                await self.db.conn.rollback()
            raise RecordUpdateError(self.table_name) from exc
        else:
            return updated_count
