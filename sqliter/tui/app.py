"""Main SQLiter TUI demo application."""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, ClassVar, cast

from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import (
    Container,
    Horizontal,
    Vertical,
    VerticalScroll,
)
from textual.css.query import NoMatches
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Markdown, Tree

if TYPE_CHECKING:  # pragma: no cover
    from sqliter.tui.demos.base import Demo

from sqliter.tui.demos import DemoRegistry
from sqliter.tui.runner import run_demo
from sqliter.tui.widgets import (
    CodeDisplay,
    DemoList,
    DemoSelected,
    OutputDisplay,
)


class HelpScreen(ModalScreen[None]):
    """Modal help screen."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "dismiss", "Close"),
        Binding("q", "dismiss", "Close"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the help screen."""
        with VerticalScroll(id="help-scroll"):
            yield Markdown(
                """
# SQLiter Demo - Help

## Navigation

| Key | Action |
|-----|--------|
| Up/Down or j/k | Navigate demo list |
| Left/Right or h/l | Collapse/expand category |
| Enter | Select demo / Run demo |
| Tab | Move focus between panels |

## Actions

| Key | Action |
|-----|--------|
| F5 | Run selected demo |
| F8 | Clear output |
| ? or F1 | Show this help |
| q | Quit application |

## Mouse

- Click categories to expand/collapse
- Click demos to select and view code
- Click buttons to run/clear

Press Escape or q to close this help.
                """,
                id="help-content",
            )


class SQLiterDemoApp(App[None]):
    """Main SQLiter TUI demo application."""

    CSS_PATH = "styles/app.tcss"
    TITLE = "SQLiter Interactive Demo"

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("q", "quit", "Quit", show=True, priority=True),
        Binding("f5", "run_demo", "Run", show=True),
        Binding("f8", "clear_output", "Clear", show=True),
        Binding("question_mark", "show_help", "Help", show=True),
        Binding("f1", "show_help", show=False),
        Binding("j", "tree_cursor_down", show=False),
        Binding("k", "tree_cursor_up", show=False),
    ]

    def __init__(self) -> None:
        """Initialize the application."""
        super().__init__()
        self._current_demo: Demo | None = None

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield Header()
        with Container(id="main-container"):
            yield DemoList(id="demo-list")
            with Vertical(id="right-panel"):
                yield CodeDisplay(widget_id="code-display")
                yield OutputDisplay(widget_id="output-display")
                with Horizontal(id="button-bar"):
                    yield Button(
                        "Run Demo (F5)", id="run-btn", variant="primary"
                    )
                    yield Button("Clear Output (F8)", id="clear-btn")
        yield Footer()

    def on_mount(self) -> None:
        """Set initial focus on the demo list."""
        with suppress(NoMatches):
            demo_list = self.query_one("#demo-list", DemoList)
            tree = demo_list.query_one("#demo-tree", Tree)
            tree.focus()

    def on_demo_selected(self, event: DemoSelected) -> None:
        """Handle demo selection from the list."""
        self._current_demo = event.demo
        code_display = self.query_one("#code-display", CodeDisplay)
        code_display.set_code(DemoRegistry.get_demo_code(event.demo.id))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "run-btn":
            self.action_run_demo()
        elif event.button.id == "clear-btn":
            self.action_clear_output()

    def action_run_demo(self) -> None:
        """Run the currently selected demo."""
        if self._current_demo is None:
            output_display = self.query_one("#output-display", OutputDisplay)
            output_display.show_output(
                "Please select a demo first.", success=False
            )
            return

        result = run_demo(self._current_demo)
        output_display = self.query_one("#output-display", OutputDisplay)

        if result.success:
            output_display.show_output(result.output, success=True)
        else:
            output_display.show_error(
                result.error or "Unknown error",
                result.traceback,
            )

    def action_clear_output(self) -> None:
        """Clear the output display."""
        output_display = self.query_one("#output-display", OutputDisplay)
        output_display.clear()

    def action_show_help(self) -> None:
        """Show the help screen."""
        self.push_screen(HelpScreen())

    def action_tree_cursor_down(self) -> None:
        """Move cursor down in the tree (vim-style j key)."""
        try:
            demo_list = self.query_one(DemoList)
            tree = cast("Tree[object]", demo_list.query_one("#demo-tree"))
            tree.action_cursor_down()
        except NoMatches:
            pass  # Tree might not be focused

    def action_tree_cursor_up(self) -> None:
        """Move cursor up in the tree (vim-style k key)."""
        try:
            demo_list = self.query_one(DemoList)
            tree = cast("Tree[object]", demo_list.query_one("#demo-tree"))
            tree.action_cursor_up()
        except NoMatches:
            pass  # Tree might not be focused
