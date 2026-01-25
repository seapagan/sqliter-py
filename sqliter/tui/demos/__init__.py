"""Demo registry for managing all available demos."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from sqliter.tui.demos import (
    caching,
    connection,
    constraints,
    crud,
    errors,
    field_selection,
    filters,
    models,
    ordering,
    orm,
    results,
    string_filters,
    timestamps,
    transactions,
)

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Sequence

    from sqliter.tui.demos.base import Demo, DemoCategory


class DemoRegistry:
    """Registry for all available demos."""

    _categories: ClassVar[list[DemoCategory]] = []
    _demos_by_id: ClassVar[dict[str, Demo]] = {}

    @classmethod
    def register_category(cls, category: DemoCategory) -> None:
        """Register a demo category with all its demos."""
        cls._categories.append(category)
        for demo in category.demos:
            if demo.id in cls._demos_by_id:
                msg = f"Duplicate demo id: {demo.id}"
                raise ValueError(msg)
            cls._demos_by_id[demo.id] = demo

    @classmethod
    def get_categories(cls) -> Sequence[DemoCategory]:
        """Get all registered categories in order."""
        return tuple(cls._categories)

    @classmethod
    def get_demo(cls, demo_id: str) -> Demo | None:
        """Get a demo by its unique ID."""
        return cls._demos_by_id.get(demo_id)

    @classmethod
    def get_demo_code(cls, demo_id: str) -> str:
        """Get the display code for a demo (including setup if any)."""
        demo = cls.get_demo(demo_id)
        if demo is None:
            return ""
        code_parts: list[str] = []
        if demo.setup_code:
            code_parts.append(f"# Setup\n{demo.setup_code}\n")
        code_parts.append(demo.code)
        return "\n".join(code_parts)

    @classmethod
    def reset(cls) -> None:
        """Reset the registry (for testing).

        After calling reset(), call _init_registry() to repopulate.
        """
        cls._categories = []
        cls._demos_by_id = {}


def _init_registry() -> None:
    """Initialize the demo registry with all categories."""
    DemoRegistry.register_category(connection.get_category())
    DemoRegistry.register_category(models.get_category())
    DemoRegistry.register_category(crud.get_category())
    DemoRegistry.register_category(filters.get_category())
    DemoRegistry.register_category(results.get_category())
    DemoRegistry.register_category(ordering.get_category())
    DemoRegistry.register_category(field_selection.get_category())
    DemoRegistry.register_category(string_filters.get_category())
    DemoRegistry.register_category(constraints.get_category())
    DemoRegistry.register_category(orm.get_category())
    DemoRegistry.register_category(caching.get_category())
    DemoRegistry.register_category(timestamps.get_category())
    DemoRegistry.register_category(transactions.get_category())
    DemoRegistry.register_category(errors.get_category())


_init_registry()
