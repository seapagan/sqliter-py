"""Demo list widget with expandable categories."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.message import Message
from textual.widgets import Tree

from sqliter.tui.demos import DemoRegistry
from sqliter.tui.demos.base import Demo, DemoCategory


class DemoSelected(Message):
    """Message sent when a demo is selected."""

    def __init__(self, demo: Demo) -> None:
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
            cat_node = tree.root.add(
                f"{category.icon} {category.title}",
                data=category,
                expand=category.expanded,
            )
            for demo in category.demos:
                cat_node.add_leaf(
                    f"  {demo.title}",
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
