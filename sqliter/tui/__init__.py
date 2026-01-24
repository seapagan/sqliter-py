"""TUI demo application for SQLiter.

This module provides an interactive terminal-based demonstration of SQLiter
features using the Textual library.

Usage:
    python -m sqliter.tui

Requires:
    pip install sqliter-py[tui]
"""

from __future__ import annotations

from typing import TYPE_CHECKING, NoReturn

if TYPE_CHECKING:
    from sqliter.tui.app import SQLiterDemoApp

_TEXTUAL_AVAILABLE = False
_IMPORT_ERROR: str | None = None

try:
    import textual  # noqa: F401
    _TEXTUAL_AVAILABLE = True
except ImportError as e:
    _IMPORT_ERROR = str(e)


def _missing_dependency_error() -> NoReturn:
    """Raise informative error when textual is not installed."""
    msg = (
        "The SQLiter TUI demo requires the 'textual' library.\n"
        "Install it with: pip install sqliter-py[tui]\n"
        f"Import error: {_IMPORT_ERROR}"
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

    from sqliter.tui.app import SQLiterDemoApp
    return SQLiterDemoApp()


def run() -> None:
    """Run the TUI demo application.

    Raises:
        ImportError: If textual is not installed.
    """
    app = get_app()
    app.run()


__all__ = ["get_app", "run"]
