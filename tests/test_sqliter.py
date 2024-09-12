"""Test suite for the 'sqliter' library."""

import pytest
from sqliter import SqliterDB
from sqliter.exceptions import RecordFetchError, RecordNotFoundError
from sqliter.model import BaseDBModel

from tests.conftest import ExampleModel

# License model for testing


def test_create_table(db_mock) -> None:
    """Test table creation."""
    with db_mock.connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        assert len(tables) == 1
        assert tables[0][0] == "test_table"


def test_create_table_with_auto_increment(db_mock) -> None:
    """Test table creation with auto-incrementing primary key."""

    class AutoIncrementModel(BaseDBModel):
        name: str

        class Meta:
            create_id: bool = True  # Enable auto-increment ID
            primary_key: str = "id"  # Default primary key is 'id'
            table_name: str = "auto_increment_table"

    # Create the table
    db_mock.create_table(AutoIncrementModel)

    # Verify that the table was created with an auto-incrementing primary key
    with db_mock.connect() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(auto_increment_table);")
        table_info = cursor.fetchall()

    # Check that the first column is 'id' and it's an auto-incrementing integer
    assert table_info[0][1] == "id"  # Column name
    assert table_info[0][2] == "INTEGER"  # Column type
    assert table_info[0][5] == 1  # Primary key flag


def test_create_table_with_custom_primary_key(db_mock) -> None:
    """Test table creation with a custom primary key."""

    class CustomPKModel(BaseDBModel):
        code: str
        description: str

        class Meta:
            create_id: bool = False  # Disable auto-increment ID
            primary_key: str = "code"  # Use 'code' as the primary key
            table_name: str = "custom_pk_table"

    # Create the table
    db_mock.create_table(CustomPKModel)

    # Verify that the table was created with 'code' as the primary key
    with db_mock.connect() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(custom_pk_table);")
        table_info = cursor.fetchall()

    # Check that the primary key is the 'code' column
    primary_key_column = next(col for col in table_info if col[1] == "code")
    assert primary_key_column[1] == "code"  # Column name
    assert primary_key_column[5] == 1  # Primary key flag


def test_create_table_with_custom_auto_increment_pk(db_mock) -> None:
    """Test table creation with a custom auto-incrementing primary key."""

    class CustomAutoIncrementPKModel(BaseDBModel):
        name: str

        class Meta:
            create_id: bool = True  # Enable auto-increment ID
            primary_key: str = "custom_id"  # Use 'custom_id' as the primary key
            table_name: str = "custom_auto_increment_pk_table"

    # Create the table
    db_mock.create_table(CustomAutoIncrementPKModel)

    # Check the table schema using PRAGMA
    with db_mock.connect() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(custom_auto_increment_pk_table);")
        table_info = cursor.fetchall()

    # Check that the 'custom_id' column is INTEGER and a primary key
    primary_key_column = next(
        col for col in table_info if col[1] == "custom_id"
    )
    assert primary_key_column[1] == "custom_id"  # Column name
    assert primary_key_column[2] == "INTEGER"  # Column type
    assert primary_key_column[5] == 1  # Primary key flag

    # Insert rows to verify that the custom primary key auto-increments
    model_instance1 = CustomAutoIncrementPKModel(name="First Entry")
    model_instance2 = CustomAutoIncrementPKModel(name="Second Entry")

    db_mock.insert(model_instance1)
    db_mock.insert(model_instance2)

    # Fetch the inserted rows and check the 'custom_id' values
    with db_mock.connect() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT custom_id, name FROM custom_auto_increment_pk_table;"
        )
        results = cursor.fetchall()

    # Check that the custom_id column auto-incremented
    assert results[0][0] == 1
    assert results[1][0] == 2
    assert results[0][1] == "First Entry"
    assert results[1][1] == "Second Entry"


def test_default_table_name(db_mock) -> None:
    """Test that the table name defaults to the class name in lowercase."""

    class DefaultNameModel(BaseDBModel):
        name: str

        class Meta:
            table_name = None  # Explicitly set to None to test the default

    # Verify that get_table_name defaults to class name in lowercase
    assert DefaultNameModel.get_table_name() == "defaultnamemodel"


def test_insert_license(db_mock) -> None:
    """Test inserting a license into the database."""
    test_model = ExampleModel(
        slug="mit", name="MIT License", content="MIT License Content"
    )
    db_mock.insert(test_model)

    with db_mock.connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM test_table WHERE slug = ?", ("mit",))
        result = cursor.fetchone()
        assert result[0] == "mit"
        assert result[1] == "MIT License"
        assert result[2] == "MIT License Content"


def test_fetch_license(db_mock) -> None:
    """Test fetching a license by primary key."""
    test_model = ExampleModel(
        slug="gpl", name="GPL License", content="GPL License Content"
    )
    db_mock.insert(test_model)

    fetched_license = db_mock.get(ExampleModel, "gpl")
    assert fetched_license is not None
    assert fetched_license.slug == "gpl"
    assert fetched_license.name == "GPL License"
    assert fetched_license.content == "GPL License Content"


def test_update_license(db_mock) -> None:
    """Test updating an existing license."""
    test_model = ExampleModel(
        slug="mit", name="MIT License", content="MIT License Content"
    )
    db_mock.insert(test_model)

    # Update license content
    test_model.content = "Updated MIT License Content"
    db_mock.update(test_model)

    # Fetch and check if updated
    fetched_license = db_mock.get(ExampleModel, "mit")
    assert fetched_license.content == "Updated MIT License Content"


def test_delete_license(db_mock) -> None:
    """Test deleting a license."""
    test_model = ExampleModel(
        slug="mit", name="MIT License", content="MIT License Content"
    )
    db_mock.insert(test_model)

    # Delete the record
    db_mock.delete(ExampleModel, "mit")

    # Ensure it no longer exists
    fetched_license = db_mock.get(ExampleModel, "mit")
    assert fetched_license is None


def test_select_filter(db_mock) -> None:
    """Test filtering licenses using the QueryBuilder."""
    license1 = ExampleModel(
        slug="mit", name="MIT License", content="MIT License Content"
    )
    license2 = ExampleModel(
        slug="gpl", name="GPL License", content="GPL License Content"
    )
    db_mock.insert(license1)
    db_mock.insert(license2)

    # Query and filter licenses
    filtered = (
        db_mock.select(ExampleModel).filter(name="GPL License").fetch_all()
    )
    assert len(filtered) == 1
    assert filtered[0].slug == "gpl"


def test_query_fetch_first(db_mock) -> None:
    """Test fetching the first record."""
    license1 = ExampleModel(
        slug="mit", name="MIT License", content="MIT License Content"
    )
    license2 = ExampleModel(
        slug="gpl", name="GPL License", content="GPL License Content"
    )
    db_mock.insert(license1)
    db_mock.insert(license2)

    first_record = db_mock.select(ExampleModel).fetch_first()
    assert first_record.slug == "mit"


def test_query_fetch_last(db_mock) -> None:
    """Test fetching the last record."""
    license1 = ExampleModel(
        slug="mit", name="MIT License", content="MIT License Content"
    )
    license2 = ExampleModel(
        slug="gpl", name="GPL License", content="GPL License Content"
    )
    db_mock.insert(license1)
    db_mock.insert(license2)

    last_record = db_mock.select(ExampleModel).fetch_last()
    assert last_record.slug == "gpl"


def test_count_records(db_mock) -> None:
    """Test counting records in the database."""
    license1 = ExampleModel(
        slug="mit", name="MIT License", content="MIT License Content"
    )
    license2 = ExampleModel(
        slug="gpl", name="GPL License", content="GPL License Content"
    )
    db_mock.insert(license1)
    db_mock.insert(license2)

    count = db_mock.select(ExampleModel).count()
    assert count == 2


def test_exists_record(db_mock) -> None:
    """Test checking if a record exists."""
    license1 = ExampleModel(
        slug="mit", name="MIT License", content="MIT License Content"
    )
    db_mock.insert(license1)

    exists = db_mock.select(ExampleModel).filter(slug="mit").exists()
    assert exists


def test_transaction_commit(db_mock, mocker) -> None:
    """Test if auto_commit works correctly when enabled."""
    # Mock the commit method on the connection
    mock_conn = mocker.MagicMock()

    # Manually reset the connection to ensure our mock is used
    db_mock.conn = mock_conn

    # Patch connect method to return the mock connection
    mocker.patch.object(db_mock, "connect", return_value=mock_conn)

    license1 = ExampleModel(
        slug="mit", name="MIT License", content="MIT License Content"
    )

    with db_mock:
        db_mock.create_table(ExampleModel)
        db_mock.insert(license1)

    # Ensure commit was called once during the context (due to auto_commit=True)
    mock_conn.commit.assert_called_once()


def test_transaction_manual_commit(mocker) -> None:
    """Test manual commit when auto_commit is set to False."""
    db_manual = SqliterDB(":memory:", auto_commit=False)

    # Mock the connection and commit
    mock_conn = mocker.MagicMock()
    mocker.patch.object(db_manual, "connect", return_value=mock_conn)

    license1 = ExampleModel(
        slug="mit", name="MIT License", content="MIT License Content"
    )

    with db_manual:
        db_manual.create_table(ExampleModel)
        db_manual.insert(license1)
        # Ensure commit hasn't been called yet
        mock_conn.commit.assert_not_called()

    # After leaving the context, commit should still not be called (since
    # auto_commit=False)
    mock_conn.commit.assert_not_called()


def test_update_existing_record(db_mock) -> None:
    """Test that updating an existing record works correctly."""
    # Insert an example record
    example_model = ExampleModel(
        slug="test", name="Test License", content="Test Content"
    )
    db_mock.insert(example_model)

    # Update the record's content
    example_model.content = "Updated Content"
    db_mock.update(example_model)

    # Fetch the updated record and verify the changes
    updated_record = db_mock.get(ExampleModel, "test")
    assert updated_record is not None
    assert updated_record.content == "Updated Content"


def test_update_non_existing_record(db_mock) -> None:
    """Test that updating a non-existing record raises RecordNotFoundError."""
    # Create an example record that is not inserted into the DB
    example_model = ExampleModel(
        slug="nonexistent",
        name="Nonexistent License",
        content="Nonexistent Content",
    )

    # Try updating the non-existent record
    with pytest.raises(RecordNotFoundError) as exc_info:
        db_mock.update(example_model)

    # Check that the correct error message is raised
    assert "No record found for key 'nonexistent'" in str(exc_info.value)


def test_get_non_existent_table(db_mock) -> None:
    """Test fetching from a non-existent table raises RecordFetchError."""

    class NonExistentModel(ExampleModel):
        class Meta:
            table_name = "non_existent_table"  # A table that doesn't exist

    with pytest.raises(RecordFetchError):
        db_mock.get(NonExistentModel, "non_existent_key")


def test_get_record_no_result(db_mock) -> None:
    """Test fetching a non-existent record returns None."""
    result = db_mock.get(ExampleModel, "non_existent_key")
    assert result is None
