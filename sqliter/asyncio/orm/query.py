"""Async reverse-relationship query helpers."""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Optional,
    Protocol,
    Union,
    cast,
    overload,
    runtime_checkable,
)

from sqliter.orm.query import HasPKAndContext as SyncHasPKAndContext
from sqliter.orm.query import PrefetchedResult, ReverseQuery
from sqliter.orm.query import ReverseRelationship as SyncReverseRelationship

if TYPE_CHECKING:  # pragma: no cover
    from sqliter.asyncio.db import AsyncSqliterDB
    from sqliter.asyncio.query import AsyncQueryBuilder
    from sqliter.model.model import BaseDBModel
    from sqliter.query.query import FilterValue


@runtime_checkable
class HasPKAndContext(Protocol):
    """Protocol for model instances with pk and async db_context."""

    pk: Optional[int]
    db_context: Optional[AsyncSqliterDB]


class AsyncPrefetchedResult:
    """Wrapper around prefetched reverse-FK data."""

    def __init__(
        self,
        cached_items: list[BaseDBModel],
        instance: HasPKAndContext,
        to_model: type[BaseDBModel],
        fk_field: str,
        db_context: Optional[AsyncSqliterDB],
    ) -> None:
        """Store prefetched instances and async fallback context."""
        self._items = cached_items
        self._instance = instance
        self._to_model = to_model
        self._fk_field = fk_field
        self._db = db_context

    async def fetch_all(self) -> list[BaseDBModel]:
        """Return all prefetched related instances."""
        return list(self._items)

    async def fetch_one(self) -> Optional[BaseDBModel]:
        """Return the first prefetched related instance."""
        return self._items[0] if self._items else None

    async def count(self) -> int:
        """Return the count of prefetched related instances."""
        return len(self._items)

    async def exists(self) -> bool:
        """Return whether any prefetched related instances exist."""
        return len(self._items) > 0

    def filter(self, **kwargs: FilterValue) -> AsyncReverseQuery:
        """Fall back to a real async query for filtered results."""
        return AsyncReverseQuery(
            instance=self._instance,
            to_model=self._to_model,
            fk_field=self._fk_field,
            db_context=self._db,
        ).filter(**kwargs)


class AsyncReverseQuery:
    """Async query builder for reverse relationships."""

    def __init__(
        self,
        instance: HasPKAndContext,
        to_model: type[BaseDBModel],
        fk_field: str,
        db_context: Optional[AsyncSqliterDB],
    ) -> None:
        """Store reverse-query state for later async execution."""
        self.instance = instance
        self.to_model = to_model
        self.fk_field = fk_field
        self._db = db_context
        self._filters: dict[str, FilterValue] = {}
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None

    @property
    def fk_value(self) -> Optional[int]:
        """Return the parent primary key value."""
        return self.instance.pk

    def filter(self, **kwargs: FilterValue) -> AsyncReverseQuery:
        """Store filters for later execution."""
        self._filters.update(kwargs)
        return self

    def limit(self, count: int) -> AsyncReverseQuery:
        """Store a result limit."""
        self._limit = count
        return self

    def offset(self, count: int) -> AsyncReverseQuery:
        """Store a result offset."""
        self._offset = count
        return self

    def _build_query(self) -> AsyncQueryBuilder[BaseDBModel] | None:
        fk_id = self.fk_value
        if fk_id is None or self._db is None:
            return None

        query = self._db.select(self.to_model).filter(
            **{f"{self.fk_field}_id": fk_id}
        )
        if self._filters:
            query = query.filter(**self._filters)
        if self._limit is not None:
            query = query.limit(self._limit)
        if self._offset is not None:
            query = query.offset(self._offset)
        return query

    async def fetch_all(self) -> list[BaseDBModel]:
        """Execute the reverse query."""
        query = self._build_query()
        if query is None:
            return []
        return await query.fetch_all()

    async def fetch_one(self) -> Optional[BaseDBModel]:
        """Fetch one related model instance."""
        results = await self.limit(1).fetch_all()
        return results[0] if results else None

    async def count(self) -> int:
        """Count related model instances."""
        query = self._build_query()
        if query is None:
            return 0
        return await query.count()

    async def exists(self) -> bool:
        """Return whether related model instances exist."""
        return await self.count() > 0


class AsyncReverseRelationship(SyncReverseRelationship):
    """Descriptor returning async reverse relationship wrappers."""

    def __init__(
        self,
        from_model: type[BaseDBModel],
        fk_field: str,
        related_name: str,
    ) -> None:
        """Initialize the async reverse descriptor."""
        super().__init__(from_model, fk_field, related_name)

    @overload
    def __get__(
        self,
        instance: None,
        owner: type[object],
    ) -> SyncReverseRelationship: ...

    @overload
    def __get__(
        self,
        instance: SyncHasPKAndContext,
        owner: type[object],
    ) -> Union[ReverseQuery, PrefetchedResult]: ...

    def __get__(
        self,
        instance: Optional[SyncHasPKAndContext],
        owner: type[object],
    ) -> Union[
        SyncReverseRelationship,
        ReverseQuery,
        PrefetchedResult,
    ]:
        """Return async prefetched or lazy reverse wrappers."""
        if instance is None:
            return self

        cache = instance.__dict__.get("_prefetch_cache", {})
        if self.related_name in cache:
            return cast(
                "PrefetchedResult",
                AsyncPrefetchedResult(
                    cached_items=cache[self.related_name],
                    instance=cast("HasPKAndContext", instance),
                    to_model=self.from_model,
                    fk_field=self.fk_field,
                    db_context=cast(
                        "Optional[AsyncSqliterDB]",
                        instance.db_context,
                    ),
                ),
            )

        return cast(
            "ReverseQuery",
            AsyncReverseQuery(
                instance=cast("HasPKAndContext", instance),
                to_model=self.from_model,
                fk_field=self.fk_field,
                db_context=cast(
                    "Optional[AsyncSqliterDB]",
                    instance.db_context,
                ),
            ),
        )
