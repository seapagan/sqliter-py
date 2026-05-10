"""Async query execution for SQLiter."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING, Any, Generic, TypeVar, cast

from sqliter.exceptions import (
    InvalidProjectionError,
    InvalidUpdateError,
    RecordDeletionError,
    RecordFetchError,
    RecordUpdateError,
)
from sqliter.query.query import QueryBuilder, get_prefetch_target_model

if TYPE_CHECKING:  # pragma: no cover
    from sqliter.asyncio.db import AsyncSqliterDB
    from sqliter.model import BaseDBModel

T = TypeVar("T", bound="BaseDBModel")


class AsyncQueryBuilder(Generic[T]):
    """Async query builder with the same chain-building API as QueryBuilder."""

    def __init__(
        self,
        db: AsyncSqliterDB,
        model_class: type[T],
        fields: list[str] | None = None,
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
        order_by_field: str | None = None,
        direction: str | None = None,
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

    def fields(
        self,
        fields: list[str] | None = None,
    ) -> AsyncQueryBuilder[T]:
        """Specify which fields to select in the query."""
        self._query.fields(fields)
        return self

    def only(self, field: str) -> AsyncQueryBuilder[T]:
        """Include only a single field in the query."""
        self._query.only(field)
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

    def having(self, **conditions: Any) -> AsyncQueryBuilder[T]:  # noqa: ANN401
        """Apply HAVING filters to grouped/aggregate projection queries."""
        self._query.having(**conditions)
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

    def prefetch_related(self, *paths: str) -> AsyncQueryBuilder[T]:
        """Specify reverse FK or M2M relationships to prefetch."""
        self._query.prefetch_related(*paths)
        return self

    async def _execute_projection_query(self) -> list[tuple[Any, ...]]:
        """Execute a projection query and return raw rows."""
        sql, values, projection_columns = (
            self._query.build_projection_query_plan()
        )
        self._query.set_projection_columns(projection_columns)

        try:
            conn = await self.db.connect()
            cursor = await conn.cursor()
            await self.db.execute_cursor(cursor, sql, values)
            rows = await cursor.fetchall()
        except sqlite3.Error as exc:
            raise RecordFetchError(self.table_name) from exc
        else:
            return cast("list[tuple[Any, ...]]", rows)

    async def _fetch_projection_result(self) -> list[dict[str, Any]]:
        """Fetch projection rows as dictionaries with query caching."""
        if not self._query.projection_mode:
            msg = "fetch_dicts() requires projection mode."
            raise InvalidProjectionError(msg)

        hit, cached = self._query.lookup_cache(fetch_one=False)
        if hit:
            return cast("list[dict[str, Any]]", cached)

        rows = await self._execute_projection_query()
        results = [
            self._query.convert_projection_row_to_dict(row) for row in rows
        ]
        self._query.store_cache(results, fetch_one=False)
        return results

    async def _execute_query(
        self,
        *,
        fetch_one: bool = False,
        count_only: bool = False,
    ) -> tuple[
        list[tuple[Any, ...]] | tuple[Any, ...] | None,
        list[tuple[str, str, type[BaseDBModel]]],
        tuple[str, ...] | None,
    ]:
        """Execute the constructed SQL query."""
        plan = self._query.build_execution_plan(count_only=count_only)

        try:
            conn = await self.db.connect()
            cursor = await conn.cursor()
            await self.db.execute_cursor(cursor, plan.sql, plan.values)
            results = (
                await cursor.fetchone()
                if fetch_one
                else await cursor.fetchall()
            )
        except sqlite3.Error as exc:
            raise RecordFetchError(self.table_name) from exc
        else:
            return (
                cast("Any", results),
                plan.column_names,
                plan.selected_fields,
            )

    async def _fetch_result(
        self,
        *,
        fetch_one: bool = False,
    ) -> list[T] | T | None:
        """Fetch and convert query results to model instances."""
        hit, cached = self._query.lookup_cache(fetch_one=fetch_one)
        if hit:
            return cast("list[T] | T | None", cached)

        result, column_names, selected_fields = await self._execute_query(
            fetch_one=fetch_one
        )

        if not result:
            empty: list[T] | T | None = None if fetch_one else []
            self._query.store_cache(empty, fetch_one=fetch_one)
            return empty

        converted = self._query.convert_fetched_result(
            result,
            column_names,
            fetch_one=fetch_one,
            execute_prefetch=False,
            selected_fields=selected_fields,
        )
        await self._execute_prefetch(converted)
        self._query.store_cache(converted, fetch_one=fetch_one)
        return converted

    async def _prefetch_reverse_fk(
        self,
        path: str,
        descriptor: Any,  # noqa: ANN401
        instances: list[Any],
        pks: list[Any],
    ) -> None:
        """Prefetch reverse FK relationships."""
        fk_field = descriptor.fk_field
        related_model = descriptor.from_model
        pk_filter: list[Any] = list(pks)
        related_objects = await (
            self.db.select(related_model)
            .filter(**{f"{fk_field}_id__in": pk_filter})
            .fetch_all()
        )

        grouped: dict[int, list[Any]] = {pk: [] for pk in pks}
        for obj in related_objects:
            parent_pk = getattr(obj, f"{fk_field}_id", None)
            if parent_pk and parent_pk in grouped:
                grouped[parent_pk].append(obj)

        for inst in instances:
            self._query.store_prefetch_cache(
                inst,
                path,
                grouped.get(inst.pk or 0, []),
            )

    async def _query_junction_table(
        self,
        junction_table: str,
        columns: tuple[str, str, str, str],
        pks: list[int],
        *,
        symmetrical: bool,
    ) -> list[tuple[int, int]]:
        """Query a M2M junction table for related pairs."""
        conn = await self.db.connect()
        cursor = await conn.cursor()
        sql, values = self._query.build_m2m_junction_query(
            junction_table,
            columns,
            pks,
            symmetrical=symmetrical,
        )
        await self.db.execute_cursor(cursor, sql, values)
        rows = await cursor.fetchall()
        return cast("list[tuple[int, int]]", rows)

    async def _prefetch_m2m_for_model(
        self,
        path: str,
        descriptor: Any,  # noqa: ANN401
        instances: list[Any],
        pks: list[int],
        owner_model: type[BaseDBModel],
    ) -> None:
        """Prefetch M2M relationships for a given owner model."""
        resolved = self._query.resolve_m2m_columns(
            descriptor,
            owner_model.get_table_name(),
        )
        if resolved is None:
            return

        (
            target_model,
            junction_table,
            col_a,
            col_b,
            from_col,
            to_col,
            symmetrical,
        ) = resolved

        rows = await self._query_junction_table(
            junction_table,
            (col_a, col_b, from_col, to_col),
            pks,
            symmetrical=symmetrical,
        )
        parent_to_target, all_target_pks = self._query.build_m2m_mapping(
            rows,
            pks,
            symmetrical=symmetrical,
        )

        target_objects: dict[int, Any] = {}
        if all_target_pks:
            target_filter: list[Any] = list(all_target_pks)
            results = await (
                self.db.select(target_model)
                .filter(pk__in=target_filter)
                .fetch_all()
            )
            for obj in results:
                if obj.pk is not None:
                    target_objects[obj.pk] = obj

        for inst in instances:
            target_pks = parent_to_target.get(inst.pk or 0, [])
            related = [
                target_objects[tpk]
                for tpk in target_pks
                if tpk in target_objects
            ]
            self._query.store_prefetch_cache(inst, path, related)

    async def _prefetch_segment(
        self,
        segment: str,
        parent_instances: list[Any],
        current_model: type[BaseDBModel],
    ) -> None:
        """Run the prefetch query for a single relationship segment."""
        from sqliter.orm.m2m import (  # noqa: PLC0415
            ManyToMany,
            ReverseManyToMany,
        )
        from sqliter.orm.query import ReverseRelationship  # noqa: PLC0415

        parent_pks = self._query.collect_prefetch_parent_pks(
            parent_instances,
        )
        if not parent_pks:
            return

        descriptor = getattr(current_model, segment)

        if isinstance(descriptor, ReverseRelationship):
            await self._prefetch_reverse_fk(
                segment,
                descriptor,
                parent_instances,
                parent_pks,
            )
        elif isinstance(descriptor, (ManyToMany, ReverseManyToMany)):
            await self._prefetch_m2m_for_model(
                segment,
                descriptor,
                parent_instances,
                parent_pks,
                owner_model=current_model,
            )

    async def _execute_prefetch(
        self,
        instances: list[T] | T | None,
    ) -> None:
        """Run prefetch queries and populate caches on instances."""
        if instances is None or not self._query.prefetch_related_paths:
            return

        if not isinstance(instances, list):
            instance_list: list[Any] = [instances]
        else:
            instance_list = instances

        if not instance_list:
            return
        if not any(getattr(inst, "pk", None) for inst in instance_list):
            return

        levels = self._query.build_prefetch_levels(
            self._query.prefetch_related_paths,
        )

        instances_by_path: dict[str, list[Any]] = {"": list(instance_list)}
        model_at_path: dict[str, type[BaseDBModel]] = {"": self.model_class}

        max_depth = max(levels)
        for depth in range(max_depth + 1):
            for parent_path, segment in levels[depth]:
                parent_instances = instances_by_path.get(parent_path, [])
                if not parent_instances:
                    continue

                current_model = model_at_path[parent_path]
                await self._prefetch_segment(
                    segment,
                    parent_instances,
                    current_model,
                )

                full_path = (
                    f"{parent_path}__{segment}" if parent_path else segment
                )
                instances_by_path[full_path] = (
                    self._query.collect_prefetched_children(
                        parent_instances,
                        segment,
                    )
                )
                descriptor = getattr(current_model, segment)
                model_at_path[full_path] = get_prefetch_target_model(descriptor)

    async def fetch_all(self) -> list[T]:
        """Fetch all query results."""
        self._query.ensure_projection_method_allowed(
            "fetch_all",
            hint="Use fetch_dicts() instead.",
        )
        return cast("list[T]", await self._fetch_result(fetch_one=False))

    async def fetch_one(self) -> T | None:
        """Fetch a single query result."""
        self._query.ensure_projection_method_allowed(
            "fetch_one",
            hint="Use fetch_dicts() instead.",
        )
        return cast("T | None", await self._fetch_result(fetch_one=True))

    async def fetch_first(self) -> T | None:
        """Fetch the first query result."""
        self._query.ensure_projection_method_allowed(
            "fetch_first",
            hint="Use fetch_dicts() instead.",
        )
        self._query.prepare_fetch_first()
        return cast("T | None", await self._fetch_result(fetch_one=True))

    async def fetch_last(self) -> T | None:
        """Fetch the last query result."""
        self._query.ensure_projection_method_allowed(
            "fetch_last",
            hint="Use fetch_dicts() instead.",
        )
        self._query.prepare_fetch_last()
        return cast("T | None", await self._fetch_result(fetch_one=True))

    async def fetch_dicts(self) -> list[dict[str, Any]]:
        """Fetch projection rows as dictionaries."""
        return await self._fetch_projection_result()

    async def count(self) -> int:
        """Count rows matching the current query."""
        self._query.ensure_projection_method_allowed(
            "count",
            hint="Use len(fetch_dicts()) instead.",
        )
        result, _column_names, _selected_fields = await self._execute_query(
            count_only=True
        )
        row_list = cast("list[tuple[Any, ...]]", result)
        return int(row_list[0][0]) if row_list else 0

    async def exists(self) -> bool:
        """Return whether the query matches any rows."""
        self._query.ensure_projection_method_allowed(
            "exists",
            hint="Use len(fetch_dicts()) > 0 instead.",
        )
        return await self.count() > 0

    async def delete(self) -> int:
        """Delete rows matching the current query."""
        self._query.ensure_projection_method_allowed("delete")
        sql, values = self._query.build_delete_statement()

        try:
            conn = await self.db.connect()
            cursor = await conn.cursor()
            await self.db.execute_cursor(cursor, sql, values)
            deleted_count = int(cursor.rowcount)
            await self.db.maybe_commit()
            self.db.invalidate_table_cache(self.table_name)
        except sqlite3.Error as exc:
            if not self.db.in_transaction and self.db.conn is not None:
                await self.db.conn.rollback()
            raise RecordDeletionError(self.table_name) from exc
        else:
            return deleted_count

    async def update(self, values: dict[str, Any]) -> int:
        """Update rows matching the current query."""
        self._query.ensure_projection_method_allowed("update")
        if not values:
            return 0

        pk_field = self.model_class.get_primary_key()
        if pk_field in values:
            msg = f"Cannot update the primary key '{pk_field}' via bulk update"
            raise InvalidUpdateError(msg)

        valid_fields = set(self.model_class.model_fields.keys())
        invalid_fields = set(values.keys()) - valid_fields
        if invalid_fields:
            invalid_names = ", ".join(sorted(invalid_fields))
            raise InvalidUpdateError(invalid_names)

        sql, all_values = self._query.build_update_statement(
            values,
            current_timestamp=self.db.now(),
        )

        try:
            conn = await self.db.connect()
            cursor = await conn.cursor()
            await self.db.execute_cursor(cursor, sql, all_values)
            updated_count = int(cursor.rowcount)
            await self.db.maybe_commit()
            self.db.invalidate_table_cache(self.table_name)
        except sqlite3.Error as exc:
            if not self.db.in_transaction and self.db.conn is not None:
                await self.db.conn.rollback()
            raise RecordUpdateError(self.table_name) from exc
        else:
            return updated_count
