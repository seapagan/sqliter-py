"""Unit tests for models demo functions."""

from __future__ import annotations

from sqliter.tui.demos import models


class TestGetCategory:
    """Test the models category."""

    def test_get_category_returns_valid_category(self) -> None:
        """Test that get_category returns a valid DemoCategory."""
        category = models.get_category()

        assert category.id == "models"
        assert "Models" in category.title
        assert len(category.demos) == 6

    def test_all_demos_are_executable(self) -> None:
        """Test that all model demos execute successfully."""
        category = models.get_category()

        for demo in category.demos:
            output = demo.execute()
            assert isinstance(output, str)
            assert len(output) > 0
