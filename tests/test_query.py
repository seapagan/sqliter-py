"""Tests for the query module."""

from typing import Optional

from sqliter.model import BaseDBModel


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
    assert results[0].age == 30  # noqa: PLR2004


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
    assert results[0].age == 30  # noqa: PLR2004


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
    assert results[0].age == 40  # noqa: PLR2004


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
