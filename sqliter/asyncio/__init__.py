"""Async support for SQLiter."""

from __future__ import annotations

_IMPORT_ERROR: ImportError | None = None

try:
    from sqliter.asyncio.db import AsyncSqliterDB
    from sqliter.asyncio.query import AsyncQueryBuilder
except ImportError as exc:
    _IMPORT_ERROR = exc

__all__ = ["AsyncQueryBuilder", "AsyncSqliterDB"]


def __getattr__(name: str) -> object:
    """Raise a helpful dependency error for async imports."""
    if name not in __all__:
        err = f"module {__name__!r} has no attribute {name!r}"
        raise AttributeError(err)

    if _IMPORT_ERROR is None:
        return globals()[name]

    msg = (
        "aiosqlite is required for sqliter.asyncio. "
        "Install the package with `sqliter-py[async]` or "
        "`sqliter-py[full]`."
    )
    raise ImportError(msg) from _IMPORT_ERROR
