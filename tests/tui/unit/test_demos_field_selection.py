"""Unit tests for field selection demo functions."""

from __future__ import annotations

from sqliter.tui.demos import field_selection


class TestGetCategory:
    """Test the field_selection category."""

    def test_get_category_returns_valid_category(self) -> None:
        """Test that get_category returns a valid DemoCategory."""
        category = field_selection.get_category()

        assert category.id == "field_selection"
        assert "Field" in category.title
        assert "Selection" in category.title
        assert len(category.demos) >= 3

    def test_all_demos_are_executable(self) -> None:
        """Test that all field selection demos execute successfully."""
        category = field_selection.get_category()

        for demo in category.demos:
            output = demo.execute()
            assert isinstance(output, str)
            assert len(output) > 0
