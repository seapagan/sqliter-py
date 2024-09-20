"""Tests for selecting specific fields from a model."""

from typing import Union, cast

import pytest

from sqliter import SqliterDB
from sqliter.model.model import BaseDBModel
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

    def test_select_single_field(self, db_mock_detailed: SqliterDB) -> None:
        """Test selecting just a single field from a model."""
        results = db_mock_detailed.select(
            DetailedPersonModel, fields=["name"]
        ).fetch_all()
        assert len(results) == 3
        for result in results:
            assert hasattr(result, "name")
            assert not hasattr(result, "age")
            assert not hasattr(result, "email")
            assert not hasattr(result, "address")
            assert not hasattr(result, "phone")
            assert not hasattr(result, "occupation")

    def test_select_fields_with_filter(
        self, db_mock_detailed: SqliterDB
    ) -> None:
        """Test selecting specific fields with a filter."""
        results = (
            db_mock_detailed.select(DetailedPersonModel, fields=["name", "age"])
            .filter(age__gt=25)
            .fetch_all()
        )
        assert len(results) == 2
        for result in results:
            assert hasattr(result, "name")
            assert hasattr(result, "age")
            assert result.age > 25
            assert not hasattr(result, "email")

    def test_select_all_fields_explicitly(
        self, db_mock_detailed: SqliterDB
    ) -> None:
        """Test selecting all fields explicitly."""
        all_fields = ["name", "age", "email", "address", "phone", "occupation"]
        results = db_mock_detailed.select(
            DetailedPersonModel, fields=all_fields
        ).fetch_all()
        assert len(results) == 3
        for result in results:
            for field in all_fields:
                assert hasattr(result, field)

    def test_select_no_fields(self, db_mock_detailed: SqliterDB) -> None:
        """Test that passing an empty fields arg returns all fields."""
        results = db_mock_detailed.select(
            DetailedPersonModel, fields=[]
        ).fetch_all()
        assert len(results) == 3
        for result in results:
            assert isinstance(result, DetailedPersonModel)
            assert all(
                hasattr(result, field)
                for field in DetailedPersonModel.__annotations__
            )

    def test_select_fields_with_ordering(
        self, db_mock_detailed: SqliterDB
    ) -> None:
        """Test selecting specific fields with ordering."""
        results = (
            db_mock_detailed.select(DetailedPersonModel, fields=["name", "age"])
            .order("age", direction="DESC")
            .fetch_all()
        )
        assert len(results) == 3
        assert results[0].age > results[1].age > results[2].age
        for result in results:
            assert hasattr(result, "name")
            assert hasattr(result, "age")
            assert not hasattr(result, "email")

    def test_select_fields_with_limit_offset(
        self, db_mock_detailed: SqliterDB
    ) -> None:
        """Test selecting specific fields with a limit and offset."""
        results = (
            db_mock_detailed.select(
                DetailedPersonModel, fields=["name", "email"]
            )
            .limit(2)
            .offset(1)
            .fetch_all()
        )
        assert len(results) == 2
        for result in results:
            assert hasattr(result, "name")
            assert hasattr(result, "email")
            assert not hasattr(result, "age")

    def test_select_nonexistent_fields(
        self, db_mock_detailed: SqliterDB
    ) -> None:
        """Test selecting a nonexistent fields raises an error."""
        with pytest.raises(
            ValueError, match="Invalid fields specified: nonexistent_field"
        ):
            db_mock_detailed.select(
                DetailedPersonModel, fields=["name", "nonexistent_field"]
            ).fetch_all()

    def test_original_model_unaffected(
        self, db_mock_detailed: SqliterDB
    ) -> None:
        """Ensure the original model is unaffected by field selection."""
        db_mock_detailed.select(
            DetailedPersonModel, fields=["name", "age"]
        ).fetch_all()
        full_results = db_mock_detailed.select(DetailedPersonModel).fetch_all()
        assert len(full_results) == 3
        for result in full_results:
            assert all(
                hasattr(result, field)
                for field in DetailedPersonModel.__annotations__
            )

    def test_field_types_maintained(self, db_mock_detailed: SqliterDB) -> None:
        """Ensure that the field types are maintained when selecting fields."""
        results = db_mock_detailed.select(
            DetailedPersonModel, fields=["name", "age"]
        ).fetch_all()
        assert len(results) > 0
        for result in results:
            assert isinstance(result.name, str)
            assert isinstance(result.age, int)

    def test_model_validate_partial_else_block(self) -> None:
        """Test where the for/else block is hit in model_validate_partial."""

        class TestModel(BaseDBModel):
            field_a: Union[int, float]

        invalid_value = "string"

        obj = {"field_a": invalid_value}

        result = TestModel.model_validate_partial(obj)

        assert cast(str, result.field_a) == invalid_value
