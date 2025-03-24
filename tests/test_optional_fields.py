"""Tests for selecting specific fields from a model."""

from typing import Union, cast

import pytest

from sqliter import SqliterDB
from sqliter.model.model import BaseDBModel
from tests.conftest import DetailedPersonModel, PersonModel


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

        assert cast("str", result.field_a) == invalid_value

    def test_fields_operator_all_fields_explicitly(
        self, db_mock_detailed: SqliterDB
    ) -> None:
        """Test selecting all fields explicitly."""
        all_fields = ["name", "age", "email", "address", "phone", "occupation"]
        results = (
            db_mock_detailed.select(DetailedPersonModel)
            .fields(all_fields)
            .fetch_all()
        )
        assert len(results) == 3
        for result in results:
            for field in all_fields:
                assert hasattr(result, field)

    def test_fields_operator_no_fields_explicitly(
        self, db_mock_detailed: SqliterDB
    ) -> None:
        """Test selecting all fields explicitly."""
        all_fields = ["name", "age", "email", "address", "phone", "occupation"]

        results = (
            db_mock_detailed.select(DetailedPersonModel).fields().fetch_all()
        )
        assert len(results) == 3
        for result in results:
            for field in all_fields:
                assert hasattr(result, field)

    def test_validate_fields_with_none(self, db_mock_adv) -> None:
        """Test _validate_fields with self._fields set to None."""
        # This test will indirectly invoke _validate_fields by creating a
        # QueryBuilder without specifying fields (i.e., self._fields will be
        # None).
        query = db_mock_adv.select(PersonModel, fields=None)

        # The _validate_fields method should pass without raising any errors
        # since self._fields is None.
        assert query._fields is None

    def test_direct_validate_fields_with_none(self, db_mock_adv) -> None:
        """Test _validate_fields directly with self._fields set to None."""
        # Create the query builder instance
        query = db_mock_adv.select(PersonModel, fields=None)

        # Directly call  _validate_fields to hit the specific code path
        query._validate_fields()

        # No assertion needed since we're testing for the absence of exceptions

    def test_fetch_one_with_specific_fields(
        self, db_mock_detailed: SqliterDB
    ) -> None:
        """Test fetch_one selecting specific fields."""
        result = db_mock_detailed.select(
            DetailedPersonModel, fields=["name", "email"]
        ).fetch_one()

        assert result is not None
        assert hasattr(result, "name")
        assert hasattr(result, "email")
        assert not hasattr(result, "age")
        assert not hasattr(result, "address")
        assert not hasattr(result, "phone")
        assert not hasattr(result, "occupation")

    def test_fetch_first_with_specific_fields(
        self, db_mock_detailed: SqliterDB
    ) -> None:
        """Test fetch_first selecting specific fields."""
        result = db_mock_detailed.select(
            DetailedPersonModel, fields=["name", "age"]
        ).fetch_first()

        assert result is not None
        assert hasattr(result, "name")
        assert hasattr(result, "age")
        assert not hasattr(result, "email")
        assert not hasattr(result, "address")
        assert not hasattr(result, "phone")
        assert not hasattr(result, "occupation")

    def test_fetch_last_with_specific_fields(
        self,
        db_mock_detailed: SqliterDB,
    ) -> None:
        """Test fetch_last selecting specific fields."""
        result = db_mock_detailed.select(
            DetailedPersonModel, fields=["name", "occupation"]
        ).fetch_last()

        assert result is not None
        assert hasattr(result, "name")
        assert hasattr(result, "occupation")
        assert not hasattr(result, "age")
        assert not hasattr(result, "email")
        assert not hasattr(result, "address")
        assert not hasattr(result, "phone")

    def test_fields_overrides_select(self, db_mock_adv: SqliterDB) -> None:
        """Ensure that the fields() method overrides select() method fields."""
        # Call select() first with certain fields, then override using fields()
        result = (
            db_mock_adv.select(PersonModel, fields=["name"])
            .fields(["age"])
            .fetch_all()
        )

        # Ensure only 'age' is present, as 'fields()' was called last
        assert all(hasattr(person, "age") for person in result)
        assert all(not hasattr(person, "name") for person in result)

    def test_fields_overrides_select_with_overlap(
        self,
        db_mock_detailed: SqliterDB,
    ) -> None:
        """Ensure fields() method overrides overlapping fields from select()."""
        # Call select() with certain fields, then override using fields() with
        # overlap
        result = (
            db_mock_detailed.select(
                DetailedPersonModel, fields=["name", "email"]
            )
            .fields(["age", "email"])
            .fetch_all()
        )

        # Ensure only 'age' and 'email' are present, as 'fields()' was called
        # last
        assert all(hasattr(person, "age") for person in result)
        assert all(hasattr(person, "email") for person in result)
        assert all(not hasattr(person, "name") for person in result)
        assert all(not hasattr(person, "address") for person in result)
        assert all(not hasattr(person, "phone") for person in result)
        assert all(not hasattr(person, "occupation") for person in result)

    def test_exclude_single_field(self, db_mock_detailed: SqliterDB) -> None:
        """Test excluding a single field."""
        results = (
            db_mock_detailed.select(DetailedPersonModel)
            .exclude(fields=["email"])
            .fetch_all()
        )
        assert len(results) == 3
        for result in results:
            assert hasattr(result, "name")
            assert hasattr(result, "age")
            assert not hasattr(result, "email")

    def test_exclude_multiple_fields(self, db_mock_detailed: SqliterDB) -> None:
        """Test excluding multiple fields."""
        results = (
            db_mock_detailed.select(DetailedPersonModel)
            .exclude(fields=["email", "phone", "occupation"])
            .fetch_all()
        )
        assert len(results) == 3
        for result in results:
            assert hasattr(result, "name")
            assert hasattr(result, "age")
            assert not hasattr(result, "email")
            assert not hasattr(result, "phone")
            assert not hasattr(result, "occupation")

    def test_exclude_all_fields_error(
        self, db_mock_detailed: SqliterDB
    ) -> None:
        """Test excluding all fields raises an error."""
        with pytest.raises(
            ValueError, match="Exclusion results in no fields being selected."
        ):
            db_mock_detailed.select(DetailedPersonModel).exclude(
                fields=[
                    "name",
                    "age",
                    "email",
                    "address",
                    "phone",
                    "occupation",
                    "created_at",
                    "updated_at",
                ]
            ).fetch_all()

    def test_exclude_invalid_field(self, db_mock_detailed: SqliterDB) -> None:
        """Test excluding an invalid field raises an error."""
        with pytest.raises(
            ValueError,
            match="Invalid fields specified for exclusion: invalid_field",
        ):
            db_mock_detailed.select(DetailedPersonModel).exclude(
                fields=["invalid_field"]
            ).fetch_all()

    def test_exclude_with_filter(self, db_mock_detailed: SqliterDB) -> None:
        """Test excluding fields while filtering."""
        results = (
            db_mock_detailed.select(DetailedPersonModel)
            .filter(age__gte=30)
            .exclude(fields=["phone"])
            .fetch_all()
        )
        assert len(results) == 2
        for result in results:
            assert hasattr(result, "name")
            assert hasattr(result, "email")
            assert not hasattr(result, "phone")

    def test_exclude_with_no_fields(self, db_mock_detailed: SqliterDB) -> None:
        """Test calling exclude with no fields has no effect."""
        results = (
            db_mock_detailed.select(DetailedPersonModel)
            .exclude(fields=[])
            .fetch_all()
        )
        assert len(results) == 3
        for result in results:
            assert hasattr(result, "name")
            assert hasattr(result, "age")
            assert hasattr(result, "email")
            assert hasattr(result, "phone")
            assert hasattr(result, "occupation")

    def test_only_method_with_single_field(
        self, db_mock_detailed: SqliterDB
    ) -> None:
        """Test selecting with only one specific field."""
        results = (
            db_mock_detailed.select(DetailedPersonModel)
            .only("name")
            .fetch_all()
        )
        assert len(results) == 3
        for result in results:
            assert hasattr(result, "name")
            assert not hasattr(result, "age")
            assert not hasattr(result, "email")

    def test_only_with_list_raises_type_error(
        self,
        db_mock_detailed: SqliterDB,
    ) -> None:
        """Test that only() raises TypeError with list or multiple fields.

        This is the default behavior for Python anyway, but we want to ensure
        that the method enforces this.
        """
        with pytest.raises(TypeError):
            db_mock_detailed.select(DetailedPersonModel).only(
                ["name", "email"]  # type: ignore
            ).fetch_all()  # Passing a list

        with pytest.raises(TypeError):
            db_mock_detailed.select(DetailedPersonModel).only(
                "name",
                "email",  # type: ignore
            ).fetch_all()  # Passing multiple fields

    def test_only_with_invalid_field(self, db_mock_detailed: SqliterDB) -> None:
        """Test that only() raises ValueError with invalid field."""
        with pytest.raises(
            ValueError,
            match="Invalid field specified: invalid_field",
        ):
            db_mock_detailed.select(DetailedPersonModel).only(
                "invalid_field"
            ).fetch_all()
