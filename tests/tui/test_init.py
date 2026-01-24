"""Tests for the TUI module entry points."""

from __future__ import annotations

import sqliter.tui
from sqliter.tui import _TEXTUAL_AVAILABLE, SQLiterDemoApp, get_app, run


class TestGetApp:
    """Test the get_app function."""

    def test_get_app_with_textual(self) -> None:
        """Test that get_app returns an app when textual is available."""
        app = get_app()
        assert isinstance(app, SQLiterDemoApp)


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
