"""Core async database tests."""

from __future__ import annotations

import builtins
import importlib
import sys
from typing import TYPE_CHECKING

import pytest

from sqliter.asyncio import AsyncSqliterDB
from tests.conftest import ExampleModel

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pytest_mock import MockerFixture


def test_asyncio_import_error_without_aiosqlite(
    monkeypatch: pytest.MonkeyPatch,
    mocker: MockerFixture,
) -> None:
    """Importing sqliter.asyncio without aiosqlite raises a helpful error."""
    real_import = builtins.__import__

    def fake_import(
        name: str,
        globals_: Mapping[str, object] | None = None,
        locals_: Mapping[str, object] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> object:
        if name == "aiosqlite":
            msg = "No module named 'aiosqlite'"
            raise ImportError(msg)
        return real_import(name, globals_, locals_, fromlist, level)

    mocker.patch.dict(
        "sys.modules",
        {
            "sqliter.asyncio": None,
            "sqliter.asyncio.db": None,
            "sqliter.asyncio.query": None,
            "aiosqlite": None,
        },
    )
    monkeypatch.setattr(builtins, "__import__", fake_import)
    sys.modules.pop("sqliter.asyncio", None)
    sys.modules.pop("sqliter.asyncio.db", None)
    sys.modules.pop("sqliter.asyncio.query", None)
    sys.modules.pop("aiosqlite", None)

    module = importlib.import_module("sqliter.asyncio")

    with pytest.raises(ImportError, match="aiosqlite is required"):
        _ = module.AsyncSqliterDB


@pytest.mark.asyncio
async def test_async_create_and_get_table_names() -> None:
    """Async DB can create tables and list them."""
    db = AsyncSqliterDB(memory=True)
    await db.create_table(ExampleModel)

    assert "test_table" in await db.get_table_names()

    await db.close()


@pytest.mark.asyncio
async def test_async_insert_get_update_delete() -> None:
    """Async CRUD works for the core DB API."""
    db = AsyncSqliterDB(memory=True)
    await db.create_table(ExampleModel)

    inserted = await db.insert(
        ExampleModel(slug="mit", name="MIT", content="License text")
    )
    fetched = await db.get(ExampleModel, inserted.pk)

    assert fetched is not None
    assert fetched.slug == "mit"

    inserted.content = "Updated"
    await db.update(inserted)
    updated = await db.get(ExampleModel, inserted.pk)

    assert updated is not None
    assert updated.content == "Updated"

    await db.delete(ExampleModel, inserted.pk)
    deleted = await db.get(ExampleModel, inserted.pk)
    assert deleted is None

    await db.close()


@pytest.mark.asyncio
async def test_async_query_builder_fetch_and_count() -> None:
    """Async QueryBuilder supports basic fetch and count operations."""
    db = AsyncSqliterDB(memory=True)
    await db.create_table(ExampleModel)
    await db.insert(ExampleModel(slug="mit", name="MIT", content="One"))
    await db.insert(ExampleModel(slug="gpl", name="GPL", content="Two"))

    results = await db.select(ExampleModel).order("slug").fetch_all()
    assert [item.slug for item in results] == ["gpl", "mit"]

    filtered = await db.select(ExampleModel).filter(name="MIT").fetch_one()
    assert filtered is not None
    assert filtered.slug == "mit"

    count = await db.select(ExampleModel).count()
    assert count == 2
    assert await db.select(ExampleModel).filter(name="GPL").exists() is True

    await db.close()


@pytest.mark.asyncio
async def test_async_context_manager_commits_transaction(
    temp_db_path: str,
) -> None:
    """Async context manager commits on success."""
    db = AsyncSqliterDB(temp_db_path, auto_commit=False)
    await db.create_table(ExampleModel)

    async with db:
        await db.insert(
            ExampleModel(slug="apache", name="Apache", content="Three")
        )

    fetched = await db.get(ExampleModel, 1)
    assert fetched is not None
    assert fetched.slug == "apache"

    await db.close()


@pytest.mark.asyncio
async def test_async_bulk_insert_and_update_where() -> None:
    """Async DB supports bulk insert and update_where."""
    db = AsyncSqliterDB(memory=True)
    await db.create_table(ExampleModel)

    inserted = await db.bulk_insert(
        [
            ExampleModel(slug="a", name="A", content="one"),
            ExampleModel(slug="b", name="B", content="two"),
        ]
    )
    assert len(inserted) == 2

    updated_count = await db.update_where(
        ExampleModel,
        where={"slug": "a"},
        values={"content": "updated"},
    )
    assert updated_count == 1

    updated = await db.select(ExampleModel).filter(slug="a").fetch_one()
    assert updated is not None
    assert updated.content == "updated"

    await db.close()
