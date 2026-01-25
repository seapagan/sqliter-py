"""Unit tests for filters demo functions."""

from __future__ import annotations

from sqliter.tui.demos import filters


class TestGetCategory:
    """Test the filters category."""

    def test_get_category_returns_valid_category(self) -> None:
        """Test that get_category returns a valid DemoCategory."""
        category = filters.get_category()

        assert category.id == "filters"
        assert "Filter" in category.title
        assert len(category.demos) >= 7

    def test_all_demos_are_executable(self) -> None:
        """Test that all filter demos execute successfully."""
        category = filters.get_category()

        for demo in category.demos:
            output = demo.execute()
            assert isinstance(output, str)
            assert len(output) > 0
