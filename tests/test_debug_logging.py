"""Testd the debug logging for the SqliterDB class."""

import logging

from sqliter.sqliter import SqliterDB
from tests.conftest import ComplexModel


class TestDebugLogging:
    """Test class for the debug logging in the SqliterDB class."""

    def test_sqliterdb_debug_default(self) -> None:
        """Test that the default value for the debug flag is False."""
        db = SqliterDB(":memory:")  # No debug argument passed
        assert db.debug is False, "The debug flag should be False by default."

    def test_sqliterdb_debug_set_false(self) -> None:
        """Test that the default value for the debug flag is False."""
        db = SqliterDB(":memory:", debug=False)  # Set debug argument to False
        assert db.debug is False, (
            "The debug flag should be False when explicitly passed as False."
        )

    def test_sqliterdb_debug_set_true(self) -> None:
        """Test that the debug flag can be set to True."""
        db = SqliterDB(":memory:", debug=True)  # Set debug argument to True
        assert db.debug is True, (
            "The debug flag should be True when explicitly passed as True."
        )

    def test_debug_sql_output_basic_query(
        self, db_mock_complex_debug: SqliterDB, caplog
    ) -> None:
        """Test the debug output correctly prints the SQL query and values."""
        with caplog.at_level(logging.DEBUG):
            db_mock_complex_debug.select(ComplexModel).filter(
                age=30.5
            ).fetch_all()

        # Assert the SQL query was printed
        assert (
            'Executing SQL: SELECT "pk", "created_at", "updated_at", "name", '
            '"age", "is_active", "score", '
            '"nullable_field" FROM "complex_model" WHERE age = 30.5'
            in caplog.text
        )

    def test_debug_sql_output_string_values(
        self, db_mock_complex_debug: SqliterDB, caplog
    ) -> None:
        """Test that the debug output correctly handles string values."""
        with caplog.at_level(logging.DEBUG):
            db_mock_complex_debug.select(ComplexModel).filter(
                name="Alice"
            ).fetch_all()

        # Assert the SQL query was printed with the string properly quoted
        assert (
            'Executing SQL: SELECT "pk", "created_at", "updated_at", "name", '
            '"age", "is_active", "score", '
            '"nullable_field" FROM "complex_model" WHERE name = \'Alice\''
            in caplog.text
        )

    def test_debug_sql_output_multiple_conditions(
        self, db_mock_complex_debug: SqliterDB, caplog
    ) -> None:
        """Test that the debug output works with multiple conditions."""
        with caplog.at_level(logging.DEBUG):
            db_mock_complex_debug.select(ComplexModel).filter(
                name="Alice", age=30.5
            ).fetch_all()

        # Assert the SQL query was printed with multiple conditions
        assert (
            'Executing SQL: SELECT "pk", "created_at", "updated_at", "name", '
            '"age", "is_active", "score", '
            '"nullable_field" FROM "complex_model" WHERE name = \'Alice\' AND '
            "age = 30.5" in caplog.text
        )

    def test_debug_sql_output_order_and_limit(
        self, db_mock_complex_debug: SqliterDB, caplog
    ) -> None:
        """Test that the debug output works with order and limit."""
        with caplog.at_level(logging.DEBUG):
            db_mock_complex_debug.select(ComplexModel).order(
                "age", reverse=True
            ).limit(1).fetch_all()

        # Assert the SQL query was printed with ORDER and LIMIT
        assert (
            'Executing SQL: SELECT "pk", "created_at", "updated_at", "name", '
            '"age", "is_active", "score", '
            '"nullable_field" FROM "complex_model" ORDER BY "age" DESC LIMIT 1'
            in caplog.text
        )

    def test_debug_sql_output_with_null_value(
        self, db_mock_complex_debug: SqliterDB, caplog
    ) -> None:
        """Test that the debug output works when filtering on a NULL value."""
        with caplog.at_level(logging.DEBUG):
            db_mock_complex_debug.insert(
                ComplexModel(
                    pk=4,
                    name="David",
                    age=40.0,
                    is_active=True,
                    score=80.0,
                    nullable_field=None,
                )
            )

            db_mock_complex_debug.select(ComplexModel).filter(
                age__isnull=True
            ).fetch_all()

        # Assert the SQL query was printed with IS NULL
        assert (
            'Executing SQL: SELECT "pk", "created_at", "updated_at", "name", '
            '"age", "is_active", "score", '
            '"nullable_field" FROM "complex_model" WHERE age IS NULL'
            in caplog.text
        )

    def test_debug_sql_output_with_fields_single(
        self, db_mock_complex_debug: SqliterDB, caplog
    ) -> None:
        """Test debug output correct when selecting a single field."""
        with caplog.at_level(logging.DEBUG):
            db_mock_complex_debug.select(ComplexModel).fields(
                ["name"]
            ).fetch_all()

        # Assert the SQL query only selects the 'name' field
        assert (
            'Executing SQL: SELECT "name", "pk" FROM "complex_model"'
            in caplog.text
        )

    def test_debug_sql_output_with_fields_multiple(
        self, db_mock_complex_debug: SqliterDB, caplog
    ) -> None:
        """Test that the debug output correct when selecting multiple fields."""
        with caplog.at_level(logging.DEBUG):
            db_mock_complex_debug.select(ComplexModel).fields(
                ["name", "age"]
            ).fetch_all()

        # Assert the SQL query only selects the 'name' and 'age' fields
        assert (
            'Executing SQL: SELECT "name", "age", "pk" FROM "complex_model"'
            in caplog.text
        )

    def test_debug_sql_output_with_fields_and_filter(
        self, db_mock_complex_debug: SqliterDB, caplog
    ) -> None:
        """Test the debug output correct with selected fields and a filter."""
        with caplog.at_level(logging.DEBUG):
            db_mock_complex_debug.select(ComplexModel).fields(
                ["name", "score"]
            ).filter(score__gt=85).fetch_all()

        # Assert the SQL query selects 'name' and 'score' and applies the filter
        assert (
            'Executing SQL: SELECT "name", "score", "pk" FROM "complex_model" '
            "WHERE score > 85" in caplog.text
        )

    def test_no_log_output_when_debug_false(self, caplog) -> None:
        """Test that no log output occurs when debug=False."""
        db = SqliterDB(":memory:", debug=False)
        db.create_table(ComplexModel)

        with caplog.at_level(logging.DEBUG):
            db.select(ComplexModel).filter(age=30.5).fetch_all()

        # Assert that there is no log output
        assert caplog.text == ""

    def test_no_log_output_above_debug_level(
        self, db_mock_complex_debug: SqliterDB, caplog
    ) -> None:
        """Test no DEBUG log output occurs when log level is above DEBUG."""
        with caplog.at_level(logging.INFO):  # Set log level higher than DEBUG
            db_mock_complex_debug.select(ComplexModel).filter(
                age=30.5
            ).fetch_all()

        # Assert that no DEBUG messages are present in the logs
        assert caplog.text == ""

    def test_manual_logger_respects_debug_flag(self, caplog) -> None:
        """Test that a manually passed logger respects the debug flag."""
        custom_logger = logging.getLogger("CustomLogger")
        custom_logger.setLevel(logging.DEBUG)
        db = SqliterDB(":memory:", debug=True, logger=custom_logger)
        db.create_table(ComplexModel)

        with caplog.at_level(logging.DEBUG):
            db.select(ComplexModel).filter(age=30.5).fetch_all()

        # Assert that log output was captured with the manually passed logger
        assert (
            'Executing SQL: SELECT "pk", "created_at", "updated_at", "name", '
            '"age", "is_active", "score", ' in caplog.text
        )

    def test_manual_logger_above_debug_level(self, caplog) -> None:
        """Ensure no log output when manually passed logger is above DEBUG."""
        custom_logger = logging.getLogger("CustomLogger")
        custom_logger.setLevel(logging.INFO)  # Set log level higher than DEBUG

        db = SqliterDB(":memory:", debug=True, logger=custom_logger)
        db.create_table(ComplexModel)

        with caplog.at_level(logging.INFO):  # Use caplog at INFO level
            db.select(ComplexModel).filter(age=30.5).fetch_all()

        # Assert that no DEBUG messages were logged
        assert caplog.text == ""

    def test_debug_sql_output_no_matching_records(
        self, db_mock_complex_debug: SqliterDB, caplog
    ) -> None:
        """Test the debug output occurs even when no records match the query."""
        with caplog.at_level(logging.DEBUG):
            db_mock_complex_debug.select(ComplexModel).filter(
                age=100
            ).fetch_all()  # No records with age=100

        # Assert that the SQL query was logged despite no matching records
        assert (
            'Executing SQL: SELECT "pk", "created_at", "updated_at", "name", '
            '"age", "is_active", "score", '
            '"nullable_field" FROM "complex_model" WHERE age = 100'
            in caplog.text
        )

    def test_debug_sql_output_empty_query(
        self, db_mock_complex_debug: SqliterDB, caplog
    ) -> None:
        """Test debug output occurs for empty query (no filters, etc)."""
        with caplog.at_level(logging.DEBUG):
            db_mock_complex_debug.select(ComplexModel).fetch_all()

        # Assert that the SQL query was logged for a full table scan
        assert (
            'Executing SQL: SELECT "pk", "created_at", "updated_at", "name", '
            '"age", "is_active", "score", '
            '"nullable_field" FROM "complex_model"' in caplog.text
        )

    def test_debug_output_drop_table(
        self, db_mock_complex_debug: SqliterDB, caplog
    ) -> None:
        """Test debug output when dropping a table."""
        with caplog.at_level(logging.DEBUG):
            db_mock_complex_debug.drop_table(ComplexModel)

        # Assert the SQL query for dropping the table was logged
        assert (
            "Executing SQL: DROP TABLE IF EXISTS complex_model" in caplog.text
        )

    def test_reset_database_debug_logging(self, temp_db_path, caplog) -> None:
        """Test that resetting the database logs debug information."""
        with caplog.at_level(logging.DEBUG):
            SqliterDB(temp_db_path, reset=True, debug=True)

        assert "Database reset: 0 user-created tables dropped." in caplog.text

    def test_debug_output_insert(
        self, db_mock_complex_debug: SqliterDB, caplog
    ) -> None:
        """Test that insert operations produce debug log output."""
        with caplog.at_level(logging.DEBUG):
            db_mock_complex_debug.insert(
                ComplexModel(
                    name="DebugTest",
                    age=25.0,
                    is_active=True,
                    score=90.0,
                    nullable_field=None,
                )
            )

        assert "Executing SQL:" in caplog.text
        assert "INSERT INTO complex_model" in caplog.text

    def test_debug_output_get(
        self, db_mock_complex_debug: SqliterDB, caplog
    ) -> None:
        """Test that get operations produce debug log output."""
        with caplog.at_level(logging.DEBUG):
            db_mock_complex_debug.get(ComplexModel, 1)

        assert "Executing SQL:" in caplog.text
        assert "SELECT" in caplog.text
        assert "complex_model" in caplog.text

    def test_debug_output_update(
        self, db_mock_complex_debug: SqliterDB, caplog
    ) -> None:
        """Test that update operations produce debug log output."""
        record = db_mock_complex_debug.get(ComplexModel, 1)
        assert record is not None
        record.name = "Updated"

        with caplog.at_level(logging.DEBUG):
            db_mock_complex_debug.update(record)

        assert "Executing SQL:" in caplog.text
        assert "UPDATE complex_model" in caplog.text

    def test_debug_output_delete(
        self, db_mock_complex_debug: SqliterDB, caplog
    ) -> None:
        """Test that delete operations produce debug log output."""
        with caplog.at_level(logging.DEBUG):
            db_mock_complex_debug.delete(ComplexModel, 1)

        assert "Executing SQL:" in caplog.text
        assert "DELETE FROM complex_model" in caplog.text

    def test_debug_output_table_names(self, caplog) -> None:
        """Test that table_names property produces debug log output."""
        db = SqliterDB(":memory:", debug=True)
        db.create_table(ComplexModel)

        with caplog.at_level(logging.DEBUG):
            _ = db.table_names

        assert "Executing SQL:" in caplog.text
        assert "sqlite_master" in caplog.text

    def test_setup_logger_else_clause(self, mocker) -> None:
        """Test the else clause configuration for the logger setup."""
        # Mock the root logger's hasHandlers BEFORE creating the instance
        mocker.patch.object(
            logging.getLogger(), "hasHandlers", return_value=False
        )

        # Now create the instance which will trigger _setup_logger
        instance = SqliterDB(":memory:", debug=True)

        # Verify the else clause configuration
        logger = instance.logger
        assert logger is not None

        assert logger.name == "sqliter"
        assert len(logger.handlers) == 1

        handler = logger.handlers[0]
        assert isinstance(handler, logging.StreamHandler)
        assert handler.formatter is not None
        assert handler.formatter._fmt == "%(levelname)-8s%(message)s"
        assert logger.level == logging.DEBUG
        assert logger.propagate is False

        logging.getLogger().hasHandlers.assert_called_once()

        # Cleanup - crucial to prevent test pollution
        for hdlr in logger.handlers[:]:
            logger.removeHandler(hdlr)
        logger.setLevel(logging.NOTSET)
        logger.propagate = True
