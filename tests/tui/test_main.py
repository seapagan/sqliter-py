"""Tests for the __main__ module entry point."""

from __future__ import annotations

from sqliter.tui import __main__


class TestMainModule:
    """Test the __main__ module execution."""

    def test_main_imports_run(self, mocker) -> None:
        """Test that __main__ imports run correctly."""
        # The run function should be imported
        mocker.patch("sqliter.tui.run")
        assert hasattr(__main__, "run")

    def test_main_module_structure(self) -> None:
        """Test the structure of the __main__ module."""
        # Should import run from the tui module
        assert __main__.__file__.endswith("__main__.py")
