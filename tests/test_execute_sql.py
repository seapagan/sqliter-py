"""Test class for the '_execute_sql' method."""

from unittest.mock import MagicMock, patch

import pytest

from sqliter import SqliterDB
from sqliter.exceptions import SqlExecutionError


class TestExecuteSQL:
    """Test the _execute_sql method of the SqliterDB class."""

    def setup_method(self) -> None:
        """Setup the tests."""
        self.db = SqliterDB(":memory:")

    def teardown_method(self) -> None:
        """Teardown the tests."""
        self.db.close()

    def test_execute_sql_success(self) -> None:
        """Test successful SQL execution."""
        sql = "CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)"
        self.db._execute_sql(sql)

        # Verify the table was created
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name='test'"
            )
            result = cursor.fetchone()
        assert result is not None
        assert result[0] == "test"

    def test_execute_sql_error(self) -> None:
        """Test SQL execution with an error."""
        # Missing closing parenthesis...
        invalid_sql = "CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT"
        with pytest.raises(SqlExecutionError):
            self.db._execute_sql(invalid_sql)

    @patch("sqliter.sqliter.SqliterDB._log_sql")
    def test_execute_sql_debug_logging(self, mock_log_sql: MagicMock) -> None:
        """Test that SQL is logged when debug is True."""
        self.db.debug = True
        sql = "CREATE TABLE test_log (id INTEGER PRIMARY KEY)"
        self.db._execute_sql(sql)
        mock_log_sql.assert_called_once_with(sql, [])

    def test_execute_sql_commit(self) -> None:
        """Test that changes are committed after SQL execution."""
        self.db.auto_commit = False  # Disable auto-commit to test manual commit
        sql = "CREATE TABLE test_commit (id INTEGER PRIMARY KEY)"
        self.db._execute_sql(sql)

        # Verify the table exists even with auto_commit off
        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name='test_commit'"
            )
            result = cursor.fetchone()
        assert result is not None
        assert result[0] == "test_commit"

    def test_execute_sql_multiple_statements(self) -> None:
        """Test executing multiple SQL statements raises an error."""
        sql = """
        CREATE TABLE test_multi (id INTEGER PRIMARY KEY, name TEXT);
        INSERT INTO test_multi (name) VALUES ('test');
        """
        with pytest.raises(SqlExecutionError) as exc_info:
            self.db._execute_sql(sql)

        assert "You can only execute one statement at a time." in str(
            exc_info.value
        )

    def test_execute_sql_with_parameters(self) -> None:
        """Test that _execute_sql doesn't support parameters directly."""
        self.db._execute_sql(
            "CREATE TABLE test_params (id INTEGER PRIMARY KEY, name TEXT)"
        )
        sql = "INSERT INTO test_params (name) VALUES (?)"
        with pytest.raises(SqlExecutionError):
            self.db._execute_sql(
                sql
            )  # This should fail as _execute_sql doesn't support parameters
