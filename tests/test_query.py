"""Tests for the query module."""

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
