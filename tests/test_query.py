"""Tests for the query module."""

from typing import Optional

import pytest

from sqliter.exceptions import (
    InvalidFilterError,
    InvalidOffsetError,
    InvalidOrderError,
    RecordFetchError,
)
from sqliter.model import BaseDBModel
from tests.conftest import ExampleModel, not_raises


def test_fetch_all_no_results(db_mock) -> None:
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


def test_fetch_one_single_result(db_mock) -> None:
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


def test_fetch_one_no_results(db_mock) -> None:
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


def test_fetch_first_single_result(db_mock) -> None:
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


def test_fetch_first_no_results(db_mock) -> None:
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


def test_fetch_first_multiple_results(db_mock) -> None:
    """Test that fetch_first returns the first result as a model instance."""

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


def test_fetch_last_single_result(db_mock) -> None:
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


def test_fetch_last_no_results(db_mock) -> None:
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


def fetch_last_multiple_results(db_mock) -> None:
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


def test_filter_single_condition(db_mock) -> None:
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


def test_filter_multiple_conditions(db_mock) -> None:
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


def test_filter_no_matching_results(db_mock) -> None:
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
        db_mock.select(FilterTestModel).filter(name="Nonexistent").fetch_all()
    )

    # Assert that no results are returned
    assert len(results) == 0


def test_filter_numeric_condition(db_mock) -> None:
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


def test_filter_multiple_results(db_mock) -> None:
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


def test_filter_with_none_condition(db_mock) -> None:
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


def test_limit(db_mock) -> None:
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


def test_offset(db_mock) -> None:
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


def test_order_default(db_mock) -> None:
    """Test that the order method works as expected."""

    # Define a simple model for the test
    class OrderTestModel(BaseDBModel):
        name: str

        class Meta:
            table_name: str = "order_test_table"

    # Create the table and insert records
    db_mock.create_table(OrderTestModel)
    db_mock.insert(OrderTestModel(name="John Doe"))
    db_mock.insert(OrderTestModel(name="Jane Doe"))
    db_mock.insert(OrderTestModel(name="Jim Doe"))

    # Perform a query with ordering by name DESC
    results = db_mock.select(OrderTestModel).order("name").fetch_all()

    # Assert that the ordering works in descending order
    assert len(results) == 3
    assert results[0].name == "Jane Doe"
    assert results[1].name == "Jim Doe"
    assert results[2].name == "John Doe"


def test_order_ascending(db_mock) -> None:
    """Test that the order method works as expected when ASC specified."""

    # Define a simple model for the test
    class OrderTestModel(BaseDBModel):
        name: str

        class Meta:
            table_name: str = "order_test_table"

    # Create the table and insert records
    db_mock.create_table(OrderTestModel)
    db_mock.insert(OrderTestModel(name="John Doe"))
    db_mock.insert(OrderTestModel(name="Jane Doe"))
    db_mock.insert(OrderTestModel(name="Jim Doe"))

    # Perform a query with ordering by name DESC
    results = (
        db_mock.select(OrderTestModel)
        .order("name", direction="asc")
        .fetch_all()
    )

    # Assert that the ordering works in descending order
    assert len(results) == 3
    assert results[0].name == "Jane Doe"
    assert results[1].name == "Jim Doe"
    assert results[2].name == "John Doe"


def test_order_desc(db_mock) -> None:
    """Test that the order method works as expected descending."""

    # Define a simple model for the test
    class OrderTestModel(BaseDBModel):
        name: str

        class Meta:
            table_name: str = "order_test_table"

    # Create the table and insert records
    db_mock.create_table(OrderTestModel)
    db_mock.insert(OrderTestModel(name="John Doe"))
    db_mock.insert(OrderTestModel(name="Jane Doe"))
    db_mock.insert(OrderTestModel(name="Jim Doe"))

    # Perform a query with ordering by name DESC
    results = (
        db_mock.select(OrderTestModel)
        .order("name", direction="desc")
        .fetch_all()
    )

    # Assert that the ordering works in descending order
    assert len(results) == 3
    assert results[0].name == "John Doe"
    assert results[1].name == "Jim Doe"
    assert results[2].name == "Jane Doe"


def test_limit_offset_order_combined(db_mock) -> None:
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


def test_order_invalid_direction(db_mock) -> None:
    """Test that an invalid order direction raises an exception."""

    # Define a simple model for the test
    class InvalidOrderModel(BaseDBModel):
        name: str

        class Meta:
            table_name: str = "invalid_order_test_table"

    # Create the table for the model
    db_mock.create_table(InvalidOrderModel)

    # Attempt to order by an invalid direction
    with pytest.raises(InvalidOrderError) as exc:
        db_mock.select(InvalidOrderModel).order("name", direction="invalid")

    assert (
        "Invalid order value - 'invalid' is not a valid sorting direction"
        in str(exc.value)
    )


def test_order_invalid_field(db_mock) -> None:
    """Test that an invalid order field raises an exception."""

    # Define a simple model for the test
    class InvalidOrderModel(BaseDBModel):
        name: str

        class Meta:
            table_name: str = "invalid_order_test_table"

    # Create the table for the model
    db_mock.create_table(InvalidOrderModel)

    # Attempt to order by an invalid field
    with pytest.raises(InvalidOrderError) as exc:
        db_mock.select(InvalidOrderModel).order("invalid_field")

    assert "Invalid order value - 'invalid_field' does not exist" in str(
        exc.value
    )


def test_limit_edge_cases(db_mock) -> None:
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


def test_offset_exceeding_row_count(db_mock) -> None:
    """Test that an offset > the number of rows returns an empty result."""
    # Insert multiple records
    for i in range(3):
        db_mock.insert(
            ExampleModel(
                slug=f"test{i}", name=f"Test Name {i}", content="Test Content"
            )
        )

    # Query with an offset greater than the total number of rows
    result = db_mock.select(ExampleModel).offset(5).fetch_all()

    # Assert that the result is an empty list
    assert result == []


def test_offset_edge_cases(db_mock) -> None:
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


def test_query_non_existent_table(db_mock) -> None:
    """Test querying a non-existent table raises RecordFetchError."""

    class NonExistentModel(ExampleModel):
        class Meta:
            table_name = "non_existent_table"  # A table that doesn't exist

    with pytest.raises(RecordFetchError):
        db_mock.select(NonExistentModel).fetch_all()


def test_query_invalid_filter(db_mock) -> None:
    """Test applying an invalid filter raises RecordFetchError."""
    # Ensure the table is created
    db_mock.create_table(ExampleModel)

    # Attempt to filter using a non-existent field
    with pytest.raises(InvalidFilterError):
        db_mock.select(ExampleModel).filter(
            non_existent_field="value"
        ).fetch_all()


def test_query_valid_filter(db_mock) -> None:
    """Test that valid filter fields do not raise InvalidFilterError."""
    # Ensure the table is created
    db_mock.create_table(ExampleModel)

    # Apply a filter using a valid field (e.g., 'name')
    try:
        db_mock.select(ExampleModel).filter(name="Valid Name").fetch_all()
    except InvalidFilterError:
        pytest.fail("Valid field raised InvalidFilterError unexpectedly")


def test_query_mixed_valid_invalid_filter(db_mock) -> None:
    """Test that a mix of valid and invalid fields raises InvalidFilterError."""
    # Ensure the table is created
    db_mock.create_table(ExampleModel)

    # Attempt to filter using both valid and invalid fields
    with pytest.raises(InvalidFilterError):
        db_mock.select(ExampleModel).filter(
            name="Valid Name", non_existent_field="Invalid"
        ).fetch_all()
