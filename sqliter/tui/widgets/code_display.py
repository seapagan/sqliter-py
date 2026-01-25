"""Syntax-highlighted code display widget."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.syntax import Syntax
from textual.containers import ScrollableContainer
from textual.css.query import NoMatches
from textual.widgets import Static

if TYPE_CHECKING:  # pragma: no cover
    from textual.app import ComposeResult


class CodeDisplay(ScrollableContainer):
    """Display syntax-highlighted Python code."""

    def __init__(
        self,
        code: str = "",
        *,
        widget_id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the code display.

        Args:
            code: Initial code to display.
            widget_id: Widget ID.
            classes: CSS classes for the widget.
        """
        super().__init__(id=widget_id, classes=classes)
        self._code = code

    def compose(self) -> ComposeResult:
        """Compose the code display."""
        yield Static(id="code-content")

    def on_mount(self) -> None:
        """Initialize the display on mount."""
        self._update_display()

    @property
    def code(self) -> str:
        """Get the current code."""
        return self._code

    @code.setter
    def code(self, value: str) -> None:
        """Set new code and update display."""
        self._code = value
        self._update_display()

    def _update_display(self) -> None:
        """Update the code display with syntax highlighting."""
        try:
            content = self.query_one("#code-content", Static)
        except NoMatches:
            return  # Not mounted yet

        if not self._code:
            content.update("Select a demo to view code")
            return

        # Use Rich's Syntax for highlighting
        syntax = Syntax(
            self._code.strip(),
            "python",
            theme="monokai",
            line_numbers=True,
            word_wrap=True,
        )
        content.update(syntax)

        # Scroll to top when content changes
        self.scroll_home()

    def set_code(self, code: str) -> None:
        """Set the code to display (public API)."""
        self.code = code
