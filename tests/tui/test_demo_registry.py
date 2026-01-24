"""Tests for the demo registry."""

from __future__ import annotations

from sqliter.tui.demos import DemoRegistry
from sqliter.tui.demos.base import Demo, DemoCategory


class TestDemoRegistry:
    """Test the DemoRegistry class."""

    def test_register_category(self, reset_demo_registry) -> None:
        """Test registering a single category."""
        category = DemoCategory(
            id="test_category",
            title="Test Category",
            icon="🧪",
        )

        DemoRegistry.register_category(category)

        categories = DemoRegistry.get_categories()
        assert len(categories) == 1
        assert categories[0] == category

    def test_register_multiple_categories(self, reset_demo_registry) -> None:
        """Test registering multiple categories."""
        cat1 = DemoCategory(id="cat1", title="Category 1")
        cat2 = DemoCategory(id="cat2", title="Category 2")
        cat3 = DemoCategory(id="cat3", title="Category 3")

        DemoRegistry.register_category(cat1)
        DemoRegistry.register_category(cat2)
        DemoRegistry.register_category(cat3)

        categories = DemoRegistry.get_categories()
        assert len(categories) == 3
        assert categories == [cat1, cat2, cat3]

    def test_get_demo_by_id(self, reset_demo_registry) -> None:
        """Test retrieving a demo by its ID."""
        demo = Demo(
            id="test_demo",
            title="Test Demo",
            description="Test",
            category="test",
            code="code",
            execute=lambda: "output",
        )

        category = DemoCategory(id="test", title="Test", demos=[demo])
        DemoRegistry.register_category(category)

        retrieved = DemoRegistry.get_demo("test_demo")
        assert retrieved is not None
        assert retrieved.id == "test_demo"
        assert retrieved.title == "Test Demo"

    def test_get_demo_not_found(self, reset_demo_registry) -> None:
        """Test retrieving a non-existent demo."""
        result = DemoRegistry.get_demo("nonexistent")
        assert result is None

    def test_get_demo_code_with_setup(self, reset_demo_registry) -> None:
        """Test getting demo code including setup."""
        demo = Demo(
            id="test_demo",
            title="Test Demo",
            description="Test",
            category="test",
            code="print('main')",
            execute=lambda: "output",
            setup_code="# Setup\nprint('setup')",
        )

        category = DemoCategory(id="test", title="Test", demos=[demo])
        DemoRegistry.register_category(category)

        code = DemoRegistry.get_demo_code("test_demo")
        assert "# Setup" in code
        assert "print('setup')" in code
        assert "print('main')" in code

    def test_get_demo_code_without_setup(self, reset_demo_registry) -> None:
        """Test getting demo code without setup."""
        demo = Demo(
            id="test_demo",
            title="Test Demo",
            description="Test",
            category="test",
            code="print('main')",
            execute=lambda: "output",
        )

        category = DemoCategory(id="test", title="Test", demos=[demo])
        DemoRegistry.register_category(category)

        code = DemoRegistry.get_demo_code("test_demo")
        assert code == "print('main')"

    def test_get_demo_code_not_found(self, reset_demo_registry) -> None:
        """Test getting code for non-existent demo."""
        code = DemoRegistry.get_demo_code("nonexistent")
        assert code == ""

    def test_reset_registry(self, reset_demo_registry) -> None:
        """Test resetting the registry."""
        category = DemoCategory(id="test", title="Test")
        DemoRegistry.register_category(category)

        assert len(DemoRegistry.get_categories()) == 1

        DemoRegistry.reset()

        assert len(DemoRegistry.get_categories()) == 0
        assert DemoRegistry.get_demo("test") is None

    def test_demo_id_uniqueness(self, reset_demo_registry) -> None:
        """Test that demo IDs must be unique."""
        demo1 = Demo(
            id="duplicate",
            title="Demo 1",
            description="First",
            category="cat1",
            code="code1",
            execute=lambda: "out1",
        )
        demo2 = Demo(
            id="duplicate",
            title="Demo 2",
            description="Second",
            category="cat2",
            code="code2",
            execute=lambda: "out2",
        )

        cat1 = DemoCategory(id="cat1", title="Cat 1", demos=[demo1])
        cat2 = DemoCategory(id="cat2", title="Cat 2", demos=[demo2])

        DemoRegistry.register_category(cat1)
        DemoRegistry.register_category(cat2)

        # The second demo with the same ID should overwrite the first
        retrieved = DemoRegistry.get_demo("duplicate")
        assert retrieved is not None
        assert retrieved.title == "Demo 2"

    def test_get_categories_returns_sequence(self, reset_demo_registry) -> None:
        """Test that get_categories returns a sequence."""
        category = DemoCategory(id="test", title="Test")
        DemoRegistry.register_category(category)

        categories = DemoRegistry.get_categories()
        # Should support indexing
        assert categories[0] == category
        # Should support len()
        assert len(categories) == 1

    def test_category_with_multiple_demos(self, reset_demo_registry) -> None:
        """Test a category with multiple demos."""

        def make_demo(idx: int) -> Demo:
            """Factory to create a demo with proper closure binding."""
            return Demo(
                id=f"demo{idx}",
                title=f"Demo {idx}",
                description=f"Demo {idx}",
                category="test",
                code=f"code{idx}",
                execute=lambda: f"output{idx}",
            )

        demos = [make_demo(i) for i in range(5)]

        category = DemoCategory(id="test", title="Test", demos=demos)
        DemoRegistry.register_category(category)

        for i in range(len(demos)):
            retrieved = DemoRegistry.get_demo(f"demo{i}")
            assert retrieved is not None
            assert retrieved.id == f"demo{i}"

    def test_demo_code_formatting(self, reset_demo_registry) -> None:
        """Test that demo code is formatted correctly."""
        demo = Demo(
            id="test",
            title="Test",
            description="Test",
            category="test",
            code="main_code()",
            execute=lambda: "",
            setup_code="setup_code()",
        )

        category = DemoCategory(id="test", title="Test", demos=[demo])
        DemoRegistry.register_category(category)

        code = DemoRegistry.get_demo_code("test")
        lines = code.split("\n")

        # Should have setup comment, setup code, then main code
        assert "# Setup" in lines[0]
        assert "setup_code()" in lines[1]
        assert lines[2] == ""  # Blank line
        assert "main_code()" in lines[3]
