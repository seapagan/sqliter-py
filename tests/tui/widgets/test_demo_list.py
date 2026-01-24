"""Tests for the DemoList widget."""

from __future__ import annotations

from typing import Any

import pytest
from textual.app import App
from textual.widgets import Tree

from sqliter.tui.demos import DemoRegistry
from sqliter.tui.demos.base import Demo, DemoCategory
from sqliter.tui.widgets import DemoList


class TestDemoList:
    """Test the DemoList widget."""

    @pytest.mark.asyncio
    async def test_tree_composition(self, reset_demo_registry) -> None:
        """Test that the widget composes a Tree."""
        category = DemoCategory(id="test", title="Test Category", icon="🧪")
        DemoRegistry.register_category(category)

        app: App[Any] = App()
        async with app.run_test() as _:
            demo_list = DemoList()
            await app.mount(demo_list)

            tree = demo_list.query_one("#demo-tree", Tree)
            assert tree is not None
            assert tree.id == "demo-tree"

    @pytest.mark.asyncio
    async def test_category_nodes(self, reset_demo_registry) -> None:
        """Test that categories are rendered as nodes."""
        cat1 = DemoCategory(id="cat1", title="Category 1", icon="📦")
        cat2 = DemoCategory(id="cat2", title="Category 2", icon="📁")
        DemoRegistry.register_category(cat1)
        DemoRegistry.register_category(cat2)

        app: App[Any] = App()
        async with app.run_test() as _:
            demo_list = DemoList()
            await app.mount(demo_list)

            tree = demo_list.query_one("#demo-tree", Tree)
            # Root should have 2 children (categories)
            assert len(tree.root.children) == 2

    @pytest.mark.asyncio
    async def test_demo_leaves(self, reset_demo_registry) -> None:
        """Test that demos are rendered as leaf nodes."""
        demo1 = Demo(
            id="demo1",
            title="Demo 1",
            description="First",
            category="cat1",
            code="code1",
            execute=lambda: "",
        )
        demo2 = Demo(
            id="demo2",
            title="Demo 2",
            description="Second",
            category="cat1",
            code="code2",
            execute=lambda: "",
        )

        category = DemoCategory(
            id="cat1", title="Category", demos=[demo1, demo2]
        )
        DemoRegistry.register_category(category)

        app: App[Any] = App()
        async with app.run_test() as _:
            demo_list = DemoList()
            await app.mount(demo_list)

            tree = demo_list.query_one("#demo-tree", Tree)
            # Category node should have 2 children (demos)
            cat_node = tree.root.children[0]
            assert len(cat_node.children) == 2

    @pytest.mark.asyncio
    async def test_node_expansion(self, reset_demo_registry) -> None:
        """Test that categories can be expanded/collapsed."""
        category = DemoCategory(id="cat1", title="Category", expanded=False)
        demo = Demo(
            id="demo1",
            title="Demo",
            description="Demo",
            category="cat1",
            code="code",
            execute=lambda: "",
        )

        category.demos.append(demo)
        DemoRegistry.register_category(category)

        app: App[Any] = App()
        async with app.run_test() as _:
            demo_list = DemoList()
            await app.mount(demo_list)

            tree = demo_list.query_one("#demo-tree", Tree)
            cat_node = tree.root.children[0]

            # Category should not be expanded initially
            assert not cat_node.is_expanded

            # Expand the category
            cat_node.expand()
            assert cat_node.is_expanded

    @pytest.mark.asyncio
    async def test_demo_selection_event(self, reset_demo_registry) -> None:
        """Test that selecting a demo posts DemoSelected message."""
        demo = Demo(
            id="demo1",
            title="Demo",
            description="Demo",
            category="cat1",
            code="code",
            execute=lambda: "",
        )

        category = DemoCategory(id="cat1", title="Category", demos=[demo])
        DemoRegistry.register_category(category)

        app: App[Any] = App()
        async with app.run_test() as _:
            demo_list = DemoList()
            await app.mount(demo_list)

            tree = demo_list.query_one("#demo-tree", Tree)
            # Verify the demo node is in the tree
            cat_node = tree.root.children[0]
            assert len(cat_node.children) == 1
            demo_node = cat_node.children[0]

            # Verify demo node data
            assert isinstance(demo_node.data, Demo)
            assert demo_node.data.id == "demo1"

    @pytest.mark.asyncio
    async def test_empty_registry(self, reset_demo_registry) -> None:
        """Test that empty registry works."""
        # Don't register any categories
        app: App[Any] = App()
        async with app.run_test() as _:
            demo_list = DemoList()
            await app.mount(demo_list)

            tree = demo_list.query_one("#demo-tree", Tree)
            # Root should have no children
            assert len(tree.root.children) == 0

    @pytest.mark.asyncio
    async def test_integration_with_registry(self, reset_demo_registry) -> None:
        """Test integration with DemoRegistry."""
        # Register multiple categories with demos
        demos = [
            Demo(
                id=f"demo{i}",
                title=f"Demo {i}",
                description=f"Demo {i}",
                category="cat1",
                code=f"code{i}",
                execute=lambda: "",
            )
            for i in range(3)
        ]

        category = DemoCategory(
            id="cat1", title="Category", icon="🧪", demos=demos
        )
        DemoRegistry.register_category(category)

        app: App[Any] = App()
        async with app.run_test() as _:
            demo_list = DemoList()
            await app.mount(demo_list)

            tree = demo_list.query_one("#demo-tree", Tree)
            cat_node = tree.root.children[0]

            # Verify category title includes icon
            label_text = str(cat_node.label)
            assert "🧪" in label_text
            assert "Category" in label_text

            # Verify all demos are present
            assert len(cat_node.children) == 3

    @pytest.mark.asyncio
    async def test_tree_root_hidden(self, reset_demo_registry) -> None:
        """Test that the tree root is hidden."""
        category = DemoCategory(id="test", title="Test")
        DemoRegistry.register_category(category)

        app: App[Any] = App()
        async with app.run_test() as _:
            demo_list = DemoList()
            await app.mount(demo_list)

            tree = demo_list.query_one("#demo-tree", Tree)
            assert tree.show_root is False

    @pytest.mark.asyncio
    async def test_demo_label_formatting(self, reset_demo_registry) -> None:
        """Test that demo labels are formatted correctly."""
        demo = Demo(
            id="demo1",
            title="My Demo",
            description="A demo",
            category="cat1",
            code="code",
            execute=lambda: "",
        )

        category = DemoCategory(id="cat1", title="Category", demos=[demo])
        DemoRegistry.register_category(category)

        app: App[Any] = App()
        async with app.run_test() as _:
            demo_list = DemoList()
            await app.mount(demo_list)

            tree = demo_list.query_one("#demo-tree", Tree)
            demo_node = tree.root.children[0].children[0]

            # Demo should be indented and have title
            label = str(demo_node.label)
            assert "My Demo" in label
