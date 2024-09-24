"""Test the helper functions for the 'sqliter' package."""

from ctypes import Union

from sqliter.helpers import infer_sqlite_type


def test_infer_sqlite_type() -> None:
    """Test the 'infer_sqlite_type' function."""
    # Test with various Python types we know we support
    assert infer_sqlite_type(int) == "INTEGER"
    assert infer_sqlite_type(float) == "REAL"
    assert infer_sqlite_type(str) == "TEXT"
    assert infer_sqlite_type(bool) == "INTEGER"

    # Test with None
    assert infer_sqlite_type(None) == "TEXT"

    # Test with an unsupported type
    assert infer_sqlite_type(list) == "TEXT"
    assert infer_sqlite_type(dict) == "TEXT"
    assert infer_sqlite_type(tuple) == "TEXT"
    assert infer_sqlite_type(set) == "TEXT"
    assert infer_sqlite_type(Union) == "TEXT"
