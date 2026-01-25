"""Tests for the query module."""

from typing import Optional

import pytest

from sqliter.exceptions import (
    InvalidFilterError,
    InvalidOffsetError,
    RecordDeletionError,
    RecordFetchError,
)
from sqliter.model import BaseDBModel
from sqliter.sqliter import SqliterDB
from tests.conftest import ExampleModel, not_raises


class TestQuery:
    """Test cases for the QueryBuilder class."""

    def test_fetch_all_no_results(self, db_mock) -> None:
        """Test that fetch_all returns None when no results are found."""

        # Define a simple model for the test
        class NoResultModel(BaseDBModel):
            name: str

            class Meta:
                table_name: str = "no_result_table"

        # Create the table for the model
        db_mock.create_table(NoResultModel)

        # Perform a query that returns no results
        result = db_mock.select(NoResultModel).fetch_all()

        # Assert that fetch_all returns None when no results are found
        assert result == []

    def test_fetch_one_single_result(self, db_mock) -> None:
        """Test that fetch_one returns a single result as a model instance."""

        # Define a simple model for the test
        class SingleResultModel(BaseDBModel):
            name: str

            class Meta:
                table_name: str = "single_result_table"

        # Create the table for the model
        db_mock.create_table(SingleResultModel)

        # Insert a single record into the table
        db_mock.insert(SingleResultModel(name="John Doe"))

        # Fetch one result
        result = db_mock.select(SingleResultModel).fetch_one()

        # Assert that the result is a model instance with the correct data
        assert result is not None
        assert result.name == "John Doe"

    def test_fetch_one_no_results(self, db_mock) -> None:
        """Test that fetch_one returns None when no results are found."""

        # Define a simple model for the test
        class NoResultModel(BaseDBModel):
            name: str

            class Meta:
                table_name: str = "no_result_table"

        # Create the table for the model
        db_mock.create_table(NoResultModel)

        # Perform a query that returns no results
        result = db_mock.select(NoResultModel).fetch_one()

        # Assert that fetch_one returns None when no results are found
        assert result is None

    def test_fetch_first_single_result(self, db_mock) -> None:
        """Test that fetch_first returns a single result as a model instance."""

        # Define a simple model for the test
        class SingleResultModel(BaseDBModel):
            name: str

            class Meta:
                table_name: str = "single_result_table"

        # Create the table for the model
        db_mock.create_table(SingleResultModel)

        # Insert a single record into the table
        db_mock.insert(SingleResultModel(name="John Doe"))

        # Fetch one result
        result = db_mock.select(SingleResultModel).fetch_first()

        # Assert that the result is a model instance with the correct data
        assert result is not None
        assert result.name == "John Doe"

    def test_fetch_first_no_results(self, db_mock) -> None:
        """Test that fetch_first returns None when no results are found."""

        # Define a simple model for the test
        class NoResultModel(BaseDBModel):
            name: str

            class Meta:
                table_name: str = "no_result_table"

        # Create the table for the model
        db_mock.create_table(NoResultModel)

        # Perform a query that returns no results
        result = db_mock.select(NoResultModel).fetch_first()

        # Assert that fetch_first returns None when no results are found
        assert result is None

    def test_fetch_first_multiple_results(self, db_mock) -> None:
        """Test fetch_first returns the first result as a model instance."""

        # Define a simple model for the test
        class MultipleResultsModel(BaseDBModel):
            name: str

            class Meta:
                table_name: str = "multiple_results_table"

        # Create the table for the model
        db_mock.create_table(MultipleResultsModel)

        # Insert multiple records into the table
        db_mock.insert(MultipleResultsModel(name="John Doe"))
        db_mock.insert(MultipleResultsModel(name="Jane Doe"))

        # Fetch one result
        result = db_mock.select(MultipleResultsModel).fetch_first()

        # Assert that the result is a model instance with the correct data
        assert result is not None
        assert result.name == "John Doe"

    def test_fetch_last_single_result(self, db_mock) -> None:
        """Test that fetch_last returns a single result as a model instance."""

        # Define a simple model for the test
        class SingleResultModel(BaseDBModel):
            name: str

            class Meta:
                table_name: str = "single_result_table"

        # Create the table for the model
        db_mock.create_table(SingleResultModel)

        # Insert a single record into the table
        db_mock.insert(SingleResultModel(name="John Doe"))

        # Fetch one result
        result = db_mock.select(SingleResultModel).fetch_last()

        # Assert that the result is a model instance with the correct data
        assert result is not None
        assert result.name == "John Doe"

    def test_fetch_last_no_results(self, db_mock) -> None:
        """Test that fetch_last returns None when no results are found."""

        # Define a simple model for the test
        class NoResultModel(BaseDBModel):
            name: str

            class Meta:
                table_name: str = "no_result_table"

        # Create the table for the model
        db_mock.create_table(NoResultModel)

        # Perform a query that returns no results
        result = db_mock.select(NoResultModel).fetch_last()

        # Assert that fetch_last returns None when no results are found
        assert result is None

    def fetch_last_multiple_results(self, db_mock) -> None:
        """Test that fetch_last returns the last result as a model instance."""

        # Define a simple model for the test
        class MultipleResultsModel(BaseDBModel):
            name: str

            class Meta:
                table_name: str = "multiple_results_table"

        # Create the table for the model
        db_mock.create_table(MultipleResultsModel)

        # Insert multiple records into the table
        db_mock.insert(MultipleResultsModel(name="John Doe"))
        db_mock.insert(MultipleResultsModel(name="Jane Doe"))

        # Fetch one result
        result = db_mock.select(MultipleResultsModel).fetch_last()

        # Assert that the result is a model instance with the correct data
        assert result is not None
        assert result.name == "Jane Doe"

    def test_filter_single_condition(self, db_mock) -> None:
        """Test filtering with a single condition."""

        # Define a model for the test
        class FilterTestModel(BaseDBModel):
            name: str
            age: int

            class Meta:
                table_name: str = "filter_test_table"

        # Create the table and insert records
        db_mock.create_table(FilterTestModel)
        db_mock.insert(FilterTestModel(name="John Doe", age=30))
        db_mock.insert(FilterTestModel(name="Jane Doe", age=25))
        db_mock.insert(FilterTestModel(name="John Smith", age=40))

        # Perform a query with a single filter condition
        results = (
            db_mock.select(FilterTestModel).filter(name="John Doe").fetch_all()
        )

        # Assert that the filter works and returns the correct record
        assert len(results) == 1
        assert results[0].name == "John Doe"
        assert results[0].age == 30

    def test_filter_multiple_conditions(self, db_mock) -> None:
        """Test filtering with multiple conditions."""

        # Define a model for the test
        class FilterTestModel(BaseDBModel):
            name: str
            age: int

            class Meta:
                table_name: str = "filter_test_table"

        # Create the table and insert records
        db_mock.create_table(FilterTestModel)
        db_mock.insert(FilterTestModel(name="John Doe", age=30))
        db_mock.insert(FilterTestModel(name="Jane Doe", age=25))
        db_mock.insert(FilterTestModel(name="John Smith", age=40))

        # Perform a query with multiple filter conditions
        results = (
            db_mock.select(FilterTestModel)
            .filter(name="John Doe", age=30)
            .fetch_all()
        )

        # Assert that the filter works and returns the correct record
        assert len(results) == 1
        assert results[0].name == "John Doe"
        assert results[0].age == 30

    def test_filter_no_matching_results(self, db_mock) -> None:
        """Test filtering that returns no matching results."""

        # Define a model for the test
        class FilterTestModel(BaseDBModel):
            name: str
            age: int

            class Meta:
                table_name: str = "filter_test_table"

        # Create the table and insert records
        db_mock.create_table(FilterTestModel)
        db_mock.insert(FilterTestModel(name="John Doe", age=30))
        db_mock.insert(FilterTestModel(name="Jane Doe", age=25))

        # Perform a query with a filter condition that doesn't match any records
        results = (
            db_mock.select(FilterTestModel)
            .filter(name="Nonexistent")
            .fetch_all()
        )

        # Assert that no results are returned
        assert len(results) == 0

    def test_filter_numeric_condition(self, db_mock) -> None:
        """Test filtering using a numeric condition."""

        # Define a model for the test
        class FilterTestModel(BaseDBModel):
            name: str
            age: int

            class Meta:
                table_name: str = "filter_test_table"

        # Create the table and insert records
        db_mock.create_table(FilterTestModel)
        db_mock.insert(FilterTestModel(name="John Doe", age=30))
        db_mock.insert(FilterTestModel(name="Jane Doe", age=25))
        db_mock.insert(FilterTestModel(name="John Smith", age=40))

        # Perform a query with a numeric filter condition
        results = db_mock.select(FilterTestModel).filter(age=40).fetch_all()

        # Assert that the filter works and returns the correct record
        assert len(results) == 1
        assert results[0].name == "John Smith"
        assert results[0].age == 40

    def test_filter_multiple_results(self, db_mock) -> None:
        """Test filtering that returns multiple matching results."""

        # Define a model for the test
        class FilterTestModel(BaseDBModel):
            name: str
            age: int

            class Meta:
                table_name: str = "filter_test_table"

        # Create the table and insert records
        db_mock.create_table(FilterTestModel)
        db_mock.insert(FilterTestModel(name="John Doe", age=30))
        db_mock.insert(FilterTestModel(name="Jane Doe", age=25))
        db_mock.insert(FilterTestModel(name="John Smith", age=40))

        # Perform a query that matches multiple records
        results = (
            db_mock.select(FilterTestModel).filter(name="John Doe").fetch_all()
        )

        # Assert that multiple results are returned
        assert len(results) == 1  # Only one 'John Doe'
        assert results[0].name == "John Doe"

    def test_filter_with_none_condition(self, db_mock) -> None:
        """Test filtering with None as a condition."""

        # Define a model for the test
        class FilterTestModel(BaseDBModel):
            name: str
            age: Optional[int] = None

            class Meta:
                table_name: str = "filter_test_table"

        # Create the table and insert records
        db_mock.create_table(FilterTestModel)
        db_mock.insert(FilterTestModel(name="John Doe", age=30))
        db_mock.insert(FilterTestModel(name="Jane Doe", age=None))

        # Perform a query that filters on a None condition
        results = db_mock.select(FilterTestModel).filter(age=None).fetch_all()

        # Assert that the filter works and returns the correct record
        assert len(results) == 1
        assert results[0].name == "Jane Doe"
        assert results[0].age is None

    def test_limit(self, db_mock) -> None:
        """Test that the limit method works as expected."""

        # Define a simple model for the test
        class LimitTestModel(BaseDBModel):
            name: str

            class Meta:
                table_name: str = "limit_test_table"

        # Create the table and insert records
        db_mock.create_table(LimitTestModel)
        db_mock.insert(LimitTestModel(name="John Doe"))
        db_mock.insert(LimitTestModel(name="Jane Doe"))
        db_mock.insert(LimitTestModel(name="Jim Doe"))

        # Perform a query with a limit
        results = db_mock.select(LimitTestModel).limit(2).fetch_all()

        # Assert that the limit works and only returns 2 records
        assert len(results) == 2
        assert results[0].name == "John Doe"
        assert results[1].name == "Jane Doe"

    def test_offset(self, db_mock) -> None:
        """Test that the offset method works as expected."""

        # Define a simple model for the test
        class OffsetTestModel(BaseDBModel):
            name: str

            class Meta:
                table_name: str = "offset_test_table"

        # Create the table and insert records
        db_mock.create_table(OffsetTestModel)
        db_mock.insert(OffsetTestModel(name="John Doe"))
        db_mock.insert(OffsetTestModel(name="Jane Doe"))
        db_mock.insert(OffsetTestModel(name="Jim Doe"))

        # Perform a query with an offset
        results = db_mock.select(OffsetTestModel).offset(1).fetch_all()

        # Assert that the offset works and skips the first record
        assert len(results) == 2
        assert results[0].name == "Jane Doe"
        assert results[1].name == "Jim Doe"

    def test_limit_offset_order_combined(self, db_mock) -> None:
        """Test that limit, offset, and order can work together."""

        # Define a simple model for the test
        class CombinedTestModel(BaseDBModel):
            name: str

            class Meta:
                table_name: str = "combined_test_table"

        # Create the table and insert records
        db_mock.create_table(CombinedTestModel)
        db_mock.insert(CombinedTestModel(name="John Doe"))
        db_mock.insert(CombinedTestModel(name="Jane Doe"))
        db_mock.insert(CombinedTestModel(name="Jim Doe"))
        db_mock.insert(CombinedTestModel(name="Jake Doe"))

        # Perform a query with ordering by name DESC, offset 1, limit 2
        results = (
            db_mock.select(CombinedTestModel)
            .order("name")
            .offset(1)
            .limit(2)
            .fetch_all()
        )

        # Assert that ordering, offset, and limit work together
        assert len(results) == 2
        assert results[0].name == "Jane Doe"
        assert results[1].name == "Jim Doe"

    def test_limit_edge_cases(self, db_mock) -> None:
        """Test limit with edge cases like zero and negative values."""

        # Define a simple model for the test
        class EdgeCaseTestModel(BaseDBModel):
            name: str

            class Meta:
                table_name: str = "edge_case_test_table"

        # Create the table and insert records
        db_mock.create_table(EdgeCaseTestModel)
        db_mock.insert(EdgeCaseTestModel(name="John Doe"))
        db_mock.insert(EdgeCaseTestModel(name="Jane Doe"))

        # Limit with zero should return no results
        results = db_mock.select(EdgeCaseTestModel).limit(0).fetch_all()
        assert len(results) == 0

        # Negative limit should be treated as no limit (all results)
        results = db_mock.select(EdgeCaseTestModel).limit(-1).fetch_all()
        assert len(results) == 2

    def test_offset_exceeding_row_count(self, db_mock) -> None:
        """Test that an offset > the number of rows returns an empty result."""
        # Insert multiple records
        for i in range(3):
            db_mock.insert(
                ExampleModel(
                    slug=f"test{i}",
                    name=f"Test Name {i}",
                    content="Test Content",
                )
            )

        # Query with an offset greater than the total number of rows
        result = db_mock.select(ExampleModel).offset(5).fetch_all()

        # Assert that the result is an empty list
        assert result == []

    def test_offset_edge_cases(self, db_mock) -> None:
        """Test offset with edge cases like zero and negative values."""

        # Define a simple model for the test
        class EdgeCaseOffsetModel(BaseDBModel):
            name: str

            class Meta:
                table_name: str = "edge_case_offset_test_table"

        # Create the table and insert records
        db_mock.create_table(EdgeCaseOffsetModel)
        db_mock.insert(EdgeCaseOffsetModel(name="John Doe"))
        db_mock.insert(EdgeCaseOffsetModel(name="Jane Doe"))

        # Offset with zero should NOT raise InvalidOffsetError
        with not_raises(InvalidOffsetError) as exc:
            db_mock.select(EdgeCaseOffsetModel).offset(0).fetch_all()

        # Negative offset should raise InvalidOffsetError
        with pytest.raises(InvalidOffsetError) as exc:
            db_mock.select(EdgeCaseOffsetModel).offset(-1).fetch_all()
        assert "Invalid offset value: '-1'" in str(exc.value)

        # Valid offset should work normally
        results = db_mock.select(EdgeCaseOffsetModel).offset(1).fetch_all()
        assert len(results) == 1
        assert results[0].name == "Jane Doe"

    def test_query_non_existent_table(self, db_mock) -> None:
        """Test querying a non-existent table raises RecordFetchError."""

        class NonExistentModel(ExampleModel):
            class Meta:
                table_name = "non_existent_table"  # A table that doesn't exist

        with pytest.raises(RecordFetchError):
            db_mock.select(NonExistentModel).fetch_all()

    def test_query_invalid_filter(self, db_mock) -> None:
        """Test applying an invalid filter raises RecordFetchError."""
        # Ensure the table is created
        db_mock.create_table(ExampleModel)

        # Attempt to filter using a non-existent field
        with pytest.raises(InvalidFilterError):
            db_mock.select(ExampleModel).filter(
                non_existent_field="value"
            ).fetch_all()

    def test_query_valid_filter(self, db_mock) -> None:
        """Test that valid filter fields do not raise InvalidFilterError."""
        # Ensure the table is created
        db_mock.create_table(ExampleModel)

        # Apply a filter using a valid field (e.g., 'name')
        try:
            db_mock.select(ExampleModel).filter(name="Valid Name").fetch_all()
        except InvalidFilterError:
            pytest.fail("Valid field raised InvalidFilterError unexpectedly")

    def test_query_mixed_valid_invalid_filter(self, db_mock) -> None:
        """Test a mix of valid and invalid fields raises InvalidFilterError."""
        # Ensure the table is created
        db_mock.create_table(ExampleModel)

        # Attempt to filter using both valid and invalid fields
        with pytest.raises(InvalidFilterError):
            db_mock.select(ExampleModel).filter(
                name="Valid Name", non_existent_field="Invalid"
            ).fetch_all()

    def test_filter_rejects_list_for_equality_operators(self, db_mock) -> None:
        """Test that equality operators reject list values."""
        db_mock.create_table(ExampleModel)

        # Test __eq rejects list
        with pytest.raises(TypeError, match=r"requires scalar.*not list"):
            db_mock.select(ExampleModel).filter(
                name__eq=["value1", "value2"]
            ).fetch_all()

        # Test __ne rejects list
        with pytest.raises(TypeError, match=r"requires scalar.*not list"):
            db_mock.select(ExampleModel).filter(
                name__ne=["value1", "value2"]
            ).fetch_all()

    def test_filter_rejects_list_for_comparison_operators(
        self, db_mock
    ) -> None:
        """Test that comparison operators reject list values."""
        db_mock.create_table(ExampleModel)

        # Test __lt rejects list
        with pytest.raises(TypeError, match=r"requires scalar.*not list"):
            db_mock.select(ExampleModel).filter(name__lt=["a", "b"]).fetch_all()

        # Test __lte rejects list
        with pytest.raises(TypeError, match=r"requires scalar.*not list"):
            db_mock.select(ExampleModel).filter(
                name__lte=["a", "b"]
            ).fetch_all()

        # Test __gt rejects list
        with pytest.raises(TypeError, match=r"requires scalar.*not list"):
            db_mock.select(ExampleModel).filter(name__gt=["a", "b"]).fetch_all()

        # Test __gte rejects list
        with pytest.raises(TypeError, match=r"requires scalar.*not list"):
            db_mock.select(ExampleModel).filter(
                name__gte=["a", "b"]
            ).fetch_all()

    def test_filter_accepts_list_for_in_operators(self, db_mock) -> None:
        """Test that __in and __not_in accept and require list values."""
        db_mock.create_table(ExampleModel)

        # Insert test data
        db_mock.insert(
            ExampleModel(slug="alice", name="Alice", content="Content A")
        )
        db_mock.insert(
            ExampleModel(slug="bob", name="Bob", content="Content B")
        )
        db_mock.insert(
            ExampleModel(slug="charlie", name="Charlie", content="Content C")
        )

        # Test __in accepts list and works correctly
        results = (
            db_mock.select(ExampleModel)
            .filter(name__in=["Alice", "Bob"])
            .fetch_all()
        )
        assert len(results) == 2
        assert {r.name for r in results} == {"Alice", "Bob"}

        # Test __not_in accepts list and works correctly
        results = (
            db_mock.select(ExampleModel)
            .filter(name__not_in=["Alice"])
            .fetch_all()
        )
        assert len(results) == 2
        assert {r.name for r in results} == {"Bob", "Charlie"}

        # Test that __in rejects non-list values
        with pytest.raises(TypeError, match="requires a list"):
            db_mock.select(ExampleModel).filter(name__in="Alice").fetch_all()

    def test_fetch_result_with_list_of_tuples(self, mocker) -> None:
        """Test _fetch_result when _execute_query returns list of tuples."""
        # ensure we get a dependable timestamp
        mocker.patch("time.time", return_value=1234567890)

        db = SqliterDB(memory=True)

        # Create some mock tuples (mimicking database rows)
        mock_result = [
            ("1", "1234567890", "1234567890", "john", "John", "content"),
            ("2", "1234567890", "1234567890", "jane", "Jane", "content"),
        ]

        # Mock the _execute_query method on the QueryBuilder instance
        query = db.select(ExampleModel)
        mocker.patch.object(query, "_execute_query", return_value=mock_result)

        # Perform the fetch_one (this will internally call _fetch_result)
        result = query.fetch_one()

        # Assert that the result is the first tuple in the list and correct type
        # and content
        assert not isinstance(result, list)
        assert isinstance(result, ExampleModel)
        assert result == ExampleModel(
            pk=1,
            updated_at=1234567890,
            created_at=1234567890,
            slug="john",
            name="John",
            content="content",
        )

    def test_exclude_pk_raises_valueerror(self) -> None:
        """Test that excluding the primary key raises a ValueError."""
        match_str = "The primary key 'pk' cannot be excluded."

        db = SqliterDB(memory=True)
        with pytest.raises(ValueError, match=match_str):
            db.select(ExampleModel).exclude(["pk"])

    def test_delete_all_records(self, db_mock) -> None:
        """Test delete() removes all records when no filters are applied."""

        # Define a simple model for the test
        class DeleteTestModel(BaseDBModel):
            name: str

            class Meta:
                table_name: str = "delete_test_table"

        # Create the table and insert some test data
        db_mock.create_table(DeleteTestModel)
        db_mock.insert(DeleteTestModel(name="John"))
        db_mock.insert(DeleteTestModel(name="Jane"))
        db_mock.insert(DeleteTestModel(name="Bob"))

        # Delete all records
        deleted_count = db_mock.select(DeleteTestModel).delete()

        # Assert that all records were deleted
        assert deleted_count == 3
        assert db_mock.select(DeleteTestModel).count() == 0

    def test_delete_filtered_records(self, db_mock) -> None:
        """Test that delete() removes only records matching the filter."""

        # Define a simple model for the test
        class DeleteTestModel(BaseDBModel):
            name: str
            age: int

            class Meta:
                table_name: str = "delete_test_table"

        # Create the table and insert test data
        db_mock.create_table(DeleteTestModel)
        db_mock.insert(DeleteTestModel(name="John", age=25))
        db_mock.insert(DeleteTestModel(name="Jane", age=30))
        db_mock.insert(DeleteTestModel(name="Bob", age=35))

        # Delete records where age > 30
        deleted_count = (
            db_mock.select(DeleteTestModel).filter(age__gt=30).delete()
        )

        # Assert that only one record was deleted
        assert deleted_count == 1
        assert db_mock.select(DeleteTestModel).count() == 2

        # Verify remaining records
        remaining = db_mock.select(DeleteTestModel).order().fetch_all()
        assert len(remaining) == 2
        assert remaining[0].name == "John"
        assert remaining[1].name == "Jane"

    def test_delete_no_matches(self, db_mock) -> None:
        """Test that delete() returns 0 when no records match the filter."""

        # Define a simple model for the test
        class DeleteTestModel(BaseDBModel):
            name: str

            class Meta:
                table_name: str = "delete_test_table"

        # Create the table and insert a test record
        db_mock.create_table(DeleteTestModel)
        db_mock.insert(DeleteTestModel(name="John"))

        # Try to delete records with a filter that won't match
        deleted_count = (
            db_mock.select(DeleteTestModel).filter(name="NonExistent").delete()
        )

        # Assert that no records were deleted
        assert deleted_count == 0
        assert db_mock.select(DeleteTestModel).count() == 1

    def test_delete_with_complex_filters(self, db_mock) -> None:
        """Test deleting records with multiple filter conditions."""

        # Define a model for the test
        class ComplexDeleteModel(BaseDBModel):
            name: str
            age: int
            status: str

            class Meta:
                table_name: str = "complex_delete_table"

        # Create the table and insert test data
        db_mock.create_table(ComplexDeleteModel)
        db_mock.insert(ComplexDeleteModel(name="John", age=25, status="active"))
        db_mock.insert(
            ComplexDeleteModel(name="Jane", age=30, status="inactive")
        )
        db_mock.insert(ComplexDeleteModel(name="Bob", age=35, status="active"))
        db_mock.insert(
            ComplexDeleteModel(name="Alice", age=28, status="active")
        )

        # Delete records with multiple conditions:
        # age > 25 AND status = 'active'
        deleted_count = (
            db_mock.select(ComplexDeleteModel)
            .filter(age__gt=25, status="active")
            .delete()
        )

        # Assert correct number of records were deleted
        assert deleted_count == 2  # Both Bob and Alice meet both conditions
        assert db_mock.select(ComplexDeleteModel).count() == 2

        # Verify the correct records were deleted
        remaining_names = [
            record.name
            for record in db_mock.select(ComplexDeleteModel).order().fetch_all()
        ]
        assert "Bob" not in remaining_names
        assert "Alice" not in remaining_names
        assert set(remaining_names) == {"John", "Jane"}

    def test_delete_with_null_values(self, db_mock) -> None:
        """Test deleting records with NULL value conditions."""

        # Define a model for the test
        class NullDeleteModel(BaseDBModel):
            name: str
            optional_field: Optional[str] = None

            class Meta:
                table_name: str = "null_delete_table"

        # Create the table and insert test data
        db_mock.create_table(NullDeleteModel)
        db_mock.insert(NullDeleteModel(name="John", optional_field="value"))
        db_mock.insert(NullDeleteModel(name="Jane", optional_field=None))
        db_mock.insert(NullDeleteModel(name="Bob", optional_field="other"))
        db_mock.insert(NullDeleteModel(name="Alice", optional_field=None))

        # Delete records where optional_field is NULL
        deleted_count = (
            db_mock.select(NullDeleteModel).filter(optional_field=None).delete()
        )

        # Assert correct number of records were deleted
        assert deleted_count == 2  # Jane and Alice had NULL values
        assert db_mock.select(NullDeleteModel).count() == 2

        # Verify the correct records remain
        remaining = db_mock.select(NullDeleteModel).order().fetch_all()
        assert len(remaining) == 2
        assert all(record.optional_field is not None for record in remaining)
        assert {record.name for record in remaining} == {"John", "Bob"}

    def test_delete_database_error(self, db_mock) -> None:
        """Test that database errors during delete are handled properly."""

        # Define a model for the test
        class ErrorDeleteModel(BaseDBModel):
            name: str

            class Meta:
                table_name: str = "error_delete_table"

        # Create the table and insert a test record
        db_mock.create_table(ErrorDeleteModel)
        db_mock.insert(ErrorDeleteModel(name="John"))

        # Drop the table to simulate a database error
        db_mock.drop_table(ErrorDeleteModel)

        # Delete from the non-existent table should raise RecordDeletionError
        with pytest.raises(RecordDeletionError) as exc:
            db_mock.select(ErrorDeleteModel).delete()

        # Verify the error message
        assert "error_delete_table" in str(exc.value)

    def test_delete_ignores_limit_offset(self, db_mock) -> None:
        """Test that delete operation ignores LIMIT and OFFSET clauses."""

        # Define a model for the test
        class LimitOffsetModel(BaseDBModel):
            name: str

            class Meta:
                table_name: str = "limit_offset_table"

        # Create the table and insert test data
        db_mock.create_table(LimitOffsetModel)
        for name in ["A", "B", "C", "D", "E"]:
            db_mock.insert(LimitOffsetModel(name=name))

        # Try to delete with LIMIT and OFFSET - these should be ignored
        deleted_count = (
            db_mock.select(LimitOffsetModel).limit(2).offset(1).delete()
        )

        # Assert that ALL records were deleted, ignoring LIMIT/OFFSET
        assert deleted_count == 5
        assert db_mock.select(LimitOffsetModel).count() == 0

    def test_delete_with_auto_commit(self, db_mock, mocker) -> None:
        """Test delete behavior with auto_commit enabled and disabled."""

        # Create a model for the test
        class AutoCommitModel(BaseDBModel):
            name: str

            class Meta:
                table_name: str = "auto_commit_table"

        # Create the table and insert test data with auto_commit disabled
        db_mock.auto_commit = False
        db_mock.create_table(AutoCommitModel)
        db_mock.insert(AutoCommitModel(name="Test1"))
        db_mock.insert(AutoCommitModel(name="Test2"))
        db_mock.commit()  # Commit the initial data

        # Mock the _maybe_commit method to track calls
        mock_commit = mocker.patch.object(db_mock, "_maybe_commit")

        # Delete records
        deleted_count = db_mock.select(AutoCommitModel).delete()
        assert deleted_count == 2

        # Verify _maybe_commit was called (delete calls it internally)
        mock_commit.assert_called_once()

        # Test with auto_commit enabled
        db_mock.auto_commit = True
        db_mock.insert(AutoCommitModel(name="Test3"))
        db_mock.insert(AutoCommitModel(name="Test4"))

        # Reset the mock to verify next call
        mock_commit.reset_mock()

        deleted_count = db_mock.select(AutoCommitModel).delete()
        assert deleted_count == 2
        # Verify _maybe_commit was called with auto_commit=True
        mock_commit.assert_called_once()
        # Records should be gone
        assert db_mock.select(AutoCommitModel).count() == 0

    def test_delete_ignores_order(self, db_mock) -> None:
        """Test that delete operation ignores ORDER BY clause."""

        # Define a model for the test
        class OrderModel(BaseDBModel):
            name: str
            value: int

            class Meta:
                table_name: str = "order_table"

        # Create the table and insert test data
        db_mock.create_table(OrderModel)
        db_mock.insert(OrderModel(name="A", value=3))
        db_mock.insert(OrderModel(name="B", value=1))
        db_mock.insert(OrderModel(name="C", value=2))

        # Delete with ORDER BY - should be ignored
        deleted_count = (
            db_mock.select(OrderModel)
            .filter(value__gt=1)
            .order("value", reverse=True)
            .delete()
        )

        # Assert correct records were deleted regardless of order
        assert deleted_count == 2
        remaining = db_mock.select(OrderModel).fetch_all()
        assert len(remaining) == 1
        assert remaining[0].name == "B"
        assert remaining[0].value == 1

    def test_delete_empty_table(self, db_mock) -> None:
        """Test deleting from an empty table."""

        # Define a model for the test
        class EmptyModel(BaseDBModel):
            name: str

            class Meta:
                table_name: str = "empty_table"

        # Create an empty table
        db_mock.create_table(EmptyModel)

        # Attempt to delete from empty table
        deleted_count = db_mock.select(EmptyModel).delete()

        # Should return 0 and not raise any errors
        assert deleted_count == 0
        assert db_mock.select(EmptyModel).count() == 0

    def test_delete_with_debug_logging(self, db_mock, mocker) -> None:
        """Test that delete operation logs SQL when debug is enabled."""

        # Define a model for the test
        class DebugModel(BaseDBModel):
            name: str

            class Meta:
                table_name: str = "debug_table"

        # Create the table and insert test data
        db_mock.create_table(DebugModel)
        db_mock.insert(DebugModel(name="Test1"))
        db_mock.insert(DebugModel(name="Test2"))

        # Enable debug mode and mock the _log_sql method
        db_mock.debug = True
        mock_log = mocker.patch.object(db_mock, "_log_sql")

        # Delete with a filter to generate more complex SQL
        deleted_count = db_mock.select(DebugModel).filter(name="Test1").delete()

        # Verify debug logging was called with correct SQL
        mock_log.assert_called_once()
        sql_arg = mock_log.call_args[0][0]
        assert 'DELETE FROM "debug_table"' in sql_arg
        assert "WHERE" in sql_arg

        # Verify the delete operation still worked
        assert deleted_count == 1
        assert db_mock.select(DebugModel).count() == 1
