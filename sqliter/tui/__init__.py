"""TUI demo application for SQLiter.

This module provides an interactive terminal-based demonstration of SQLiter
features using the Textual library.

Usage:
    python -m sqliter.tui
    # or
    sqliter-demo

Requires:
    pip install sqliter-py[demo]
"""

from __future__ import annotations

from importlib.util import find_spec

from sqliter.tui.app import SQLiterDemoApp

_TEXTUAL_AVAILABLE = find_spec("textual") is not None


def _missing_dependency_error() -> None:
    """Raise informative error when textual is not installed."""
    msg = (
        "The SQLiter TUI demo requires the 'textual' library.\n"
        "Install it with: pip install sqliter-py[demo]\n"
    )
    raise ImportError(msg)


def get_app() -> SQLiterDemoApp:
    """Get the TUI application instance.

    Returns:
        The SQLiterDemoApp instance.

    Raises:
        ImportError: If textual is not installed.
    """
    if not _TEXTUAL_AVAILABLE:
        _missing_dependency_error()

    return SQLiterDemoApp()


def run() -> None:
    """Run the TUI demo application.

    Raises:
        ImportError: If textual is not installed.
    """
    app = get_app()
    app.run()


__all__ = ["get_app", "run"]
