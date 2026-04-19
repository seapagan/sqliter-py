"""Core async database tests."""

from __future__ import annotations

import builtins
import importlib
import logging
import sqlite3
import sys
from typing import TYPE_CHECKING, Any, cast

import pytest

from sqliter import asyncio as sqliter_asyncio
from sqliter.asyncio import AsyncSqliterDB
from sqliter.exceptions import (
    DatabaseConnectionError,
    ForeignKeyConstraintError,
    InvalidIndexError,
    InvalidProjectionError,
    RecordDeletionError,
    RecordFetchError,
    RecordInsertionError,
    RecordNotFoundError,
    RecordUpdateError,
    SqlExecutionError,
    TableCreationError,
    TableDeletionError,
)
from sqliter.orm import BaseDBModel, ForeignKey, ManyToMany
from sqliter.orm.m2m import _m2m_column_names
from sqliter.orm.registry import ModelRegistry
from sqliter.query import func
from tests.conftest import ExampleModel

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pytest_mock import MockerFixture


class _FakeCursor:
    """Small async cursor test double."""

    def __init__(
        self,
        *,
        execute_error: BaseException | None = None,
        fetchone_result: object = None,
        fetchall_result: list[object] | None = None,
        rowcount: int = 1,
        lastrowid: int = 1,
    ) -> None:
        self.execute_error = execute_error
        self.fetchone_result = fetchone_result
        self.fetchall_result = fetchall_result or []
        self.rowcount = rowcount
        self.lastrowid = lastrowid

    async def execute(self, _sql: str, _values: object = ()) -> _FakeCursor:
        if self.execute_error is not None:
            raise self.execute_error
        return self

    async def fetchone(self) -> object:
        return self.fetchone_result

    async def fetchall(self) -> list[object]:
        return self.fetchall_result


class _FakeConnection:
    """Small async connection test double."""

    def __init__(self, cursor: _FakeCursor) -> None:
        self._cursor = cursor
        self.rollback_calls = 0
        self.commit_calls = 0
        self.closed = False

    async def cursor(self) -> _FakeCursor:
        return self._cursor

    async def execute(self, _sql: str) -> None:
        return None

    async def commit(self) -> None:
        self.commit_calls += 1

    async def rollback(self) -> None:
        self.rollback_calls += 1

    async def close(self) -> None:
        self.closed = True


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


def test_asyncio_module_getattr_paths() -> None:
    """Async package exposes expected attributes via __getattr__."""
    module = importlib.reload(sqliter_asyncio)

    assert module.__getattr__("AsyncSqliterDB") is AsyncSqliterDB

    with pytest.raises(AttributeError, match="no attribute 'missing'"):
        module.__getattr__("missing")


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
async def test_async_get_table_names_closes_temporary_connection() -> None:
    """get_table_names closes a temporary connection after use."""
    db = AsyncSqliterDB(memory=True)

    assert await db.get_table_names() == []
    assert db.conn is None
    assert db._model_field_to_db_column(ExampleModel, "slug") == "slug"


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


def test_async_init_rejects_reset() -> None:
    """Async init rejects reset=True."""
    with pytest.raises(ValueError, match="reset=True is not supported"):
        AsyncSqliterDB(memory=True, reset=True)


@pytest.mark.asyncio
async def test_async_create_with_reset_clears_existing_tables(
    temp_db_path: str,
) -> None:
    """Async create(reset=True) drops existing user tables."""
    initial = AsyncSqliterDB(temp_db_path)
    await initial.create_table(ExampleModel)
    assert "test_table" in await initial.get_table_names()
    await initial.close()

    reset_db = await AsyncSqliterDB.create(temp_db_path, reset=True)
    assert "test_table" not in await reset_db.get_table_names()
    await reset_db.close()


@pytest.mark.asyncio
async def test_async_db_properties_expose_sync_configuration(
    mocker: MockerFixture,
) -> None:
    """Async DB exposes sync-backed properties and reset logging."""
    logger = logging.getLogger("sqliter.asyncio.test")
    db = AsyncSqliterDB(
        memory=True,
        auto_commit=False,
        debug=True,
        logger=logger,
    )
    assert db.debug is True
    assert db.logger is not None
    assert db.logger.name == "sqliter"
    assert db.is_memory is True
    assert db.filename is None
    assert db.auto_commit is False
    assert db.is_autocommit is False
    assert db.in_transaction is False

    await db.create_table(ExampleModel)
    logger_debug = mocker.spy(db.logger, "debug")
    await db.reset_database()
    assert logger_debug.call_count >= 1
    assert any(
        "Database reset" in call.args[0] for call in logger_debug.call_args_list
    )
    await db.close()


@pytest.mark.asyncio
async def test_async_drop_table_removes_table() -> None:
    """drop_table removes an existing table."""
    db = AsyncSqliterDB(memory=True)
    await db.create_table(ExampleModel)
    await db.drop_table(ExampleModel)
    assert "test_table" not in await db.get_table_names()
    await db.close()


@pytest.mark.asyncio
async def test_async_connect_and_get_table_names_wrap_connection_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Connection setup failures are wrapped consistently."""

    async def fail_connect(_filename: str) -> None:
        msg = "boom"
        raise sqlite3.Error(msg)

    asyncio_db_module = cast(
        "Any", importlib.import_module("sqliter.asyncio.db")
    )
    aiosqlite_module = cast("Any", asyncio_db_module.aiosqlite)
    monkeypatch.setattr(aiosqlite_module, "connect", fail_connect)

    db = AsyncSqliterDB(memory=True)
    with pytest.raises(DatabaseConnectionError):
        await db.connect()

    async def connect_without_state() -> _FakeConnection:
        return _FakeConnection(_FakeCursor())

    monkeypatch.setattr(db, "connect", connect_without_state)
    with pytest.raises(
        DatabaseConnectionError,
        match="Failed to establish a database connection",
    ):
        await db.get_table_names()


@pytest.mark.asyncio
async def test_async_create_table_force_and_indexes() -> None:
    """create_table(force=True) rebuilds indexed tables."""
    state = ModelRegistry.snapshot()
    try:

        class IndexedModel(BaseDBModel):
            """Model with regular and unique indexes."""

            slug: str
            name: str

            class Meta:
                """Index metadata."""

                indexes = ("name", ("slug", "name"))
                unique_indexes = ("slug",)

        db = AsyncSqliterDB(memory=True)
        await db.create_table(IndexedModel)
        await db.create_table(IndexedModel, force=True)

        table_name = IndexedModel.get_table_name()
        conn = await db.connect()
        cursor = await conn.cursor()
        await db.execute_cursor(cursor, f'PRAGMA index_list("{table_name}")')
        indexes = [row[1] for row in await cursor.fetchall()]

        assert f"idx_{table_name}_name" in indexes
        assert f"idx_{table_name}_slug_name" in indexes
        assert f"idx_{table_name}_slug_unique" in indexes

        await db.close()
    finally:
        ModelRegistry.restore(state)


@pytest.mark.asyncio
async def test_async_create_table_invalid_index_raises() -> None:
    """Async create_table surfaces invalid index configuration."""
    state = ModelRegistry.snapshot()
    try:

        class BadIndexModel(BaseDBModel):
            """Model with invalid async index metadata."""

            slug: str

            class Meta:
                """Broken index metadata."""

                indexes = ("missing",)

        db = AsyncSqliterDB(memory=True)
        with pytest.raises(InvalidIndexError, match="BadIndexModel"):
            await db.create_table(BadIndexModel)
        await db.close()
    finally:
        ModelRegistry.restore(state)


@pytest.mark.asyncio
async def test_async_table_and_sql_wrappers_handle_sqlite_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raw SQL, create_table, and drop_table wrap sqlite failures."""
    db = AsyncSqliterDB(memory=True)
    fake_conn = _FakeConnection(_FakeCursor())
    db.conn = cast("Any", fake_conn)

    async def fail_execute(
        _cursor: _FakeCursor,
        _sql: str,
        _values: object = (),
    ) -> _FakeCursor:
        msg = "bad sql"
        raise sqlite3.Error(msg)

    monkeypatch.setattr(db, "_execute_async", fail_execute)

    with pytest.raises(TableCreationError):
        await db.create_table(ExampleModel)

    with pytest.raises(SqlExecutionError):
        await db._execute_sql("SELECT 1")

    with pytest.raises(TableDeletionError):
        await db.drop_table(ExampleModel)

    await db.close()


@pytest.mark.asyncio
async def test_async_bulk_insert_rejects_mixed_models() -> None:
    """bulk_insert rejects mixed model types."""
    state = ModelRegistry.snapshot()
    try:

        class OtherModel(BaseDBModel):
            """Second model for mixed bulk insert validation."""

            name: str

        db = AsyncSqliterDB(memory=True)
        await db.create_table(ExampleModel)
        await db.create_table(OtherModel)

        with pytest.raises(TypeError, match="All instances must be the same"):
            await db.bulk_insert(
                [
                    ExampleModel(slug="a", name="A", content="one"),
                    OtherModel(name="B"),
                ]
            )

        await db.close()
    finally:
        ModelRegistry.restore(state)


@pytest.mark.asyncio
async def test_async_bulk_insert_empty_returns_empty_list() -> None:
    """bulk_insert returns an empty list for no input."""
    db = AsyncSqliterDB(memory=True)
    assert await db.bulk_insert([]) == []
    await db.close()


@pytest.mark.asyncio
async def test_async_bulk_insert_fk_violation_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """bulk_insert wraps FK failures in ForeignKeyConstraintError."""
    db = AsyncSqliterDB(memory=True)
    fake_conn = _FakeConnection(
        _FakeCursor(
            execute_error=sqlite3.IntegrityError(
                "FOREIGN KEY constraint failed"
            )
        )
    )
    db.conn = cast("Any", fake_conn)

    async def return_conn() -> _FakeConnection:
        return fake_conn

    monkeypatch.setattr(db, "connect", return_conn)

    with pytest.raises(ForeignKeyConstraintError):
        await db.bulk_insert([ExampleModel(slug="a", name="A", content="one")])

    assert fake_conn.rollback_calls == 1
    await db.close()


@pytest.mark.asyncio
async def test_async_bulk_insert_non_fk_integrity_error_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """bulk_insert wraps non-FK IntegrityError as RecordInsertionError."""
    db = AsyncSqliterDB(memory=True)
    fake_conn = _FakeConnection(
        _FakeCursor(
            execute_error=sqlite3.IntegrityError("UNIQUE constraint failed")
        )
    )
    db.conn = cast("Any", fake_conn)

    async def return_conn() -> _FakeConnection:
        return fake_conn

    monkeypatch.setattr(db, "connect", return_conn)

    with pytest.raises(RecordInsertionError):
        await db.bulk_insert([ExampleModel(slug="a", name="A", content="one")])

    assert fake_conn.rollback_calls == 1
    await db.close()


@pytest.mark.asyncio
async def test_async_bulk_insert_sqlite_error_rolls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """bulk_insert wraps generic sqlite errors and rolls back."""
    db = AsyncSqliterDB(memory=True)
    fake_conn = _FakeConnection(
        _FakeCursor(execute_error=sqlite3.Error("bulk failure"))
    )
    db.conn = cast("Any", fake_conn)

    async def return_conn() -> _FakeConnection:
        return fake_conn

    monkeypatch.setattr(db, "connect", return_conn)

    with pytest.raises(RecordInsertionError):
        await db.bulk_insert([ExampleModel(slug="a", name="A", content="one")])

    assert fake_conn.rollback_calls == 1
    await db.close()


@pytest.mark.asyncio
async def test_async_get_validates_negative_cache_ttl() -> None:
    """Get rejects negative cache TTL."""
    db = AsyncSqliterDB(memory=True)
    with pytest.raises(ValueError, match="cache_ttl must be non-negative"):
        await db.get(ExampleModel, 1, cache_ttl=-1)
    await db.close()


@pytest.mark.asyncio
async def test_async_get_uses_cache_after_first_lookup() -> None:
    """Get serves repeated lookups from cache."""
    db = AsyncSqliterDB(memory=True, cache_enabled=True)
    await db.create_table(ExampleModel)
    inserted = await db.insert(
        ExampleModel(slug="cached", name="Cached", content="once")
    )

    first = await db.get(ExampleModel, inserted.pk)
    second = await db.get(ExampleModel, inserted.pk)

    assert first is second
    await db.close()


@pytest.mark.asyncio
async def test_async_insert_foreign_key_violation_raises() -> None:
    """Insert wraps FK failures in ForeignKeyConstraintError."""
    state = ModelRegistry.snapshot()
    try:

        class Parent(BaseDBModel):
            """Parent model for FK insert failure."""

            name: str

        class Child(BaseDBModel):
            """Child model for FK insert failure."""

            name: str
            parent: ForeignKey[Parent] = ForeignKey(Parent, on_delete="CASCADE")

        db = AsyncSqliterDB(memory=True)
        await db.create_table(Parent)
        await db.create_table(Child)

        with pytest.raises(ForeignKeyConstraintError):
            await db.insert(Child(name="kid", parent_id=999))

        await db.close()
    finally:
        ModelRegistry.restore(state)


@pytest.mark.asyncio
async def test_async_insert_wraps_non_fk_errors_and_rolls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Insert wraps non-FK sqlite errors and rolls back."""
    db = AsyncSqliterDB(memory=True)
    fake_conn = _FakeConnection(
        _FakeCursor(execute_error=sqlite3.IntegrityError("other failure"))
    )
    db.conn = cast("Any", fake_conn)

    async def return_conn() -> _FakeConnection:
        return fake_conn

    monkeypatch.setattr(db, "connect", return_conn)

    with pytest.raises(RecordInsertionError):
        await db.insert(ExampleModel(pk=0, slug="a", name="A", content="x"))

    assert fake_conn.rollback_calls == 1
    await db.close()


@pytest.mark.asyncio
async def test_async_insert_generic_sqlite_error_rolls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Insert wraps generic sqlite errors and rolls back."""
    db = AsyncSqliterDB(memory=True)
    fake_conn = _FakeConnection(
        _FakeCursor(execute_error=sqlite3.Error("insert failure"))
    )
    db.conn = cast("Any", fake_conn)

    async def return_conn() -> _FakeConnection:
        return fake_conn

    monkeypatch.setattr(db, "connect", return_conn)

    with pytest.raises(RecordInsertionError):
        await db.insert(ExampleModel(pk=0, slug="a", name="A", content="x"))

    assert fake_conn.rollback_calls == 1
    await db.close()


@pytest.mark.asyncio
async def test_async_update_and_delete_raise_for_missing_rows() -> None:
    """Update/delete surface missing-row errors."""
    db = AsyncSqliterDB(memory=True)
    await db.create_table(ExampleModel)

    missing = ExampleModel(
        pk=999,
        slug="gone",
        name="Gone",
        content="gone",
    )
    with pytest.raises(RecordNotFoundError):
        await db.update(missing)

    with pytest.raises(RecordNotFoundError):
        await db.delete(ExampleModel, 999)

    await db.close()


@pytest.mark.asyncio
async def test_async_get_update_and_delete_wrap_sqlite_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Get, update, and delete wrap sqlite failures."""
    db = AsyncSqliterDB(memory=True)
    fake_conn = _FakeConnection(_FakeCursor(execute_error=sqlite3.Error("bad")))
    db.conn = cast("Any", fake_conn)

    async def return_conn() -> _FakeConnection:
        return fake_conn

    monkeypatch.setattr(db, "connect", return_conn)

    with pytest.raises(RecordFetchError):
        await db.get(ExampleModel, 1)

    with pytest.raises(RecordUpdateError):
        await db.update(
            ExampleModel(pk=1, slug="a", name="A", content="updated")
        )

    with pytest.raises(RecordDeletionError):
        await db.delete(ExampleModel, 1)

    assert fake_conn.rollback_calls == 2
    await db.close()


@pytest.mark.asyncio
async def test_async_delete_non_fk_integrity_error_wraps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Delete wraps non-FK integrity errors as deletion failures."""
    db = AsyncSqliterDB(memory=True)
    fake_conn = _FakeConnection(
        _FakeCursor(execute_error=sqlite3.IntegrityError("delete failure"))
    )
    db.conn = cast("Any", fake_conn)

    async def return_conn() -> _FakeConnection:
        return fake_conn

    monkeypatch.setattr(db, "connect", return_conn)

    with pytest.raises(RecordDeletionError):
        await db.delete(ExampleModel, 1)

    assert fake_conn.rollback_calls == 1
    await db.close()


@pytest.mark.asyncio
async def test_async_delete_foreign_key_violation_raises() -> None:
    """Delete wraps FK reference failures in ForeignKeyConstraintError."""
    state = ModelRegistry.snapshot()
    try:

        class Parent(BaseDBModel):
            """Parent model for FK delete failure."""

            name: str

        class Child(BaseDBModel):
            """Child model for FK delete failure."""

            name: str
            parent: ForeignKey[Parent] = ForeignKey(
                Parent,
                on_delete="RESTRICT",
            )

        db = AsyncSqliterDB(memory=True)
        await db.create_table(Parent)
        await db.create_table(Child)
        parent = await db.insert(Parent(name="parent"))
        await db.insert(Child(name="child", parent_id=parent.pk))

        with pytest.raises(ForeignKeyConstraintError):
            await db.delete(Parent, parent.pk)

        await db.close()
    finally:
        ModelRegistry.restore(state)


@pytest.mark.asyncio
async def test_async_create_m2m_junction_tables_import_error_is_ignored(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ImportError in async ORM helper imports is ignored for M2M setup."""
    original_import = builtins.__import__

    def fake_import(
        name: str,
        globals_: Mapping[str, object] | None = None,
        locals_: Mapping[str, object] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> object:
        if name in ("sqliter.orm.m2m", "sqliter.orm.registry"):
            msg = "no orm"
            raise ImportError(msg)
        return original_import(name, globals_, locals_, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    db = AsyncSqliterDB(memory=True)
    await db._create_m2m_junction_tables(ExampleModel)
    await db.close()


@pytest.mark.asyncio
async def test_async_create_m2m_junction_tables_ignores_index_creation_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Async M2M setup keeps going if junction index creation fails."""
    state = ModelRegistry.snapshot()
    try:

        class AsyncTagEdge(BaseDBModel):
            """Tag model for junction-table edge paths."""

            name: str

        class AsyncArticleEdge(BaseDBModel):
            """Article model for junction-table edge paths."""

            title: str
            tags: ManyToMany[AsyncTagEdge] = ManyToMany(AsyncTagEdge)

        db = AsyncSqliterDB(memory=True)
        seen_sql: list[str] = []
        original_execute_sql = db._execute_sql

        async def tracking_execute(sql: str) -> None:
            seen_sql.append(sql)
            if 'CREATE INDEX IF NOT EXISTS "idx_' in sql:
                raise SqlExecutionError(sql)
            await original_execute_sql(sql)

        monkeypatch.setattr(db, "_execute_sql", tracking_execute)
        await db.create_table(AsyncTagEdge)
        await db.create_table(AsyncArticleEdge)

        junction_table = AsyncArticleEdge.tags.junction_table or ""
        assert any(junction_table in sql for sql in seen_sql)
        assert junction_table in await db.get_table_names()
        await db.close()
    finally:
        ModelRegistry.restore(state)


@pytest.mark.asyncio
async def test_async_query_wrappers_cover_cache_and_error_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Async query wrappers cover cached, empty, and sqlite error paths."""
    db = AsyncSqliterDB(memory=True, cache_enabled=True)
    await db.create_table(ExampleModel)
    await db.insert(ExampleModel(slug="a", name="A", content="one"))

    projection = (
        db.select(ExampleModel)
        .group_by("slug")
        .annotate(total=func.count())
        .order("slug")
    )
    assert await projection.fetch_dicts() == [{"slug": "a", "total": 1}]
    assert await projection.fetch_dicts() == [{"slug": "a", "total": 1}]
    with pytest.raises(InvalidProjectionError, match="requires projection"):
        await db.select(ExampleModel).fetch_dicts()

    missing_one = db.select(ExampleModel).filter(slug="missing")
    assert await missing_one.fetch_one() is None

    async def explode_fetch_one(*, fetch_one: bool = False) -> object:
        msg = f"unexpected execute {fetch_one}"
        raise AssertionError(msg)

    monkeypatch.setattr(missing_one, "_execute_query", explode_fetch_one)
    assert await missing_one.fetch_one() is None

    missing_many = db.select(ExampleModel).filter(slug="missing-many")
    assert await missing_many.fetch_all() == []

    monkeypatch.setattr(missing_many, "_execute_query", explode_fetch_one)
    assert await missing_many.fetch_all() == []

    bypassed = db.select(ExampleModel).filter(slug="missing").bypass_cache()
    assert await bypassed.fetch_one() is None
    exists_query = db.select(ExampleModel).filter(slug="missing")
    assert await exists_query.exists() is False

    async def fail_cursor(
        _cursor: object,
        _sql: str,
        _values: object = (),
    ) -> object:
        msg = "bad query"
        raise sqlite3.Error(msg)

    monkeypatch.setattr(db, "execute_cursor", fail_cursor)

    error_query = db.select(ExampleModel).filter(slug="a")
    with pytest.raises(RecordFetchError):
        await error_query.fetch_all()

    error_projection = (
        db.select(ExampleModel).group_by("slug").annotate(total=func.count())
    )
    with pytest.raises(RecordFetchError):
        await error_projection.fetch_dicts()

    await db.close()


@pytest.mark.asyncio
async def test_async_prefetch_internal_edge_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Internal async prefetch helpers cover no-op and nested-empty paths."""
    state = ModelRegistry.snapshot()
    try:

        class EdgeAuthor(BaseDBModel):
            """Author model for async prefetch edge coverage."""

            name: str

        class EdgePublisher(BaseDBModel):
            """Publisher model for async prefetch edge coverage."""

            name: str

        class EdgeBook(BaseDBModel):
            """Book model for async prefetch edge coverage."""

            title: str
            author: ForeignKey[EdgeAuthor] = ForeignKey(
                EdgeAuthor,
                related_name="books",
                on_delete="CASCADE",
            )
            publisher: ForeignKey[EdgePublisher] = ForeignKey(
                EdgePublisher,
                null=True,
                on_delete="SET NULL",
            )

        class EdgeTag(BaseDBModel):
            """Tag model for async M2M prefetch edge coverage."""

            name: str

        class EdgeArticle(BaseDBModel):
            """Article model for async M2M prefetch edge coverage."""

            title: str
            tags: ManyToMany[EdgeTag] = ManyToMany(EdgeTag)

        db = AsyncSqliterDB(memory=True)
        await db.create_table(EdgeAuthor)
        await db.create_table(EdgePublisher)
        await db.create_table(EdgeBook)
        await db.create_table(EdgeTag)
        await db.create_table(EdgeArticle)

        author = await db.insert(EdgeAuthor(name="No books"))
        article = await db.insert(EdgeArticle(title="No tags"))

        query = db.select(EdgeAuthor)
        query._query._prefetch_related_paths = ["books__publisher"]
        await query._execute_prefetch([author])

        reverse_calls: list[list[Any]] = []

        async def fake_reverse(
            _path: str,
            _descriptor: object,
            _instances: list[Any],
            pks: list[Any],
        ) -> None:
            reverse_calls.append(pks)

        monkeypatch.setattr(query, "_prefetch_reverse_fk", fake_reverse)
        await query._prefetch_segment("books", [author, author], EdgeAuthor)
        assert reverse_calls == [[author.pk]]

        transient_author = EdgeAuthor(name="Transient")
        await query._prefetch_segment("books", [transient_author], EdgeAuthor)

        m2m_query = db.select(EdgeArticle)

        def resolve_none(_descriptor: object, _table_name: str) -> None:
            return None

        monkeypatch.setattr(
            m2m_query._query,
            "resolve_m2m_columns",
            resolve_none,
        )
        await m2m_query._prefetch_m2m_for_model(
            "tags",
            EdgeArticle.tags,
            [article],
            [article.pk or 0],
            owner_model=EdgeArticle,
        )

        await db.close()
    finally:
        ModelRegistry.restore(state)


@pytest.mark.asyncio
async def test_async_query_wrapper_methods_and_write_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """with_count, select_related, delete, and update cover wrapper paths."""
    state = ModelRegistry.snapshot()
    try:

        class Author(BaseDBModel):
            """Author model for async query wrapper tests."""

            name: str

        class Book(BaseDBModel):
            """Book model for async query wrapper tests."""

            title: str
            author: ForeignKey[Author] = ForeignKey(
                Author,
                related_name="books",
                on_delete="CASCADE",
            )

        db = AsyncSqliterDB(memory=True)
        await db.create_table(Author)
        await db.create_table(Book)
        author = await db.insert(Author(name="Ada"))
        await db.insert(Book(title="Notes", author_id=author.pk))

        count_query = db.select(Author).with_count("books", alias="book_count")
        assert count_query.select_related() is count_query
        rows = await count_query.fetch_dicts()
        assert rows[0]["pk"] == author.pk
        assert rows[0]["name"] == "Ada"
        assert rows[0]["book_count"] == 1

        single = db.select(Author)
        single._query._prefetch_related_paths = ["ignored"]
        await single._execute_prefetch(Author(name="No PK"))
        await single._execute_prefetch([])

        error_cursor = _FakeCursor(execute_error=sqlite3.Error("bad"))
        fake_conn = _FakeConnection(error_cursor)
        db.conn = cast("Any", fake_conn)

        async def return_conn() -> _FakeConnection:
            return fake_conn

        monkeypatch.setattr(db, "connect", return_conn)

        with pytest.raises(RecordDeletionError):
            await db.select(Book).filter(pk=1).delete()

        with pytest.raises(RecordUpdateError):
            await db.select(Book).filter(pk=1).update({"title": "Updated"})

        assert fake_conn.rollback_calls == 2
        await db.close()
    finally:
        ModelRegistry.restore(state)


@pytest.mark.asyncio
async def test_async_context_manager_rolls_back_on_error(
    temp_db_path: str,
) -> None:
    """Async transaction context rolls back on exception."""
    db = AsyncSqliterDB(temp_db_path, auto_commit=False)
    await db.create_table(ExampleModel)

    error_message = "boom"

    async def fail_transaction() -> None:
        async with db:
            await db.insert(
                ExampleModel(slug="rolled", name="Rolled", content="back")
            )
            raise RuntimeError(error_message)

    with pytest.raises(RuntimeError, match=error_message):
        await fail_transaction()

    assert await db.get(ExampleModel, 1) is None
    await db.close()


@pytest.mark.asyncio
async def test_async_prefetch_related_reverse_fk() -> None:
    """Async queries prefetch reverse-FK relationships."""
    state = ModelRegistry.snapshot()
    try:

        class AsyncAuthor(BaseDBModel):
            """Author model for async prefetch tests."""

            name: str
            email: str

        class AsyncPublisher(BaseDBModel):
            """Publisher model for async prefetch tests."""

            name: str

        class AsyncBook(BaseDBModel):
            """Book model for async reverse-FK prefetch tests."""

            title: str
            year: int
            author: ForeignKey[AsyncAuthor] = ForeignKey(
                AsyncAuthor,
                on_delete="CASCADE",
                related_name="books",
            )
            publisher: ForeignKey[AsyncPublisher] = ForeignKey(
                AsyncPublisher,
                on_delete="SET NULL",
                null=True,
            )

        db = AsyncSqliterDB(memory=True)
        await db.create_table(AsyncAuthor)
        await db.create_table(AsyncPublisher)
        await db.create_table(AsyncBook)

        author = await db.insert(AsyncAuthor(name="Jane", email="jane@test"))
        await db.insert(AsyncBook(title="One", year=1813, author_id=author.pk))
        await db.insert(AsyncBook(title="Two", year=1814, author_id=author.pk))

        authors = await (
            db.select(AsyncAuthor).prefetch_related("books").fetch_all()
        )

        prefetched_author = authors[0]
        cache = prefetched_author.__dict__.get("_prefetch_cache", {})
        assert "books" in cache
        assert [book.title for book in cache["books"]] == ["One", "Two"]

        await db.close()
    finally:
        ModelRegistry.restore(state)


@pytest.mark.asyncio
async def test_async_prefetch_related_m2m() -> None:
    """Async queries prefetch M2M relationships."""
    state = ModelRegistry.snapshot()
    try:

        class AsyncTag(BaseDBModel):
            """Tag model for async M2M prefetch tests."""

            name: str

        class AsyncArticle(BaseDBModel):
            """Article model for async M2M prefetch tests."""

            title: str
            tags: ManyToMany[AsyncTag] = ManyToMany(AsyncTag)

        db = AsyncSqliterDB(memory=True)
        await db.create_table(AsyncTag)
        await db.create_table(AsyncArticle)

        tag_python = await db.insert(AsyncTag(name="python"))
        tag_async = await db.insert(AsyncTag(name="async"))
        article = await db.insert(AsyncArticle(title="Guide"))
        conn = await db.connect()
        cursor = await conn.cursor()
        junction_table = AsyncArticle.tags.junction_table or ""
        col_a, col_b = _m2m_column_names(
            AsyncArticle.get_table_name(),
            AsyncTag.get_table_name(),
        )
        await db.execute_cursor(
            cursor,
            (
                f'INSERT INTO "{junction_table}" '
                f'("{col_a}", "{col_b}") VALUES (?, ?)'
            ),
            [article.pk, tag_python.pk],
        )
        await db.execute_cursor(
            cursor,
            (
                f'INSERT INTO "{junction_table}" '
                f'("{col_a}", "{col_b}") VALUES (?, ?)'
            ),
            [article.pk, tag_async.pk],
        )
        await db.commit()

        articles = await (
            db.select(AsyncArticle).prefetch_related("tags").fetch_all()
        )

        cache = articles[0].__dict__.get("_prefetch_cache", {})
        assert "tags" in cache
        assert {tag.name for tag in cache["tags"]} == {"python", "async"}

        await db.close()
    finally:
        ModelRegistry.restore(state)


@pytest.mark.asyncio
async def test_async_query_projection_fetch_dicts_and_guards() -> None:
    """Projection queries support fetch_dicts and reject model fetches."""
    db = AsyncSqliterDB(memory=True)
    await db.create_table(ExampleModel)
    await db.insert(ExampleModel(slug="a", name="A", content="one"))
    await db.insert(ExampleModel(slug="b", name="B", content="two"))

    query = (
        db.select(ExampleModel)
        .group_by("slug")
        .annotate(total=func.count())
        .order("slug")
    )
    rows = await query.fetch_dicts()
    assert rows == [
        {"slug": "a", "total": 1},
        {"slug": "b", "total": 1},
    ]

    with pytest.raises(InvalidProjectionError):
        await query.fetch_all()

    await db.close()


@pytest.mark.asyncio
async def test_async_query_fetch_first_and_last() -> None:
    """Async query supports fetch_first and fetch_last."""
    db = AsyncSqliterDB(memory=True)
    await db.create_table(ExampleModel)
    await db.insert(ExampleModel(slug="a", name="A", content="one"))
    await db.insert(ExampleModel(slug="b", name="B", content="two"))

    first = await db.select(ExampleModel).order("slug").fetch_first()
    last = await db.select(ExampleModel).order("slug").fetch_last()

    assert first is not None
    assert first.slug == "a"
    assert last is not None
    assert last.slug == "b"
    await db.close()


@pytest.mark.asyncio
async def test_async_query_update_and_delete() -> None:
    """Async bulk query update/delete work and invalidate cache."""
    db = AsyncSqliterDB(memory=True, cache_enabled=True)
    await db.create_table(ExampleModel)
    await db.insert(ExampleModel(slug="a", name="A", content="one"))
    await db.insert(ExampleModel(slug="b", name="B", content="two"))

    count = (
        await db.select(ExampleModel)
        .filter(slug="a")
        .update({"content": "updated"})
    )
    assert count == 1
    updated = await db.select(ExampleModel).filter(slug="a").fetch_one()
    assert updated is not None
    assert updated.content == "updated"

    deleted = await db.select(ExampleModel).filter(slug="b").delete()
    assert deleted == 1
    assert await db.select(ExampleModel).filter(slug="b").exists() is False
    await db.close()


@pytest.mark.asyncio
async def test_async_query_update_rejects_invalid_fields() -> None:
    """Async bulk update validates payload fields."""
    db = AsyncSqliterDB(memory=True)
    await db.create_table(ExampleModel)
    await db.insert(ExampleModel(slug="a", name="A", content="one"))

    with pytest.raises(RecordUpdateError, match="primary key"):
        await db.select(ExampleModel).update({"pk": 1})

    with pytest.raises(RecordUpdateError, match="unknown"):
        await db.select(ExampleModel).update({"unknown": "x"})

    assert await db.select(ExampleModel).update({}) == 0
    await db.close()


@pytest.mark.asyncio
async def test_async_query_builder_chain_methods() -> None:
    """Chain methods cover builder wrappers and still return correct data."""
    db = AsyncSqliterDB(memory=True)
    await db.create_table(ExampleModel)
    await db.insert(ExampleModel(slug="a", name="A", content="one"))
    await db.insert(ExampleModel(slug="b", name="B", content="two"))
    await db.insert(ExampleModel(slug="c", name="C", content="three"))

    query = db.select(ExampleModel, exclude=["content"])
    assert query.fields(["slug"]) is query
    assert query.only("slug") is query
    assert query.exclude(["name"]) is query
    assert query.bypass_cache() is query
    assert query.cache_ttl(5) is query
    assert query.limit(1) is query
    assert query.offset(1) is query
    assert query.order("slug") is query

    rows = await query.fetch_all()

    assert len(rows) == 1
    assert rows[0].slug == "b"
    await db.close()


@pytest.mark.asyncio
async def test_async_query_fields_selects_subset() -> None:
    """fields() mirrors the sync query-builder API."""
    db = AsyncSqliterDB(memory=True)
    await db.create_table(ExampleModel)
    await db.insert(ExampleModel(slug="a", name="A", content="one"))

    result = await db.select(ExampleModel).fields(["name"]).fetch_one()

    assert result is not None
    assert result.name == "A"
    assert result.pk is not None
    await db.close()


@pytest.mark.asyncio
async def test_async_query_only_rejects_multiple_fields() -> None:
    """only() matches the sync single-field contract."""
    db = AsyncSqliterDB(memory=True)
    await db.create_table(ExampleModel)
    query = db.select(ExampleModel)
    only_method = cast("Any", query.only)

    with pytest.raises(TypeError):
        only_method("slug", "name")

    await db.close()


@pytest.mark.asyncio
async def test_async_query_having_filters_grouped_results() -> None:
    """having() is available for async grouped projection queries."""

    class Sale(BaseDBModel):
        """Simple model for aggregate query tests."""

        category: str
        amount: float

        class Meta:
            """Aggregate test table metadata."""

            table_name = "sales_async"

    db = AsyncSqliterDB(memory=True)
    await db.create_table(Sale)
    await db.insert(Sale(category="books", amount=10))
    await db.insert(Sale(category="books", amount=20))
    await db.insert(Sale(category="music", amount=5))

    rows = await (
        db.select(Sale)
        .group_by("category")
        .annotate(total=func.sum("amount"))
        .having(total__gt=15)
        .fetch_dicts()
    )

    assert rows == [{"category": "books", "total": 30.0}]
    await db.close()


@pytest.mark.asyncio
async def test_async_get_cache_stats_tracks_hits_and_resets() -> None:
    """Async DB exposes sync-backed cache statistics."""
    db = AsyncSqliterDB(memory=True, cache_enabled=True)
    await db.create_table(ExampleModel)
    inserted = await db.insert(ExampleModel(slug="a", name="A", content="one"))

    stats = db.get_cache_stats()
    assert stats == {"hits": 0, "misses": 0, "total": 0, "hit_rate": 0.0}

    first = await db.get(ExampleModel, inserted.pk)
    second = await db.get(ExampleModel, inserted.pk)
    stats = db.get_cache_stats()

    assert first is not None
    assert second is not None
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["total"] == 2

    await db.close()
    assert db.get_cache_stats() == {
        "hits": 0,
        "misses": 0,
        "total": 0,
        "hit_rate": 0.0,
    }


@pytest.mark.asyncio
async def test_async_cache_management_wrappers() -> None:
    """Async DB exposes public sync-backed cache clear/reset wrappers."""
    db = AsyncSqliterDB(memory=True, cache_enabled=True)

    db.cache_set("users", "pk:1", {"name": "Ada"})
    assert db.get_cache_stats()["total"] == 0

    hit, _ = db.cache_get("users", "pk:1")
    assert hit is True
    hit, _ = db.cache_get("users", "missing")
    assert hit is False
    stats = db.get_cache_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1

    db.clear_cache()
    hit, _ = db.cache_get("users", "pk:1")
    assert hit is False

    db.reset_cache_stats()
    assert db.get_cache_stats() == {
        "hits": 0,
        "misses": 0,
        "total": 0,
        "hit_rate": 0.0,
    }

    await db.close()


@pytest.mark.asyncio
async def test_async_helper_wrappers_delegate_consistently() -> None:
    """Async helper wrappers should expose shared sync helper behavior."""
    db = AsyncSqliterDB(memory=True)
    instance = ExampleModel(slug="a", name="A", content="one")

    db._set_insert_timestamps(instance, timestamp_override=False)
    mapped = db._map_data_to_db_columns(
        ExampleModel,
        {"slug": "a", "name": "A", "content": "one"},
    )
    select_list = db._build_model_select_list(ExampleModel)
    fields, foreign_keys, fk_columns = db._build_field_definitions(
        ExampleModel,
        ExampleModel.get_primary_key(),
    )

    assert instance.created_at > 0
    assert instance.updated_at > 0
    assert mapped == {"slug": "a", "name": "A", "content": "one"}
    assert (
        select_list
        == '"pk", "created_at", "updated_at", "slug", "name", "content"'
    )
    assert len(fields) >= 1
    assert foreign_keys == []
    assert fk_columns == []
