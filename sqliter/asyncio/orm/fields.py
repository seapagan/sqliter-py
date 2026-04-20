"""Async ORM FK descriptors and loaders."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Generic, Optional, TypeVar, cast, overload

from sqliter.asyncio.orm.query import AsyncReverseRelationship
from sqliter.orm.fields import ForeignKey as SyncForeignKey

if TYPE_CHECKING:  # pragma: no cover
    from sqliter.asyncio.db import AsyncSqliterDB
    from sqliter.model.model import BaseDBModel

T = TypeVar("T")

logger = logging.getLogger(__name__)


class AsyncLazyLoader(Generic[T]):
    """Explicit async FK loader."""

    def __init__(
        self,
        instance: object,
        to_model: type[T],
        fk_id: Optional[int],
        db_context: Optional[AsyncSqliterDB],
    ) -> None:
        """Store loader state for explicit async fetching."""
        self._instance = instance
        self._to_model = to_model
        self._fk_id = fk_id
        self._db = db_context
        self._cached: Optional[T] = None

    @property
    def db_context(self) -> object:
        """Return the database context."""
        return self._db

    async def fetch(self) -> Optional[T]:
        """Load and return the related object, if present."""
        if not self._fk_id:
            self._cached = None
            return None

        if self._cached is None and self._db is not None:
            from sqliter.exceptions import SqliterError  # noqa: PLC0415

            try:
                result = await self._db.get(
                    cast("type[BaseDBModel]", self._to_model),
                    self._fk_id,
                )
                self._cached = cast("Optional[T]", result)
            except SqliterError as exc:
                logger.debug(
                    "AsyncLazyLoader failed to fetch %s with pk=%s: %s",
                    self._to_model.__name__,
                    self._fk_id,
                    exc,
                )
                self._cached = None
        return self._cached

    def __getattr__(self, name: str) -> object:
        """Tell callers to use explicit async loading."""
        msg = (
            f"Async foreign key '{name}' is not loaded. "
            "Use `await relation.fetch()` first."
        )
        raise AttributeError(msg)

    def __repr__(self) -> str:
        """Show lazy state for debugging."""
        if self._cached is None:
            return (
                f"<AsyncLazyLoader unloaded for {self._to_model.__name__} "
                f"id={self._fk_id}>"
            )
        return f"<AsyncLazyLoader loaded: {self._cached!r}>"


class AsyncForeignKey(SyncForeignKey[T]):
    """Async FK descriptor providing explicit lazy loading."""

    def __set_name__(self, owner: type, name: str) -> None:
        """Register the FK and replace existing reverse accessors."""
        super().__set_name__(owner, name)
        if self.related_name and hasattr(self.to_model, self.related_name):
            setattr(
                self.to_model,
                self.related_name,
                AsyncReverseRelationship(owner, name, self.related_name),
            )

    @overload
    def __get__(
        self,
        instance: None,
        owner: type[object],
    ) -> AsyncForeignKey[T]: ...

    @overload
    def __get__(self, instance: object, owner: type[object]) -> T: ...

    def __get__(
        self,
        instance: object | None,
        owner: type[object],
    ) -> AsyncForeignKey[T] | T:
        """Return an async lazy loader for instance access."""
        if instance is None:
            return self

        fk_id = getattr(instance, f"{self.name}_id", None)
        if not fk_id:
            return cast("T", None)

        cache = getattr(instance, "__dict__", {}).setdefault("_fk_cache", {})
        cached = cache.get(self.name or "")
        if cached is not None:
            return cast("T", cached)

        loader = AsyncLazyLoader(
            instance=instance,
            to_model=self.to_model,
            fk_id=fk_id,
            db_context=getattr(instance, "db_context", None),
        )
        cache[self.name or ""] = loader
        return cast("T", loader)
