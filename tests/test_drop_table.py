"""Test the 'drop_table' method of the 'SqliterDB' class."""

import sqlite3

import pytest

from sqliter import SqliterDB
from sqliter.exceptions import TableDeletionError
from sqliter.model import BaseDBModel


class TestDropTable:
    """Test class for the 'drop_table' method."""

    def test_drop_existing_table(self, db_mock) -> None:
        """Test dropping an existing table."""

        class TestModel(BaseDBModel):
            name: str

            class Meta:
                table_name = "test_drop_table"

        db_mock.create_table(TestModel)
        db_mock.drop_table(TestModel)

        # Verify the table no longer exists
        with db_mock.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name='test_drop_table'"
            )
            result = cursor.fetchone()
        assert result is None

    def test_drop_non_existent_table(self, db_mock) -> None:
        """Test dropping a table that doesn't exist."""

        class NonExistentModel(BaseDBModel):
            name: str

            class Meta:
                table_name = "non_existent_table"

        # This should not raise an exception due to 'IF EXISTS' in the SQL
        db_mock.drop_table(NonExistentModel)

    def test_drop_table_with_data(self, db_mock) -> None:
        """Test dropping a table that contains data."""

        class DataModel(BaseDBModel):
            name: str

            class Meta:
                table_name = "data_table"

        db_mock.create_table(DataModel)
        db_mock.insert(DataModel(name="Test Data"))

        db_mock.drop_table(DataModel)

        # Verify the table no longer exists
        with db_mock.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name='data_table'"
            )
            result = cursor.fetchone()
        assert result is None

    def test_drop_table_error(self, db_mock: SqliterDB, mocker) -> None:
        """Test error handling when dropping a table fails."""

        class ErrorModel(BaseDBModel):
            name: str

            class Meta:
                table_name = "error_table"

        mocker.patch.object(db_mock, "connect", side_effect=sqlite3.Error)

        with pytest.raises(TableDeletionError) as exc_info:
            db_mock.drop_table(ErrorModel)

        assert "Failed to delete the table: 'error_table'" in str(
            exc_info.value
        )

    def test_drop_table_auto_commit(self, db_mock, mocker) -> None:
        """Test auto-commit behavior when dropping a table."""

        class CommitModel(BaseDBModel):
            name: str

            class Meta:
                table_name = "commit_table"

        mock_commit = mocker.patch.object(db_mock, "commit")
        db_mock.drop_table(CommitModel)
        mock_commit.assert_called_once()
