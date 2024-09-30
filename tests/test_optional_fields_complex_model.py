"""Test cases to ensure model type conversion works correctly."""

import pytest

from sqliter import SqliterDB
from tests.conftest import ComplexModel


@pytest.fixture
def db_mock_complex(db_mock: SqliterDB) -> SqliterDB:
    """Fixture for a mock database with a complex model."""
    db_mock.create_table(ComplexModel)
    db_mock.insert(
        ComplexModel(
            pk=1,
            name="Alice",
            age=30.5,
            is_active=True,
            score=85,
            nullable_field="Not null",
        )
    )
    db_mock.insert(
        ComplexModel(
            pk=2,
            name="Bob",
            age=25.0,
            is_active=False,
            score=90.5,
            nullable_field=None,
        )
    )
    return db_mock


class TestComplexModelPartialSelection:
    """Define test cases for selecting specific fields from a complex model."""

    def test_select_all_fields(self, db_mock_complex: SqliterDB) -> None:
        """Select all fields and ensure their types are correct."""
        results = db_mock_complex.select(ComplexModel).fetch_all()
        assert len(results) == 2
        for result in results:
            assert isinstance(result.pk, int)
            assert isinstance(result.name, str)
            assert isinstance(result.age, float)
            assert isinstance(result.is_active, bool)
            assert isinstance(result.score, (int, float))

            assert result.nullable_field is None or isinstance(
                result.nullable_field, str
            )

    def test_select_subset_of_fields(self, db_mock_complex: SqliterDB) -> None:
        """Select a subset of fields and ensure their types are correct."""
        fields = ["pk", "name", "age", "is_active", "score"]
        results = db_mock_complex.select(
            ComplexModel, fields=fields
        ).fetch_all()
        assert len(results) == 2
        for result in results:
            assert isinstance(result.pk, int)
            assert isinstance(result.name, str)
            assert isinstance(result.age, float)
            assert isinstance(result.is_active, bool)
            assert isinstance(result.score, (int, float))
            assert not hasattr(result, "birthday")
            assert not hasattr(result, "nullable_field")

    def test_select_with_type_conversion(
        self, db_mock_complex: SqliterDB
    ) -> None:
        """Select a subset of fields and ensure their types are correct."""
        fields = ["pk", "age", "is_active", "score"]
        results = db_mock_complex.select(
            ComplexModel, fields=fields
        ).fetch_all()
        assert len(results) == 2
        for result in results:
            assert isinstance(result.pk, int)
            assert isinstance(result.age, float)
            assert isinstance(result.is_active, bool)
            assert isinstance(result.score, (int, float))

    def test_select_with_nullable_field(
        self, db_mock_complex: SqliterDB
    ) -> None:
        """Select fields with a nullable field."""
        fields = ["nullable_field"]
        results = db_mock_complex.select(
            ComplexModel, fields=fields
        ).fetch_all()

        assert len(results) == 2
        assert any(result.nullable_field is None for result in results)
        assert any(isinstance(result.nullable_field, str) for result in results)

    def test_select_with_union_field(self, db_mock_complex: SqliterDB) -> None:
        """Select fields with a Union type."""
        fields = ["score"]
        results = db_mock_complex.select(
            ComplexModel, fields=fields
        ).fetch_all()
        assert len(results) == 2
        assert any(isinstance(result.score, int) for result in results)
        assert any(isinstance(result.score, float) for result in results)

    def test_select_with_filtering(self, db_mock_complex: SqliterDB) -> None:
        """Select fields with a filter."""
        fields = ["pk", "name", "age"]
        results = (
            db_mock_complex.select(ComplexModel, fields=fields)
            .filter(age__gt=28)
            .fetch_all()
        )
        assert len(results) == 1
        assert results[0].name == "Alice"
        assert results[0].age > 28

    def test_select_with_ordering(self, db_mock_complex: SqliterDB) -> None:
        """Select fields with ordering."""
        fields = ["pk", "name", "age"]
        results = (
            db_mock_complex.select(ComplexModel, fields=fields)
            .order("age", direction="DESC")
            .fetch_all()
        )
        assert len(results) == 2
        assert results[0].name == "Alice"
        assert results[1].name == "Bob"

    def test_select_nonexistent_field(self, db_mock_complex: SqliterDB) -> None:
        """Select a nonexistent field and ensure an error is raised."""
        with pytest.raises(
            ValueError, match="Invalid fields specified: nonexistent_field"
        ):
            db_mock_complex.select(
                ComplexModel, fields=["nonexistent_field"]
            ).fetch_all()
