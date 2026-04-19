"""Async ORM model base."""

from __future__ import annotations

from typing import Any

from sqliter.asyncio.orm.fields import AsyncLazyLoader
from sqliter.asyncio.orm.m2m import AsyncReverseManyToMany
from sqliter.asyncio.orm.query import AsyncReverseRelationship
from sqliter.orm.model import BaseDBModel as SyncBaseDBModel
from sqliter.orm.registry import ModelRegistry

__all__ = ["AsyncBaseDBModel"]


class AsyncBaseDBModel(SyncBaseDBModel):
    """ORM model base with explicit async relationship access."""

    def __getattribute__(self, name: str) -> object:
        """Return async FK loaders while preserving normal attribute access."""
        if name in object.__getattribute__(self, "fk_descriptors"):
            fk_id = object.__getattribute__(self, f"{name}_id")
            if fk_id is None:
                return None

            instance_dict = object.__getattribute__(self, "__dict__")
            cache = instance_dict.setdefault("_fk_cache", {})
            db_context = object.__getattribute__(self, "db_context")
            cached = cache.get(name)
            if cached is not None:
                if isinstance(cached, AsyncLazyLoader):
                    if cached.db_context is None and db_context is not None:
                        cache[name] = AsyncLazyLoader(
                            instance=self,
                            to_model=object.__getattribute__(
                                self, "fk_descriptors"
                            )[name].to_model,
                            fk_id=fk_id,
                            db_context=db_context,
                        )
                    return cache[name]
                return cached

            descriptor = object.__getattribute__(self, "fk_descriptors")[name]
            cache[name] = AsyncLazyLoader(
                instance=self,
                to_model=descriptor.to_model,
                fk_id=fk_id,
                db_context=db_context,
            )
            return cache[name]

        return object.__getattribute__(self, name)

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:  # noqa: ANN401
        """Set up ORM metadata and patch reverse accessors to async variants."""
        super().__pydantic_init_subclass__(**kwargs)
        cls._install_async_reverse_accessors()

    @classmethod
    def _install_async_reverse_accessors(cls) -> None:
        """Replace sync reverse descriptors on async models with async ones."""
        state = ModelRegistry.snapshot()
        cls._install_async_fk_reverse_accessors(state["foreign_keys"])
        cls._install_async_m2m_reverse_accessors(state["m2m_relationships"])

    @classmethod
    def _install_async_fk_reverse_accessors(
        cls,
        foreign_keys: dict[str, list[dict[str, Any]]],
    ) -> None:
        """Replace reverse-FK descriptors with async descriptors."""
        for from_table, relations in foreign_keys.items():
            from_model = ModelRegistry.get_model(from_table)
            if from_model is None:
                continue
            for relation in relations:
                if relation["to_model"] is not cls:
                    continue
                related_name = relation.get("related_name")
                if not related_name:
                    continue
                setattr(
                    cls,
                    related_name,
                    AsyncReverseRelationship(
                        from_model,
                        relation["fk_field"],
                        related_name,
                    ),
                )

    @classmethod
    def _install_async_m2m_reverse_accessors(
        cls,
        m2m_relationships: dict[str, list[dict[str, Any]]],
    ) -> None:
        """Replace reverse-M2M descriptors with async descriptors."""
        for from_table, relations in m2m_relationships.items():
            from_model = ModelRegistry.get_model(from_table)
            if from_model is None:
                continue
            for relation in relations:
                if relation["to_model"] is not cls:
                    continue
                related_name = relation.get("related_name")
                if not related_name:
                    continue
                setattr(
                    cls,
                    related_name,
                    AsyncReverseManyToMany(
                        from_model=from_model,
                        to_model=cls,
                        junction_table=relation["junction_table"],
                        related_name=related_name,
                        symmetrical=relation["symmetrical"],
                    ),
                )
