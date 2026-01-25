"""Unit tests for constraints demo functions."""

from __future__ import annotations

from sqliter.tui.demos import constraints


class TestGetCategory:
    """Test the constraints category."""

    def test_get_category_returns_valid_category(self) -> None:
        """Test that get_category returns a valid DemoCategory."""
        category = constraints.get_category()

        assert category.id == "constraints"
        assert category.title == "Constraints"
        assert len(category.demos) == 5

    def test_all_demos_are_executable(self) -> None:
        """Test that all constraint demos execute successfully."""
        category = constraints.get_category()

        for demo in category.demos:
            output = demo.execute()
            assert isinstance(output, str)
            assert len(output) > 0
