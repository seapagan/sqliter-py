"""Query builders for reverse relationships."""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Optional,
    Protocol,
    Union,
    overload,
    runtime_checkable,
)

if TYPE_CHECKING:  # pragma: no cover
    from sqliter.model.model import BaseDBModel
    from sqliter.sqliter import SqliterDB


@runtime_checkable
class HasPKAndContext(Protocol):
    """Protocol for model instances with pk and db_context."""

    pk: Optional[int]
    db_context: Optional[SqliterDB]


class PrefetchedResult:
    """Wrapper around prefetched reverse FK data.

    Provides the same read interface as ``ReverseQuery`` so that code
    consuming ``author.books`` works identically whether the data was
    prefetched or lazily loaded.  Write-like operations such as
    ``filter()`` fall through to a real database query.
    """

    def __init__(
        self,
        cached_items: list[BaseDBModel],
        instance: HasPKAndContext,
        to_model: type[BaseDBModel],
        fk_field: str,
        db_context: Optional[SqliterDB],
    ) -> None:
        """Initialize a prefetched result wrapper.

        Args:
            cached_items: The prefetched list of related instances.
            instance: The parent model instance.
            to_model: The related model class.
            fk_field: The FK field name on the related model.
            db_context: Database connection for fallback queries.
        """
        self._items = cached_items
        self._instance = instance
        self._to_model = to_model
        self._fk_field = fk_field
        self._db = db_context

    def fetch_all(self) -> list[BaseDBModel]:
        """Return all prefetched related instances.

        Returns:
            List of related model instances.
        """
        return list(self._items)

    def fetch_one(self) -> Optional[BaseDBModel]:
        """Return the first prefetched instance, or None.

        Returns:
            A related model instance, or None.
        """
        return self._items[0] if self._items else None

    def count(self) -> int:
        """Return the count of prefetched instances.

        Returns:
            Number of related objects.
        """
        return len(self._items)

    def exists(self) -> bool:
        """Check whether any prefetched instances exist.

        Returns:
            True if at least one related object exists.
        """
        return len(self._items) > 0

    def filter(self, **kwargs: Any) -> ReverseQuery:  # noqa: ANN401
        """Fall back to a real database query for filtered results.

        Args:
            **kwargs: Filter criteria.

        Returns:
            A ReverseQuery for further chaining.
        """
        return ReverseQuery(
            instance=self._instance,
            to_model=self._to_model,
            fk_field=self._fk_field,
            db_context=self._db,
        ).filter(**kwargs)


class ReverseQuery:
    """Query builder for reverse relationships.

    Delegates to QueryBuilder for actual SQL execution.
    """

    def __init__(
        self,
        instance: HasPKAndContext,
        to_model: type[BaseDBModel],
        fk_field: str,
        db_context: Optional[SqliterDB],
    ) -> None:
        """Initialize reverse query.

        Args:
            instance: The model instance (e.g., Author)
            to_model: The related model class (e.g., Book)
            fk_field: The FK field name (e.g., "author")
            db_context: Database connection for queries
        """
        self.instance = instance
        self.to_model = to_model
        self.fk_field = fk_field
        self._db = db_context
        self._filters: dict[str, Any] = {}
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None

    @property
    def fk_value(self) -> Optional[int]:
        """Get the FK ID value from the instance."""
        return self.instance.pk

    def filter(self, **kwargs: Any) -> ReverseQuery:  # noqa: ANN401
        """Store filters for later execution.

        Args:
            **kwargs: Filter criteria

        Returns:
            Self for chaining
        """
        self._filters.update(kwargs)
        return self

    def limit(self, count: int) -> ReverseQuery:
        """Set limit on query results.

        Args:
            count: Maximum number of results

        Returns:
            Self for chaining
        """
        self._limit = count
        return self

    def offset(self, count: int) -> ReverseQuery:
        """Set offset on query results.

        Args:
            count: Number of results to skip

        Returns:
            Self for chaining
        """
        self._offset = count
        return self

    def fetch_all(self) -> list[BaseDBModel]:
        """Execute query using stored db_context.

        Returns:
            List of related model instances
        """
        fk_id = self.fk_value
        if fk_id is None or self._db is None:
            return []

        # Build query with FK filter and additional filters
        query = self._db.select(self.to_model).filter(
            **{f"{self.fk_field}_id": fk_id}
        )

        # Apply additional filters
        if self._filters:
            query = query.filter(**self._filters)

        # Apply limit and offset
        if self._limit is not None:
            query = query.limit(self._limit)
        if self._offset is not None:
            query = query.offset(self._offset)

        return query.fetch_all()

    def fetch_one(self) -> Optional[BaseDBModel]:
        """Execute query and return single result.

        Returns:
            Related model instance or None
        """
        results = self.limit(1).fetch_all()
        return results[0] if results else None

    def count(self) -> int:
        """Count related objects.

        Returns:
            Number of related objects
        """
        fk_id = self.fk_value
        if fk_id is None or self._db is None:
            return 0

        # Build query with FK filter and additional filters
        query = self._db.select(self.to_model).filter(
            **{f"{self.fk_field}_id": fk_id}
        )

        # Apply additional filters
        if self._filters:
            query = query.filter(**self._filters)

        return query.count()

    def exists(self) -> bool:
        """Check if any related objects exist.

        Returns:
            True if at least one related object exists
        """
        return self.count() > 0


class ReverseRelationship:
    """Descriptor that returns ReverseQuery when accessed.

    Added automatically to models during class creation by ForeignKeyDescriptor.
    """

    def __init__(
        self, from_model: type[BaseDBModel], fk_field: str, related_name: str
    ) -> None:
        """Initialize reverse relationship descriptor.

        Args:
            from_model: The model with the FK field (e.g., Book)
            fk_field: The FK field name (e.g., "author")
            related_name: The name of this reverse relationship (e.g., "books")
        """
        self.from_model = from_model
        self.fk_field = fk_field
        self.related_name = related_name

    @overload
    def __get__(
        self, instance: None, owner: type[object]
    ) -> ReverseRelationship: ...

    @overload
    def __get__(
        self, instance: HasPKAndContext, owner: type[object]
    ) -> Union[ReverseQuery, PrefetchedResult]: ...

    def __get__(
        self, instance: Optional[HasPKAndContext], owner: type[object]
    ) -> Union[ReverseRelationship, ReverseQuery, PrefetchedResult]:
        """Return ReverseQuery or PrefetchedResult when accessed on instance.

        If the instance has a ``_prefetch_cache`` entry for this
        relationship, returns a ``PrefetchedResult`` wrapping the cached
        list. Otherwise returns a ``ReverseQuery`` for lazy loading.

        Args:
            instance: Model instance (e.g., Author)
            owner: Model class

        Returns:
            PrefetchedResult if prefetched, else ReverseQuery
        """
        if instance is None:
            return self

        # Check prefetch cache
        cache = instance.__dict__.get("_prefetch_cache", {})
        if self.related_name in cache:
            return PrefetchedResult(
                cached_items=cache[self.related_name],
                instance=instance,
                to_model=self.from_model,
                fk_field=self.fk_field,
                db_context=instance.db_context,
            )

        return ReverseQuery(
            instance=instance,
            to_model=self.from_model,
            fk_field=self.fk_field,
            db_context=instance.db_context,
        )

    def __set__(self, instance: object, value: object) -> None:
        """Prevent setting reverse relationships."""
        msg = (
            f"Cannot set reverse relationship '{self.related_name}'. "
            f"Use the ForeignKey field on {self.from_model.__name__} instead."
        )
        raise AttributeError(msg)
