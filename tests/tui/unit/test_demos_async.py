"""Unit tests for async demo functions.

These tests directly call the demo execution functions to verify they work
correctly without needing to run the full TUI application.
"""

from __future__ import annotations

import builtins
import importlib
import sys
from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

from sqliter.tui.demos import async_demos
from sqliter.tui.demos.async_demos import (
    _demo_code,
    _run_async_bulk,
    _run_async_conn,
    _run_async_context,
    _run_async_crud,
    _run_async_fk_eager,
    _run_async_fk_lazy,
    _run_async_query,
    _run_async_reverse,
    _run_async_txn,
    _unavailable,
)
from sqliter.tui.demos.base import Demo

if TYPE_CHECKING:
    from collections.abc import Mapping

    import pytest
    from pytest_mock import MockerFixture


class TestUnavailable:
    """Test the _unavailable helper."""

    def test_returns_install_instructions(self) -> None:
        """Returns a message with install instructions."""
        msg = _unavailable("Test Demo")
        assert "Async demo 'Test Demo' requires aiosqlite" in msg
        assert "pip install sqliter-py[async]" in msg
        assert "pip install sqliter-py[full]" in msg


class TestAsyncConnDemo:
    """Test the async connection demo."""

    def test_returns_output(self) -> None:
        """Test that connection demo returns expected output."""
        output = _run_async_conn()
        assert "Created database:" in output
        assert "Is memory: True" in output
        assert "Filename: None" in output
        assert "Connected: True" in output
        assert "After close: False" in output


class TestAsyncContextDemo:
    """Test the async context manager demo."""

    def test_returns_output(self) -> None:
        """Test that context manager demo returns expected output."""
        output = _run_async_context()
        assert "Inserted: Learn async SQLiter" in output
        assert "Transaction auto-commits on exit" in output
        assert "After context: connected=True" in output


class TestAsyncCrudDemo:
    """Test the async CRUD demo."""

    def test_returns_output(self) -> None:
        """Test that CRUD demo returns expected output."""
        output = _run_async_crud()
        assert "Inserted: Widget" in output
        assert "Fetched: Widget" in output
        assert "Updated price: 12.99" in output
        assert "After delete: None" in output


class TestAsyncBulkDemo:
    """Test the async bulk insert demo."""

    def test_returns_output(self) -> None:
        """Test that bulk insert demo returns expected output."""
        output = _run_async_bulk()
        assert "Inserted 3 tags:" in output
        assert "python" in output
        assert "async" in output
        assert "sqlite" in output
        assert "Total in DB: 3" in output


class TestAsyncQueryDemo:
    """Test the async queries demo."""

    def test_returns_output(self) -> None:
        """Test that queries demo returns expected output."""
        output = _run_async_query()
        assert "All items: 4" in output
        assert "qty > 4:" in output
        assert "Most stock: Banana (12)" in output
        assert "Low-stock count:" in output
        assert "Apple exists: True" in output


class TestAsyncFkLazyDemo:
    """Test the async FK lazy loading demo."""

    def test_returns_output(self) -> None:
        """Test that FK lazy loading demo returns expected output."""
        output = _run_async_fk_lazy()
        assert "Book: The Hobbit" in output
        assert "Author: J.R.R. Tolkien" in output
        assert "Loaded via: await book.author.fetch()" in output


class TestAsyncFkEagerDemo:
    """Test the async FK eager loading demo."""

    def test_returns_output(self) -> None:
        """Test that FK eager loading demo returns expected output."""
        output = _run_async_fk_eager()
        assert "Pride and Prejudice by Jane Austen" in output
        assert "Emma by Jane Austen" in output
        assert "Loaded 2 books with eager FK" in output


class TestAsyncReverseDemo:
    """Test the async reverse relationship demo."""

    def test_returns_output(self) -> None:
        """Test that reverse relationship demo returns expected output."""
        output = _run_async_reverse()
        assert "Author: Charles Dickens" in output
        assert "Oliver Twist" in output
        assert "Great Expectations" in output
        assert "Total via .count(): 2" in output


class TestAsyncTxnDemo:
    """Test the async transaction rollback demo."""

    def test_returns_output(self) -> None:
        """Test that transaction demo returns expected output."""
        output = _run_async_txn()
        assert "Initial: Alice=$100.0" in output
        assert "Inside txn: deducted $50" in output
        assert "Error — transaction rolled back" in output
        assert "Restored: Alice=$100.0" in output
        assert "Rollback confirmed" in output


class TestDemoCode:
    """Test the _demo_code code extractor."""

    def test_strips_availability_guard(self) -> None:
        """Availability guard lines are removed from display code."""
        code = _demo_code(_run_async_conn)
        assert "_ASYNC_AVAILABLE" not in code
        assert "_run_async(" not in code

    def test_strips_unlink(self) -> None:
        """File cleanup (.unlink) lines are removed from display code."""
        code = _demo_code(_run_async_txn)
        assert ".unlink(" not in code

    def test_produces_non_empty_output(self) -> None:
        """Each demo produces non-empty display code."""
        for func in [
            _run_async_conn,
            _run_async_context,
            _run_async_crud,
            _run_async_bulk,
            _run_async_query,
            _run_async_fk_lazy,
            _run_async_fk_eager,
            _run_async_reverse,
            _run_async_txn,
        ]:
            code = _demo_code(func)
            assert len(code.strip()) > 0, (
                f"_demo_code({func.__name__}) is empty"
            )

    def test_leading_blank_lines_removed(self) -> None:
        """Leading blank lines in extracted code are stripped."""
        source = "\n\n\n    def fake():\n        pass\n"
        with patch(
            "sqliter.tui.demos.async_demos.extract_demo_code",
            return_value=source,
        ):
            result = _demo_code(_run_async_conn)
        assert not result.startswith("\n")


class TestUnavailablePath:
    """Test the fallback when async extras are not installed."""

    def test_conn_returns_unavailable(self) -> None:
        """Demo returns install message when async is unavailable."""
        with patch.object(async_demos, "_ASYNC_AVAILABLE", False):
            output = _run_async_conn()
        assert "requires aiosqlite" in output

    def test_context_returns_unavailable(self) -> None:
        """Demo returns install message when async is unavailable."""
        with patch.object(async_demos, "_ASYNC_AVAILABLE", False):
            output = _run_async_context()
        assert "requires aiosqlite" in output

    def test_crud_returns_unavailable(self) -> None:
        """Demo returns install message when async is unavailable."""
        with patch.object(async_demos, "_ASYNC_AVAILABLE", False):
            output = _run_async_crud()
        assert "requires aiosqlite" in output

    def test_bulk_returns_unavailable(self) -> None:
        """Demo returns install message when async is unavailable."""
        with patch.object(async_demos, "_ASYNC_AVAILABLE", False):
            output = _run_async_bulk()
        assert "requires aiosqlite" in output

    def test_query_returns_unavailable(self) -> None:
        """Demo returns install message when async is unavailable."""
        with patch.object(async_demos, "_ASYNC_AVAILABLE", False):
            output = _run_async_query()
        assert "requires aiosqlite" in output

    def test_fk_lazy_returns_unavailable(self) -> None:
        """Demo returns install message when async is unavailable."""
        with patch.object(async_demos, "_ASYNC_AVAILABLE", False):
            output = _run_async_fk_lazy()
        assert "requires aiosqlite" in output

    def test_fk_eager_returns_unavailable(self) -> None:
        """Demo returns install message when async is unavailable."""
        with patch.object(async_demos, "_ASYNC_AVAILABLE", False):
            output = _run_async_fk_eager()
        assert "requires aiosqlite" in output

    def test_reverse_returns_unavailable(self) -> None:
        """Demo returns install message when async is unavailable."""
        with patch.object(async_demos, "_ASYNC_AVAILABLE", False):
            output = _run_async_reverse()
        assert "requires aiosqlite" in output

    def test_txn_returns_unavailable(self) -> None:
        """Demo returns install message when async is unavailable."""
        with patch.object(async_demos, "_ASYNC_AVAILABLE", False):
            output = _run_async_txn()
        assert "requires aiosqlite" in output


class TestGetCategory:
    """Test the get_category function."""

    def test_get_category_returns_valid_category(self) -> None:
        """Test that get_category returns a valid DemoCategory."""
        category = async_demos.get_category()

        assert category.id == "async_support"
        assert category.title == "Async Support"
        assert category.icon == ""
        assert len(category.demos) == 9

    def test_get_category_demos_have_required_fields(self) -> None:
        """Test that all demos have required metadata."""
        category = async_demos.get_category()

        for demo in category.demos:
            assert demo.id
            assert demo.title
            assert demo.description
            assert demo.category == "async_support"
            assert demo.code
            assert callable(demo.execute)

    def test_all_demos_are_executable(self) -> None:
        """Test that all demo execute functions work."""
        category = async_demos.get_category()

        for demo in category.demos:
            output = demo.execute()
            assert isinstance(output, str)
            assert len(output) > 0

    def test_demo_has_correct_metadata(self) -> None:
        """Test that all demos have required metadata."""
        category = async_demos.get_category()

        for demo in category.demos:
            assert isinstance(demo, Demo)
            assert demo.id is not None
            assert demo.title is not None
            assert demo.description is not None
            assert demo.category == "async_support"


class TestImportErrorFallback:
    """Test that the module handles missing async imports gracefully."""

    def test_async_available_false_when_import_fails(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Module sets _ASYNC_AVAILABLE=False when async imports fail."""
        real_import = builtins.__import__

        def fake_import(
            name: str,
            globals_: Mapping[str, object] | None = None,
            locals_: Mapping[str, object] | None = None,
            fromlist: tuple[str, ...] = (),
            level: int = 0,
        ) -> object:
            if name in ("sqliter.asyncio", "sqliter.asyncio.orm"):
                msg = f"No module named '{name}'"
                raise ImportError(msg)
            return real_import(name, globals_, locals_, fromlist, level)

        monkeypatch.setitem(sys.modules, "sqliter.asyncio", None)
        monkeypatch.setitem(sys.modules, "sqliter.asyncio.orm", None)
        monkeypatch.setattr(builtins, "__import__", fake_import)
        monkeypatch.delitem(
            sys.modules, "sqliter.tui.demos.async_demos", raising=False
        )
        # importlib.import_module also sets the attribute on the
        # parent package, so save it for monkeypatch to restore.
        parent = sys.modules["sqliter.tui.demos"]
        monkeypatch.setattr(parent, "async_demos", parent.async_demos)

        module = importlib.import_module("sqliter.tui.demos.async_demos")
        assert module._ASYNC_AVAILABLE is False
        output = module._run_async_conn()
        assert "requires aiosqlite" in output


class TestGuardClauses:
    """Test defensive early-return paths in demo functions."""

    def test_fk_lazy_returns_early_when_get_is_none(
        self, mocker: MockerFixture
    ) -> None:
        """FK lazy demo returns early when db.get returns None."""
        mock_db = AsyncMock()
        mock_db.insert = AsyncMock(
            side_effect=[
                SimpleNamespace(pk=1),
                SimpleNamespace(pk=2),
            ]
        )
        mock_db.get = AsyncMock(return_value=None)
        mocker.patch(
            "sqliter.tui.demos.async_demos.AsyncSqliterDB",
            return_value=mock_db,
        )
        output = _run_async_fk_lazy()
        assert "Author:" not in output
        assert "Loaded via:" not in output

    def test_reverse_returns_early_when_get_is_none(
        self, mocker: MockerFixture
    ) -> None:
        """Reverse demo returns early when db.get returns None."""
        mock_db = AsyncMock()
        mock_db.insert = AsyncMock(
            side_effect=[
                SimpleNamespace(pk=1),
                SimpleNamespace(pk=2),
                SimpleNamespace(pk=3),
            ]
        )
        mock_db.get = AsyncMock(return_value=None)
        mocker.patch(
            "sqliter.tui.demos.async_demos.AsyncSqliterDB",
            return_value=mock_db,
        )
        output = _run_async_reverse()
        assert "Author:" not in output
        assert "Books" not in output
