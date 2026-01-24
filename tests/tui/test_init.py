"""Tests for the TUI module entry points."""

from __future__ import annotations

from unittest import mock

import pytest

import sqliter.tui
from sqliter.tui import (
    _TEXTUAL_AVAILABLE,
    SQLiterDemoApp,
    _missing_dependency_error,
    get_app,
    run,
)

# Error message for missing textual dependency
_MISSING_DEPENDENCY_ERROR = (
    "The SQLiter TUI demo requires the 'textual' library.\n"
    "Install it with: pip install sqliter-py[tui]\n"
)


class TestMissingDependencyError:
    """Test the _missing_dependency_error function."""

    def test_missing_dependency_error_raises_import_error(self) -> None:
        """Test that _missing_dependency_error raises ImportError."""
        with pytest.raises(ImportError) as exc_info:
            _missing_dependency_error()
        assert "textual" in str(exc_info.value)
        assert "pip install" in str(exc_info.value)


class TestGetApp:
    """Test the get_app function."""

    def test_get_app_with_textual(self) -> None:
        """Test that get_app returns an app when textual is available."""
        app = get_app()
        assert isinstance(app, SQLiterDemoApp)


class TestRunFunction:
    """Test the run function."""

    def test_run_calls_app_run(self) -> None:
        """Test that run() calls app.run()."""
        with mock.patch("sqliter.tui.SQLiterDemoApp.run") as mock_run:
            run()
            mock_run.assert_called_once()


class TestModuleExports:
    """Test module-level exports."""

    def test_module_exports(self) -> None:
        """Test that __all__ exports the correct functions."""
        assert "get_app" in sqliter.tui.__all__
        assert "run" in sqliter.tui.__all__
        assert len(sqliter.tui.__all__) == 2

    def test_sqliter_demo_app_import(self) -> None:
        """Test that SQLiterDemoApp can be imported."""
        assert SQLiterDemoApp is not None

    def test_get_app_is_callable(self) -> None:
        """Test that get_app is callable."""
        assert callable(get_app)

    def test_run_is_callable(self) -> None:
        """Test that run is callable."""
        assert callable(run)

    def test_textual_available_flag(self) -> None:
        """Test that textual availability flag is set correctly."""
        # Since we're running with textual installed, it should be True
        assert _TEXTUAL_AVAILABLE is True
