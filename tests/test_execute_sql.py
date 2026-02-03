"""Test class for the '_execute_sql' and '_execute' methods."""

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
        mock_log_sql.assert_called_once_with(sql, ())

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


class TestExecuteHelper:
    """Test the _execute helper method of the SqliterDB class."""

    def setup_method(self) -> None:
        """Set up the tests."""
        self.db = SqliterDB(":memory:")

    def teardown_method(self) -> None:
        """Tear down the tests."""
        self.db.close()

    @patch("sqliter.sqliter.SqliterDB._log_sql")
    def test_execute_calls_log_sql(self, mock_log_sql: MagicMock) -> None:
        """Test that _execute always calls _log_sql."""
        conn = self.db.connect()
        cursor = conn.cursor()
        sql = "CREATE TABLE exec_test (id INTEGER PRIMARY KEY)"
        self.db._execute(cursor, sql)
        mock_log_sql.assert_called_once_with(sql, ())

    @patch("sqliter.sqliter.SqliterDB._log_sql")
    def test_execute_passes_values_to_log_sql(
        self, mock_log_sql: MagicMock
    ) -> None:
        """Test that _execute forwards values to _log_sql."""
        self.db._execute_sql(
            "CREATE TABLE exec_vals (id INTEGER PRIMARY KEY, name TEXT)"
        )
        # Reset mock after the CREATE TABLE call
        mock_log_sql.reset_mock()

        conn = self.db.connect()
        cursor = conn.cursor()
        sql = "INSERT INTO exec_vals (name) VALUES (?)"
        values = ("hello",)
        self.db._execute(cursor, sql, values)
        mock_log_sql.assert_called_once_with(sql, values)

    def test_execute_returns_cursor(self) -> None:
        """Test that _execute returns the cursor for chaining."""
        conn = self.db.connect()
        cursor = conn.cursor()
        sql = "CREATE TABLE exec_ret (id INTEGER PRIMARY KEY)"
        result = self.db._execute(cursor, sql)
        assert result is cursor

    def test_execute_with_values(self) -> None:
        """Test that _execute correctly passes values to cursor.execute."""
        self.db._execute_sql(
            "CREATE TABLE exec_data (id INTEGER PRIMARY KEY, name TEXT)"
        )
        conn = self.db.connect()
        cursor = conn.cursor()
        self.db._execute(
            cursor,
            "INSERT INTO exec_data (name) VALUES (?)",
            ("test_value",),
        )
        conn.commit()

        cursor2 = conn.cursor()
        self.db._execute(
            cursor2,
            "SELECT name FROM exec_data WHERE name = ?",
            ("test_value",),
        )
        row = cursor2.fetchone()
        assert row is not None
        assert row[0] == "test_value"
