"""Tests for the TUI module entry points."""

from __future__ import annotations

import pytest

import sqliter.tui
from sqliter.tui import (
    _TEXTUAL_AVAILABLE,
    _missing_dependency_error,
    get_app,
    run,
)
from sqliter.tui.app import SQLiterDemoApp

# Error message for missing textual dependency
_MISSING_DEPENDENCY_ERROR = (
    "The SQLiter TUI demo requires the 'textual' library.\n"
    "Install it with: uv add sqliter-py[demo]\n"
)


class TestMissingDependencyError:
    """Test the _missing_dependency_error function."""

    def test_missing_dependency_error_raises_import_error(self) -> None:
        """Test that _missing_dependency_error raises ImportError."""
        with pytest.raises(ImportError) as exc_info:
            _missing_dependency_error()
        assert "textual" in str(exc_info.value)
        assert "uv add" in str(exc_info.value)


class TestGetApp:
    """Test the get_app function."""

    @pytest.mark.skipif(not _TEXTUAL_AVAILABLE, reason="textual not installed")
    def test_get_app_with_textual(self) -> None:
        """Test that get_app returns an app when textual is available."""
        app = get_app()
        assert isinstance(app, SQLiterDemoApp)

    def test_get_app_without_textual_raises_import_error(self, mocker) -> None:
        """Test get_app raises ImportError when textual is not available."""
        # Mock _TEXTUAL_AVAILABLE to False
        mocker.patch("sqliter.tui._TEXTUAL_AVAILABLE", False)

        # Now get_app should raise ImportError
        with pytest.raises(ImportError) as exc_info:
            get_app()
        assert "textual" in str(exc_info.value)


class TestRunFunction:
    """Test the run function."""

    @pytest.mark.skipif(not _TEXTUAL_AVAILABLE, reason="textual not installed")
    def test_run_calls_app_run(self, mocker) -> None:
        """Test that run() calls app.run()."""
        mock_run = mocker.patch("sqliter.tui.app.SQLiterDemoApp.run")
        run()
        mock_run.assert_called_once()


class TestModuleExports:
    """Test module-level exports."""

    def test_module_exports(self) -> None:
        """Test that __all__ exports the correct functions."""
        assert "get_app" in sqliter.tui.__all__
        assert "run" in sqliter.tui.__all__
        assert len(sqliter.tui.__all__) == 2

    @pytest.mark.skipif(not _TEXTUAL_AVAILABLE, reason="textual not installed")
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
        # This test verifies the flag matches actual textual availability
        try:
            import textual  # noqa: F401, PLC0415

            assert _TEXTUAL_AVAILABLE is True
        except ImportError:
            assert _TEXTUAL_AVAILABLE is False
