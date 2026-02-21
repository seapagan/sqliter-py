"""Unit tests for remaining demo functions."""

from __future__ import annotations

import pytest

from sqliter.orm import ManyToMany
from sqliter.tui.demos import (
    caching,
    errors,
    ordering,
    orm,
    timestamps,
    transactions,
)

CATEGORY_MODULES = (
    (caching, "caching"),
    (errors, "errors"),
    (orm, "orm"),
    (ordering, "ordering"),
    (timestamps, "timestamps"),
    (transactions, "transactions"),
)


class TestGetCategories:
    """Test remaining demo categories."""

    @pytest.mark.parametrize(
        ("module", "expected_id"),
        CATEGORY_MODULES,
    )
    def test_category_valid(self, module, expected_id) -> None:
        """Test that category is valid."""
        category = module.get_category()
        assert category.id == expected_id
        assert len(category.demos) > 0

    @pytest.mark.parametrize(
        ("module", "expected_id"),
        CATEGORY_MODULES,
    )
    def test_all_demos_execute(self, module, expected_id) -> None:
        """Test that all demos execute."""
        category = module.get_category()
        for demo in category.demos:
            output = demo.execute()
            assert isinstance(output, str)
            assert len(output) > 0

    def test_orm_metadata_demo_errors_when_descriptor_metadata_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """M2M metadata demo raises if descriptor metadata is unavailable."""
        monkeypatch.setattr(
            ManyToMany,
            "sql_metadata",
            property(lambda self: None),
        )
        with pytest.raises(RuntimeError, match="metadata unavailable"):
            orm._run_many_to_many_sql_metadata()
