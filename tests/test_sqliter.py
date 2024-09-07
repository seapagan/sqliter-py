"""Test suite for the 'sqliter' library."""

import sqlite3

from sqliter import SqliterDB
from sqliter.model import BaseDBModel


# License model for testing
class ExampleModel(BaseDBModel):
    """Define a model to use in the tests."""

    slug: str
    name: str
    content: str

    class Meta:
        """Configuration for the model."""

        create_id: bool = False
        primary_key: str = "slug"
        table_name: str = "test_table"


def test_create_table(db_mock) -> None:
    """Test table creation."""
    with db_mock.connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        assert len(tables) == 1
        assert tables[0][0] == "test_table"


def test_insert_license(db_mock) -> None:
    """Test inserting a license into the database."""
    license = ExampleModel(
        slug="mit", name="MIT License", content="MIT License Content"
    )
    db_mock.insert(license)

    with db_mock.connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM test_table WHERE slug = ?", ("mit",))
        result = cursor.fetchone()
        assert result[0] == "mit"
        assert result[1] == "MIT License"
        assert result[2] == "MIT License Content"


def test_fetch_license(db_mock) -> None:
    """Test fetching a license by primary key."""
    license = ExampleModel(
        slug="gpl", name="GPL License", content="GPL License Content"
    )
    db_mock.insert(license)

    fetched_license = db_mock.get(ExampleModel, "gpl")
    assert fetched_license is not None
    assert fetched_license.slug == "gpl"
    assert fetched_license.name == "GPL License"
    assert fetched_license.content == "GPL License Content"


def test_update_license(db_mock) -> None:
    """Test updating an existing license."""
    license = ExampleModel(
        slug="mit", name="MIT License", content="MIT License Content"
    )
    db_mock.insert(license)

    # Update license content
    license.content = "Updated MIT License Content"
    db_mock.update(license)

    # Fetch and check if updated
    fetched_license = db_mock.get(ExampleModel, "mit")
    assert fetched_license.content == "Updated MIT License Content"


def test_delete_license(db_mock) -> None:
    """Test deleting a license."""
    license = ExampleModel(
        slug="mit", name="MIT License", content="MIT License Content"
    )
    db_mock.insert(license)

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
