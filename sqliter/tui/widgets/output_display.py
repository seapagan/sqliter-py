"""Output display widget with status indication."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.text import Text
from textual.containers import ScrollableContainer
from textual.widgets import Static

if TYPE_CHECKING:  # pragma: no cover
    from textual.app import ComposeResult


class OutputDisplay(ScrollableContainer):
    """Display demo execution output with status styling."""

    _PLACEHOLDER = "Run a demo to see output here"

    def __init__(
        self,
        *,
        widget_id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the output display.

        Args:
            widget_id: Widget ID.
            classes: CSS classes for the widget.
        """
        super().__init__(id=widget_id, classes=classes)

    def compose(self) -> ComposeResult:
        """Compose the output display."""
        yield Static(self._PLACEHOLDER, id="output-content")

    def show_output(self, output: str, *, success: bool = True) -> None:
        """Display output from demo execution.

        Args:
            output: The output text to display
            success: Whether the demo ran successfully
        """
        content = self.query_one("#output-content", Static)

        self.remove_class("error", "success")
        self.add_class("success" if success else "error")

        if success:
            text = Text()
            text.append("Success\n\n", style="bold green")
            text.append(output)
        else:
            text = Text()
            text.append("Error\n\n", style="bold red")
            text.append(output, style="red")

        content.update(text)
        self.scroll_home()

    def show_error(
        self,
        error: str,
        traceback_str: str | None = None,
    ) -> None:
        """Display an error message.

        Args:
            error: The error message
            traceback_str: Optional full traceback
        """
        content = self.query_one("#output-content", Static)

        self.remove_class("error", "success")
        self.add_class("error")

        text = Text()
        text.append("Error\n\n", style="bold red")
        text.append(error, style="red")
        if traceback_str:
            text.append("\n\nTraceback:\n", style="bold")
            text.append(traceback_str, style="dim red")

        content.update(text)
        self.scroll_home()

    def clear(self) -> None:
        """Clear the output display."""
        content = self.query_one("#output-content", Static)
        content.update(self._PLACEHOLDER)
        self.remove_class("error", "success")
