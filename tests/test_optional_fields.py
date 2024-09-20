"""Tests for selecting specific fields from a model."""

import pytest

from sqliter import SqliterDB
from tests.conftest import DetailedPersonModel


class TestOptionalFields:
    """Test cases for selecting specific fields from a model."""

    def test_select_specific_fields(self, db_mock_detailed: SqliterDB) -> None:
        """Test selecting specific fields from a model."""
        results = db_mock_detailed.select(
            DetailedPersonModel, fields=["name", "age"]
        ).fetch_all()
        assert len(results) == 3
        for result in results:
            assert hasattr(result, "name")
            assert hasattr(result, "age")
            assert not hasattr(result, "email")
            assert not hasattr(result, "address")
            assert not hasattr(result, "phone")
            assert not hasattr(result, "occupation")

    def test_select_multiple_fields(self, db_mock_detailed: SqliterDB) -> None:
        """Test selecting multiple specific fields from a model."""
        results = db_mock_detailed.select(
            DetailedPersonModel, fields=["name", "email", "occupation"]
        ).fetch_all()
        assert len(results) == 3
        for result in results:
            assert hasattr(result, "name")
            assert hasattr(result, "email")
            assert hasattr(result, "occupation")
            assert not hasattr(result, "age")
            assert not hasattr(result, "address")
            assert not hasattr(result, "phone")

    def test_select_all_fields(self, db_mock_detailed: SqliterDB) -> None:
        """Test that selecting no specific fields returns all fields."""
        results = db_mock_detailed.select(DetailedPersonModel).fetch_all()
        assert len(results) == 3
        for result in results:
            assert hasattr(result, "name")
            assert hasattr(result, "age")
            assert hasattr(result, "email")
            assert hasattr(result, "address")
            assert hasattr(result, "phone")
            assert hasattr(result, "occupation")

    def test_select_with_filter(self, db_mock_detailed: SqliterDB) -> None:
        """Test selecting specific fields with a filter applied."""
        results = (
            db_mock_detailed.select(
                DetailedPersonModel, fields=["name", "occupation"]
            )
            .filter(age=30)
            .fetch_all()
        )
        assert len(results) == 1
        assert results[0].name == "Bob"
        assert results[0].occupation == "Designer"
        assert not hasattr(results[0], "age")
        assert not hasattr(results[0], "email")
        assert not hasattr(results[0], "address")
        assert not hasattr(results[0], "phone")

    def test_select_nonexistent_field(
        self, db_mock_detailed: SqliterDB
    ) -> None:
        """Test that selecting a nonexistent field raises an error."""
        with pytest.raises(ValueError):  # noqa: PT011
            db_mock_detailed.select(
                DetailedPersonModel, fields=["nonexistent"]
            ).fetch_all()

    def test_select_partial_fields_model_integrity(
        self,
        db_mock_detailed: SqliterDB,
    ) -> None:
        """Ensure partial field selection doesn't affect the original model."""
        db_mock_detailed.select(
            DetailedPersonModel, fields=["name", "age"]
        ).fetch_all()
        full_results = db_mock_detailed.select(DetailedPersonModel).fetch_all()
        assert len(full_results) == 3
        for result in full_results:
            assert hasattr(result, "name")
            assert hasattr(result, "age")
            assert hasattr(result, "email")
            assert hasattr(result, "address")
            assert hasattr(result, "phone")
            assert hasattr(result, "occupation")
