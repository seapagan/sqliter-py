"""Unit tests for results demo functions."""

from __future__ import annotations

from sqliter.tui.demos import results


class TestGetCategory:
    """Test the results category."""

    def test_get_category_returns_valid_category(self) -> None:
        """Test that get_category returns a valid DemoCategory."""
        category = results.get_category()

        assert category.id == "results"
        assert "Results" in category.title
        assert len(category.demos) == 6

    def test_all_demos_are_executable(self) -> None:
        """Test that all result demos execute successfully."""
        category = results.get_category()

        for demo in category.demos:
            output = demo.execute()
            assert isinstance(output, str)
            assert len(output) > 0
