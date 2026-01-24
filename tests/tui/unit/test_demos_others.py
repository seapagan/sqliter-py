"""Unit tests for remaining demo functions."""

from __future__ import annotations

from sqliter.tui.demos import (
    caching,
    errors,
    ordering,
    orm,
    timestamps,
    transactions,
)


class TestGetCategories:
    """Test remaining demo categories."""

    def test_caching_category_valid(self) -> None:
        """Test that caching category is valid."""
        category = caching.get_category()
        assert category.id == "caching"
        assert len(category.demos) > 0

    def test_all_caching_demos_execute(self) -> None:
        """Test that all caching demos execute."""
        category = caching.get_category()
        for demo in category.demos:
            output = demo.execute()
            assert isinstance(output, str)

    def test_errors_category_valid(self) -> None:
        """Test that errors category is valid."""
        category = errors.get_category()
        assert category.id == "errors"
        assert len(category.demos) > 0

    def test_all_errors_demos_execute(self) -> None:
        """Test that all error demos execute."""
        category = errors.get_category()
        for demo in category.demos:
            output = demo.execute()
            assert isinstance(output, str)

    def test_orm_category_valid(self) -> None:
        """Test that ORM category is valid."""
        category = orm.get_category()
        assert category.id == "orm"
        assert len(category.demos) > 0

    def test_all_orm_demos_execute(self) -> None:
        """Test that all ORM demos execute."""
        category = orm.get_category()
        for demo in category.demos:
            output = demo.execute()
            assert isinstance(output, str)

    def test_ordering_category_valid(self) -> None:
        """Test that ordering category is valid."""
        category = ordering.get_category()
        assert category.id == "ordering"
        assert len(category.demos) > 0

    def test_all_ordering_demos_execute(self) -> None:
        """Test that all ordering demos execute."""
        category = ordering.get_category()
        for demo in category.demos:
            output = demo.execute()
            assert isinstance(output, str)

    def test_timestamps_category_valid(self) -> None:
        """Test that timestamps category is valid."""
        category = timestamps.get_category()
        assert category.id == "timestamps"
        assert len(category.demos) > 0

    def test_all_timestamps_demos_execute(self) -> None:
        """Test that all timestamp demos execute."""
        category = timestamps.get_category()
        for demo in category.demos:
            output = demo.execute()
            assert isinstance(output, str)

    def test_transactions_category_valid(self) -> None:
        """Test that transactions category is valid."""
        category = transactions.get_category()
        assert category.id == "transactions"
        assert len(category.demos) > 0

    def test_all_transactions_demos_execute(self) -> None:
        """Test that all transaction demos execute."""
        category = transactions.get_category()
        for demo in category.demos:
            output = demo.execute()
            assert isinstance(output, str)
