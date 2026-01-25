"""Demo list widget with expandable categories."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.containers import ScrollableContainer
from textual.message import Message
from textual.widgets import Tree

from sqliter.tui.demos import DemoRegistry
from sqliter.tui.demos.base import Demo, DemoCategory

if TYPE_CHECKING:  # pragma: no cover
    from textual.app import ComposeResult


class DemoSelected(Message):
    """Message sent when a demo is selected."""

    def __init__(self, demo: Demo) -> None:
        """Initialize the message.

        Args:
            demo: The demo that was selected.
        """
        self.demo = demo
        super().__init__()


class DemoList(ScrollableContainer):
    """Scrollable tree of demo categories and items."""

    def compose(self) -> ComposeResult:
        """Compose the demo tree."""
        tree: Tree[Demo | DemoCategory] = Tree("SQLiter Demos", id="demo-tree")
        tree.show_root = False

        # Populate tree with categories and demos
        for category in DemoRegistry.get_categories():
            label = (
                f"{category.icon} {category.title}"
                if category.icon
                else category.title
            )
            cat_node = tree.root.add(
                label,
                data=category,
                expand=category.expanded,
            )
            for demo in category.demos:
                cat_node.add_leaf(
                    demo.title,
                    data=demo,
                )

        yield tree

    def on_tree_node_selected(
        self,
        event: Tree.NodeSelected[Demo | DemoCategory],
    ) -> None:
        """Handle tree node selection."""
        if isinstance(event.node.data, Demo):
            self.post_message(DemoSelected(event.node.data))
