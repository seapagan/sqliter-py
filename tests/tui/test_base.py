"""Tests for demo base classes."""

from __future__ import annotations

import pytest

from sqliter.tui.demos.base import Demo, DemoCategory


class TestDemo:
    """Test the Demo dataclass."""

    def test_demo_creation(self) -> None:
        """Test creating a Demo instance."""
        demo = Demo(
            id="test_demo",
            title="Test Demo",
            description="A test demo",
            category="test",
            code="print('hello')",
            execute=lambda: "hello",
        )

        assert demo.id == "test_demo"
        assert demo.title == "Test Demo"
        assert demo.description == "A test demo"
        assert demo.category == "test"
        assert demo.code == "print('hello')"
        assert demo.execute() == "hello"
        assert demo.setup_code is None
        assert demo.teardown is None

    def test_demo_with_setup_code(self) -> None:
        """Test creating a Demo with setup code."""
        demo = Demo(
            id="test_demo",
            title="Test Demo",
            description="A test demo",
            category="test",
            code="print('main')",
            execute=lambda: "main",
            setup_code="# Setup code\nprint('setup')",
        )

        assert demo.setup_code == "# Setup code\nprint('setup')"

    def test_demo_with_teardown(self) -> None:
        """Test creating a Demo with teardown function."""
        teardown_called = []

        def teardown() -> None:
            teardown_called.append(True)

        demo = Demo(
            id="test_demo",
            title="Test Demo",
            description="A test demo",
            category="test",
            code="print('main')",
            execute=lambda: "main",
            teardown=teardown,
        )

        assert demo.teardown is not None
        demo.teardown()
        assert teardown_called == [True]

    def test_demo_field_validation(self) -> None:
        """Test that required fields are validated."""
        with pytest.raises(TypeError):
            # Missing required fields
            Demo(  # type: ignore[call-arg]
                id="test",
            )

    def test_demo_execute_callable(self) -> None:
        """Test that execute callable is stored correctly."""

        def demo_func() -> str:
            return "demo output"

        demo = Demo(
            id="test_demo",
            title="Test Demo",
            description="A test demo",
            category="test",
            code="code",
            execute=demo_func,
        )

        assert demo.execute == demo_func
        assert demo.execute() == "demo output"


class TestDemoCategory:
    """Test the DemoCategory dataclass."""

    def test_category_creation(self) -> None:
        """Test creating a DemoCategory instance."""
        category = DemoCategory(
            id="test_category",
            title="Test Category",
            icon="🧪",
        )

        assert category.id == "test_category"
        assert category.title == "Test Category"
        assert category.icon == "🧪"
        assert category.demos == []
        assert category.expanded is False

    def test_category_with_demos(self) -> None:
        """Test creating a DemoCategory with demos."""
        demo1 = Demo(
            id="demo1",
            title="Demo 1",
            description="First demo",
            category="test",
            code="code1",
            execute=lambda: "output1",
        )
        demo2 = Demo(
            id="demo2",
            title="Demo 2",
            description="Second demo",
            category="test",
            code="code2",
            execute=lambda: "output2",
        )

        category = DemoCategory(
            id="test_category",
            title="Test Category",
            icon="📦",
            demos=[demo1, demo2],
        )

        assert len(category.demos) == 2
        assert category.demos[0] == demo1
        assert category.demos[1] == demo2

    def test_category_expanded_default(self) -> None:
        """Test that expanded defaults to False."""
        category = DemoCategory(
            id="test_category",
            title="Test Category",
        )

        assert category.expanded is False

    def test_category_expanded_true(self) -> None:
        """Test setting expanded to True."""
        category = DemoCategory(
            id="test_category",
            title="Test Category",
            expanded=True,
        )

        assert category.expanded is True

    def test_category_demo_list_factory(self) -> None:
        """Test that demos uses default_factory."""
        category1 = DemoCategory(id="cat1", title="Category 1")
        category2 = DemoCategory(id="cat2", title="Category 2")

        # Each category should have its own list
        category1.demos.append(
            Demo(
                id="demo1",
                title="Demo",
                description="Demo",
                category="cat1",
                code="code",
                execute=lambda: "",
            )
        )

        assert len(category1.demos) == 1
        assert len(category2.demos) == 0

    def test_category_field_validation(self) -> None:
        """Test that required fields are validated."""
        with pytest.raises(TypeError):
            # Missing required fields
            DemoCategory(  # type: ignore[call-arg]
                icon="🧪",
            )


class TestDemoCategoryRelationship:
    """Test the relationship between Demo and DemoCategory."""

    def test_category_contains_demos(self) -> None:
        """Test that demos are properly associated with category."""
        demo = Demo(
            id="demo1",
            title="Demo",
            description="Demo",
            category="test_category",
            code="code",
            execute=lambda: "output",
        )

        category = DemoCategory(
            id="test_category",
            title="Test Category",
            demos=[demo],
        )

        assert demo.category == "test_category"
        assert category.id == "test_category"
        assert category.demos == [demo]

    def test_multiple_categories_unique_ids(self) -> None:
        """Test that demos across categories have unique IDs."""
        demo1 = Demo(
            id="demo1",
            title="Demo 1",
            description="Demo 1",
            category="cat1",
            code="code1",
            execute=lambda: "output1",
        )
        demo2 = Demo(
            id="demo2",
            title="Demo 2",
            description="Demo 2",
            category="cat2",
            code="code2",
            execute=lambda: "output2",
        )

        cat1 = DemoCategory(id="cat1", title="Category 1", demos=[demo1])
        cat2 = DemoCategory(id="cat2", title="Category 2", demos=[demo2])

        assert demo1.id != demo2.id
        assert cat1.id != cat2.id
