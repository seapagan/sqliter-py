"""Async many-to-many ORM helpers."""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Optional,
    Protocol,
    TypeVar,
    Union,
    cast,
    overload,
    runtime_checkable,
)

from sqliter.exceptions import ManyToManyIntegrityError
from sqliter.orm.m2m import (
    M2MSQLMetadata,
    ManyToManyManager,
    ManyToManyOptions,
    PrefetchedM2MResult,
    _build_m2m_sql_metadata,
)
from sqliter.orm.m2m import (
    ManyToMany as SyncManyToMany,
)
from sqliter.orm.m2m import (
    ReverseManyToMany as SyncReverseManyToMany,
)

if TYPE_CHECKING:  # pragma: no cover
    from sqliter.asyncio.db import AsyncSqliterDB
    from sqliter.asyncio.query import AsyncQueryBuilder
    from sqliter.model.model import BaseDBModel
    from sqliter.query.query import FilterValue

T = TypeVar("T")


@runtime_checkable
class HasPKAndContext(Protocol):
    """Protocol for instances with pk and async db_context."""

    pk: Optional[int]
    db_context: Optional[Any]


class AsyncManyToManyManager(Generic[T]):
    """Async manager for M2M relationships."""

    def __init__(
        self,
        instance: HasPKAndContext,
        to_model: type[T],
        from_model: type[Any],
        junction_table: str,
        db_context: Optional[AsyncSqliterDB],
        options: Optional[ManyToManyOptions] = None,
    ) -> None:
        """Store manager state and resolved SQL metadata."""
        manager_options = options or ManyToManyOptions()
        self._instance = instance
        self._to_model = to_model
        self._from_model = from_model
        self._junction_table = junction_table
        self._db = db_context

        from_table = cast("type[BaseDBModel]", from_model).get_table_name()
        to_table = cast("type[BaseDBModel]", to_model).get_table_name()
        self._sql_metadata = _build_m2m_sql_metadata(
            source_table=from_table,
            target_table=to_table,
            junction_table=junction_table,
            symmetrical=manager_options.symmetrical,
            swap_columns=manager_options.swap_columns,
        )
        self._from_col = self._sql_metadata.from_column
        self._to_col = self._sql_metadata.to_column

    @property
    def sql_metadata(self) -> M2MSQLMetadata:
        """Return read-only SQL metadata."""
        return self._sql_metadata

    def _select_related_ids_sql(self) -> str:
        if self._sql_metadata.symmetrical:
            return " ".join(
                (
                    "SELECT CASE WHEN",
                    f'"{self._from_col}" = ?',
                    "THEN",
                    f'"{self._to_col}"',
                    "ELSE",
                    f'"{self._from_col}"',
                    "END",
                    "FROM",
                    f'"{self._junction_table}"',
                    "WHERE",
                    f'"{self._from_col}" = ?',
                    "OR",
                    f'"{self._to_col}" = ?',
                )
            )
        return " ".join(
            (
                "SELECT",
                f'"{self._to_col}"',
                "FROM",
                f'"{self._junction_table}"',
                "WHERE",
                f'"{self._from_col}" = ?',
            )
        )

    def _insert_sql(self) -> str:
        return " ".join(
            (
                "INSERT OR IGNORE INTO",
                f'"{self._junction_table}"',
                f'("{self._from_col}", "{self._to_col}")',
                "VALUES (?, ?)",
            )
        )

    def _delete_pair_sql(self) -> str:
        return " ".join(
            (
                "DELETE FROM",
                f'"{self._junction_table}"',
                "WHERE",
                f'"{self._from_col}" = ?',
                "AND",
                f'"{self._to_col}" = ?',
            )
        )

    def _clear_sql(self) -> tuple[str, tuple[int, ...]]:
        from_pk = self._get_instance_pk()
        if self._sql_metadata.symmetrical:
            return (
                " ".join(
                    (
                        "DELETE FROM",
                        f'"{self._junction_table}"',
                        "WHERE",
                        f'"{self._from_col}" = ?',
                        "OR",
                        f'"{self._to_col}" = ?',
                    )
                ),
                (from_pk, from_pk),
            )
        return (
            " ".join(
                (
                    "DELETE FROM",
                    f'"{self._junction_table}"',
                    "WHERE",
                    f'"{self._from_col}" = ?',
                )
            ),
            (from_pk,),
        )

    def _count_sql(self) -> str:
        if self._sql_metadata.symmetrical:
            return " ".join(
                (
                    "SELECT COUNT(*) FROM",
                    f'"{self._junction_table}"',
                    "WHERE",
                    f'"{self._from_col}" = ?',
                    "OR",
                    f'"{self._to_col}" = ?',
                )
            )
        return " ".join(
            (
                "SELECT COUNT(*) FROM",
                f'"{self._junction_table}"',
                "WHERE",
                f'"{self._from_col}" = ?',
            )
        )

    def _check_context(self) -> AsyncSqliterDB:
        if self._db is None:
            msg = (
                "No database context available. "
                "Insert the instance first or use within a db context."
            )
            raise ManyToManyIntegrityError(msg)
        pk = getattr(self._instance, "pk", None)
        if not pk:
            msg = (
                "Instance has no primary key. "
                "Insert the instance before managing relationships."
            )
            raise ManyToManyIntegrityError(msg)
        return self._db

    async def _rollback_if_needed(self, db: AsyncSqliterDB) -> None:
        if not db.in_transaction and db.conn is not None:
            await db.conn.rollback()

    @staticmethod
    def _raise_missing_pk() -> None:
        msg = (
            "Related instance has no primary key. "
            "Insert it before adding to a relationship."
        )
        raise ManyToManyIntegrityError(msg)

    def _get_instance_pk(self) -> int:
        pk = self._instance.pk
        if pk is None:
            msg = (
                "Instance has no primary key. "
                "Insert the instance before managing relationships."
            )
            raise ManyToManyIntegrityError(msg)
        return int(pk)

    async def _fetch_related_pks(self) -> list[int]:
        if self._db is None:
            return []
        pk = getattr(self._instance, "pk", None)
        if not pk:
            return []

        conn = await self._db.connect()
        cursor = await conn.cursor()
        sql = self._select_related_ids_sql()
        params = (pk, pk, pk) if self._sql_metadata.symmetrical else (pk,)
        await self._db.execute_cursor(cursor, sql, params)
        return [row[0] for row in await cursor.fetchall()]

    async def add(self, *instances: T) -> None:
        """Add related objects."""
        db = self._check_context()
        from_pk = self._get_instance_pk()
        sql = self._insert_sql()

        conn = await db.connect()
        cursor = await conn.cursor()
        try:
            for inst in instances:
                to_pk = getattr(inst, "pk", None)
                if not to_pk:
                    self._raise_missing_pk()
                to_pk = cast("int", to_pk)
                if self._sql_metadata.symmetrical:
                    left_pk, right_pk = sorted([from_pk, to_pk])
                    await db.execute_cursor(cursor, sql, (left_pk, right_pk))
                else:
                    await db.execute_cursor(cursor, sql, (from_pk, to_pk))
        except Exception:
            await self._rollback_if_needed(db)
            raise

        await db.maybe_commit()

    async def remove(self, *instances: T) -> None:
        """Remove related objects."""
        db = self._check_context()
        from_pk = self._get_instance_pk()
        sql = self._delete_pair_sql()

        conn = await db.connect()
        cursor = await conn.cursor()
        try:
            for inst in instances:
                to_pk = getattr(inst, "pk", None)
                if not to_pk:
                    continue
                to_pk = cast("int", to_pk)
                if self._sql_metadata.symmetrical:
                    left_pk, right_pk = sorted([from_pk, to_pk])
                    await db.execute_cursor(cursor, sql, (left_pk, right_pk))
                else:
                    await db.execute_cursor(cursor, sql, (from_pk, to_pk))
        except Exception:
            await self._rollback_if_needed(db)
            raise

        await db.maybe_commit()

    async def clear(self) -> None:
        """Remove all related objects for this instance."""
        db = self._check_context()
        sql, params = self._clear_sql()

        conn = await db.connect()
        cursor = await conn.cursor()
        try:
            await db.execute_cursor(cursor, sql, params)
        except Exception:
            await self._rollback_if_needed(db)
            raise
        await db.maybe_commit()

    async def set(self, *instances: T) -> None:
        """Replace all related objects."""
        db = self._check_context()
        for inst in instances:
            if not getattr(inst, "pk", None):
                self._raise_missing_pk()

        async with db:
            await self.clear()
            if instances:
                await self.add(*instances)

    async def fetch_all(self) -> list[T]:
        """Fetch all related objects."""
        pks = await self._fetch_related_pks()
        if not pks or self._db is None:
            return []

        model = cast("type[BaseDBModel]", self._to_model)
        return cast(
            "list[T]",
            await self._db.select(model).filter(pk__in=list(pks)).fetch_all(),
        )

    async def fetch_one(self) -> Optional[T]:
        """Fetch one related object."""
        pks = await self._fetch_related_pks()
        if not pks or self._db is None:
            return None

        model = cast("type[BaseDBModel]", self._to_model)
        results = await (
            self._db.select(model).filter(pk__in=list(pks)).limit(1).fetch_all()
        )
        return cast("Optional[T]", results[0]) if results else None

    async def count(self) -> int:
        """Count related objects via the junction table."""
        if self._db is None:
            return 0
        pk = getattr(self._instance, "pk", None)
        if not pk:
            return 0

        conn = await self._db.connect()
        cursor = await conn.cursor()
        sql = self._count_sql()
        params = (pk, pk) if self._sql_metadata.symmetrical else (pk,)
        await self._db.execute_cursor(cursor, sql, params)
        row = await cursor.fetchone()
        return int(row[0]) if row else 0

    async def exists(self) -> bool:
        """Return whether any related objects exist."""
        return await self.count() > 0

    async def filter(self, **kwargs: FilterValue) -> AsyncQueryBuilder[Any]:
        """Return an async query builder filtered to related objects."""
        db = self._check_context()
        model = cast("type[BaseDBModel]", self._to_model)
        pks = await self._fetch_related_pks()
        if not pks:
            return db.select(model).filter(pk__in=[-1], **kwargs)
        return db.select(model).filter(pk__in=list(pks), **kwargs)


class AsyncPrefetchedM2MResult(Generic[T]):
    """Wrapper around prefetched async M2M data."""

    def __init__(
        self,
        cached_items: list[T],
        manager: AsyncManyToManyManager[T],
    ) -> None:
        """Store prefetched items and a real manager for writes."""
        self._items = cached_items
        self._manager = manager

    @property
    def sql_metadata(self) -> M2MSQLMetadata:
        """Return read-only SQL metadata."""
        return self._manager.sql_metadata

    async def fetch_all(self) -> list[T]:
        """Return all prefetched related objects."""
        return list(self._items)

    async def fetch_one(self) -> Optional[T]:
        """Return one prefetched related object."""
        return self._items[0] if self._items else None

    async def count(self) -> int:
        """Count prefetched related objects."""
        return len(self._items)

    async def exists(self) -> bool:
        """Return whether any prefetched related objects exist."""
        return len(self._items) > 0

    async def filter(
        self,
        **kwargs: FilterValue,
    ) -> AsyncQueryBuilder[Any]:
        """Fall back to a real async query for filtered results."""
        return await self._manager.filter(**kwargs)

    async def add(self, *instances: T) -> None:
        """Delegate add."""
        await self._manager.add(*instances)
        self._items = await self._manager.fetch_all()

    async def remove(self, *instances: T) -> None:
        """Delegate remove."""
        await self._manager.remove(*instances)
        self._items = await self._manager.fetch_all()

    async def clear(self) -> None:
        """Delegate clear."""
        await self._manager.clear()
        self._items = await self._manager.fetch_all()

    async def set(self, *instances: T) -> None:
        """Delegate set."""
        await self._manager.set(*instances)
        self._items = await self._manager.fetch_all()


class AsyncManyToMany(SyncManyToMany[T]):
    """Async M2M descriptor returning async managers."""

    def __set_name__(self, owner: type, name: str) -> None:
        """Register M2M and replace existing reverse accessors."""
        super().__set_name__(owner, name)
        if (
            not isinstance(self.to_model, str)
            and self.related_name
            and hasattr(self.to_model, self.related_name)
        ):
            setattr(
                self.to_model,
                self.related_name,
                AsyncReverseManyToMany(
                    from_model=owner,
                    to_model=self.to_model,
                    junction_table=self._junction_table or "",
                    related_name=self.related_name,
                    symmetrical=self.m2m_info.symmetrical,
                ),
            )

    @overload
    def __get__(
        self,
        instance: None,
        owner: type[object],
    ) -> SyncManyToMany[T]: ...

    @overload
    def __get__(
        self,
        instance: object,
        owner: type[object],
    ) -> Union[
        ManyToManyManager[T],
        PrefetchedM2MResult[T],
    ]: ...

    def __get__(
        self,
        instance: object | None,
        owner: type[object],
    ) -> Union[
        SyncManyToMany[T],
        ManyToManyManager[T],
        PrefetchedM2MResult[T],
    ]:
        """Return an async manager or prefetched wrapper."""
        if instance is None:
            return self

        if isinstance(self.to_model, str):
            msg = (
                "ManyToMany target model is unresolved. "
                "Define the target model class before "
                "accessing the relationship."
            )
            raise TypeError(msg)

        manager = AsyncManyToManyManager(
            instance=cast("HasPKAndContext", instance),
            to_model=self.to_model,
            from_model=owner,
            junction_table=self._junction_table or "",
            db_context=getattr(instance, "db_context", None),
            options=ManyToManyOptions(symmetrical=self.m2m_info.symmetrical),
        )
        cache = getattr(instance, "__dict__", {}).get("_prefetch_cache", {})
        if self.name and self.name in cache:
            return cast(
                "PrefetchedM2MResult[T]",
                AsyncPrefetchedM2MResult(cache[self.name], manager),
            )
        return cast("ManyToManyManager[T]", manager)


class AsyncReverseManyToMany(SyncReverseManyToMany):
    """Async reverse M2M descriptor."""

    @overload
    def __get__(
        self,
        instance: None,
        owner: type[object],
    ) -> SyncReverseManyToMany: ...

    @overload
    def __get__(
        self,
        instance: object,
        owner: type[object],
    ) -> Union[
        ManyToManyManager[Any],
        PrefetchedM2MResult[Any],
    ]: ...

    def __get__(
        self,
        instance: object | None,
        owner: type[object],
    ) -> Union[
        SyncReverseManyToMany,
        ManyToManyManager[Any],
        PrefetchedM2MResult[Any],
    ]:
        """Return an async manager or prefetched wrapper."""
        if instance is None:
            return self

        manager = AsyncManyToManyManager(
            instance=cast("HasPKAndContext", instance),
            to_model=self._from_model,
            from_model=self._to_model,
            junction_table=self._junction_table,
            db_context=getattr(instance, "db_context", None),
            options=ManyToManyOptions(
                symmetrical=self._symmetrical,
                swap_columns=self._swap_columns,
            ),
        )
        cache = getattr(instance, "__dict__", {}).get("_prefetch_cache", {})
        if self._related_name in cache:
            return cast(
                "PrefetchedM2MResult[Any]",
                AsyncPrefetchedM2MResult(cache[self._related_name], manager),
            )
        return cast("ManyToManyManager[Any]", manager)
