"""Testd the debug logging for the SqliterDB class."""

import pytest

from sqliter.sqliter import SqliterDB
from tests.conftest import ComplexModel


def test_sqliterdb_debug_default() -> None:
    """Test that the default value for the debug flag is False."""
    db = SqliterDB(":memory:")  # No debug argument passed
    assert db.debug is False, "The debug flag should be False by default."


def test_sqliterdb_debug_set_false() -> None:
    """Test that the default value for the debug flag is False."""
    db = SqliterDB(":memory:", debug=False)  # Set debug argument to False
    assert (
        db.debug is False
    ), "The debug flag should be False when explicitly passed as False."


def test_sqliterdb_debug_set_true() -> None:
    """Test that the debug flag can be set to True."""
    db = SqliterDB(":memory:", debug=True)  # Set debug argument to True
    assert (
        db.debug is True
    ), "The debug flag should be True when explicitly passed as True."


@pytest.fixture
def db_mock_complex_debug() -> SqliterDB:
    """Return a memory-based db with debug=True using ComplexModel."""
    db = SqliterDB(":memory:", debug=True)
    db.create_table(ComplexModel)
    db.insert(
        ComplexModel(
            id=1,
            name="Alice",
            age=30.5,
            is_active=True,
            score=85,
            nullable_field="Not null",
        )
    )
    db.insert(
        ComplexModel(
            id=2,
            name="Bob",
            age=25.0,
            is_active=False,
            score=90.5,
            nullable_field=None,
        )
    )
    db.insert(
        ComplexModel(
            id=3,
            name="Charlie",
            age=35.0,
            is_active=True,
            score=95.0,
            nullable_field=None,
        )
    )
    return db


def test_debug_sql_output_basic_query(
    db_mock_complex_debug: SqliterDB, capsys
) -> None:
    """Test that the debug output correctly prints the SQL query and values."""
    db_mock_complex_debug.select(ComplexModel).filter(age=30.5).fetch_all()

    # Capture the output
    captured = capsys.readouterr()

    # Assert the SQL query was printed
    assert (
        'Executing SQL: SELECT "id", "name", "age", "is_active", "score", '
        '"nullable_field" FROM "complex_model" WHERE age = 30.5' in captured.out
    )


def test_debug_sql_output_string_values(
    db_mock_complex_debug: SqliterDB, capsys
) -> None:
    """Test that the debug output correctly handles string values."""
    db_mock_complex_debug.select(ComplexModel).filter(name="Alice").fetch_all()

    # Capture the output
    captured = capsys.readouterr()

    # Assert the SQL query was printed with the string properly quoted
    assert (
        'Executing SQL: SELECT "id", "name", "age", "is_active", "score", '
        '"nullable_field" FROM "complex_model" WHERE name = \'Alice\''
        in captured.out
    )


def test_debug_sql_output_multiple_conditions(
    db_mock_complex_debug: SqliterDB, capsys
) -> None:
    """Test that the debug output works with multiple conditions."""
    db_mock_complex_debug.select(ComplexModel).filter(
        name="Alice", age=30.5
    ).fetch_all()

    # Capture the output
    captured = capsys.readouterr()

    # Assert the SQL query was printed with multiple conditions
    assert (
        'Executing SQL: SELECT "id", "name", "age", "is_active", "score", '
        '"nullable_field" FROM "complex_model" WHERE name = \'Alice\' AND '
        "age = 30.5" in captured.out
    )


def test_debug_sql_output_order_and_limit(
    db_mock_complex_debug: SqliterDB, capsys
) -> None:
    """Test that the debug output works with order and limit."""
    db_mock_complex_debug.select(ComplexModel).order("age", reverse=True).limit(
        1
    ).fetch_all()

    # Capture the output
    captured = capsys.readouterr()

    # Assert the SQL query was printed with ORDER and LIMIT
    assert (
        'Executing SQL: SELECT "id", "name", "age", "is_active", "score", '
        '"nullable_field" FROM "complex_model" ORDER BY "age" DESC LIMIT 1'
        in captured.out
    )


def test_debug_sql_output_with_null_value(
    db_mock_complex_debug: SqliterDB, capsys
) -> None:
    """Test that the debug output works when filtering on a NULL value."""
    db_mock_complex_debug.insert(
        ComplexModel(
            id=4,
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

    # Capture the output
    captured = capsys.readouterr()

    # Assert the SQL query was printed with IS NULL
    assert (
        'Executing SQL: SELECT "id", "name", "age", "is_active", "score", '
        '"nullable_field" FROM "complex_model" WHERE age IS NULL'
        in captured.out
    )


def test_debug_sql_output_with_fields_single(
    db_mock_complex_debug: SqliterDB, capsys
) -> None:
    """Test debug output correct when selecting a single field."""
    db_mock_complex_debug.select(ComplexModel).fields(["name"]).fetch_all()

    # Capture the output
    captured = capsys.readouterr()

    # Assert the SQL query only selects the 'name' field
    assert 'Executing SQL: SELECT "name" FROM "complex_model"' in captured.out


def test_debug_sql_output_with_fields_multiple(
    db_mock_complex_debug: SqliterDB, capsys
) -> None:
    """Test that the debug output correct when selecting multiple fields."""
    db_mock_complex_debug.select(ComplexModel).fields(
        ["name", "age"]
    ).fetch_all()

    # Capture the output
    captured = capsys.readouterr()

    # Assert the SQL query only selects the 'name' and 'age' fields
    assert (
        'Executing SQL: SELECT "name", "age" FROM "complex_model"'
        in captured.out
    )


def test_debug_sql_output_with_fields_and_filter(
    db_mock_complex_debug: SqliterDB, capsys
) -> None:
    """Test that the debug output correctlwith selected fields and a filter."""
    db_mock_complex_debug.select(ComplexModel).fields(["name", "score"]).filter(
        score__gt=85
    ).fetch_all()

    # Capture the output
    captured = capsys.readouterr()

    # Assert the SQL query selects 'name' and 'score' and applies the filter
    assert (
        'Executing SQL: SELECT "name", "score" FROM "complex_model" '
        "WHERE score > 85" in captured.out
    )
