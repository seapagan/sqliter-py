"""Unit tests for string filters demo functions."""

from __future__ import annotations

from sqliter.tui.demos import string_filters


class TestGetCategory:
    """Test the string_filters category."""

    def test_get_category_returns_valid_category(self) -> None:
        """Test that get_category returns a valid DemoCategory."""
        category = string_filters.get_category()

        assert category.id == "string_filters"
        assert "String" in category.title
        assert "Filter" in category.title
        assert len(category.demos) >= 5

    def test_all_demos_are_executable(self) -> None:
        """Test that all string filter demos execute successfully."""
        category = string_filters.get_category()

        for demo in category.demos:
            output = demo.execute()
            assert isinstance(output, str)
            assert len(output) > 0
