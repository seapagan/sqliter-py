"""Test cases to ensure model type conversion works correctly."""

from datetime import date, datetime

import pytest

from sqliter import SqliterDB
from tests.conftest import ComplexModel


@pytest.fixture
def db_mock_complex(db_mock: SqliterDB) -> SqliterDB:
    """Ficture for a mock database with a complex model."""
    db_mock.create_table(ComplexModel)
    db_mock.insert(
        ComplexModel(
            id=1,
            name="Alice",
            age=30.5,
            is_active=True,
            tags=["tag1", "tag2"],
            created_at=datetime(2023, 1, 1, 12, 0),  # noqa: DTZ001
            updated_at=None,
            score=85,
            birthday=date(1993, 5, 15),
            nullable_field="Not null",
        )
    )
    db_mock.insert(
        ComplexModel(
            id=2,
            name="Bob",
            age=25.0,
            is_active=False,
            tags=["tag3"],
            created_at=datetime(2023, 2, 1, 12, 0),  # noqa: DTZ001
            updated_at=datetime(2023, 3, 1, 12, 0),  # noqa: DTZ001
            score=90.5,
            birthday=date(1998, 8, 20),
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
            assert isinstance(result.id, int)
            assert isinstance(result.name, str)
            assert isinstance(result.age, float)
            assert isinstance(result.is_active, bool)
            assert isinstance(result.tags, list)
            assert all(isinstance(tag, str) for tag in result.tags)
            assert isinstance(result.created_at, datetime)
            assert isinstance(result.score, (int, float))
            assert isinstance(result.birthday, date)
            assert result.updated_at is None or isinstance(
                result.updated_at, datetime
            )
            assert result.nullable_field is None or isinstance(
                result.nullable_field, str
            )

    def test_select_subset_of_fields(self, db_mock_complex: SqliterDB) -> None:
        """Select a subset of fields and ensure their types are correct."""
        fields = ["id", "name", "age", "is_active", "score"]
        results = db_mock_complex.select(
            ComplexModel, fields=fields
        ).fetch_all()
        assert len(results) == 2
        for result in results:
            assert isinstance(result.id, int)
            assert isinstance(result.name, str)
            assert isinstance(result.age, float)
            assert isinstance(result.is_active, bool)
            assert isinstance(result.score, (int, float))
            assert not hasattr(result, "tags")
            assert not hasattr(result, "created_at")
            assert not hasattr(result, "updated_at")
            assert not hasattr(result, "birthday")
            assert not hasattr(result, "nullable_field")

    def test_select_with_type_conversion(
        self, db_mock_complex: SqliterDB
    ) -> None:
        """Select a subset of fields and ensure their types are correct."""
        fields = ["id", "age", "is_active", "score"]
        results = db_mock_complex.select(
            ComplexModel, fields=fields
        ).fetch_all()
        assert len(results) == 2
        for result in results:
            assert isinstance(result.id, int)
            assert isinstance(result.age, float)
            assert isinstance(result.is_active, bool)
            assert isinstance(result.score, (int, float))

    def test_select_with_datetime_and_date(
        self, db_mock_complex: SqliterDB
    ) -> None:
        """Select fields with datetime and date types."""
        fields = ["created_at", "updated_at", "birthday"]
        results = db_mock_complex.select(
            ComplexModel, fields=fields
        ).fetch_all()
        assert len(results) == 2
        for result in results:
            assert isinstance(result.created_at, datetime)
            assert result.updated_at is None or isinstance(
                result.updated_at, datetime
            )
            assert isinstance(result.birthday, date)

    def test_select_with_list_field(self, db_mock_complex: SqliterDB) -> None:
        """Select fields with a list type."""
        fields = ["tags"]
        results = db_mock_complex.select(
            ComplexModel, fields=fields
        ).fetch_all()
        assert len(results) == 2
        for result in results:
            assert isinstance(result.tags, list)
            assert all(isinstance(tag, str) for tag in result.tags)

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
        fields = ["id", "name", "age"]
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
        fields = ["id", "name", "age"]
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
