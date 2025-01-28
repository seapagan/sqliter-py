"""Test the helper functions for the 'sqliter' package."""

from ctypes import Union

from sqliter.helpers import infer_sqlite_type


class TestHelpers:
    """Test the helper functions for the 'sqliter' package."""

    def test_infer_sqlite_type(self) -> None:
        """Test the 'infer_sqlite_type' function."""
        # Test with various Python types we know we support
        assert infer_sqlite_type(int) == "INTEGER"
        assert infer_sqlite_type(float) == "REAL"
        assert infer_sqlite_type(str) == "TEXT"
        assert infer_sqlite_type(bool) == "INTEGER"

        # Test with None
        assert infer_sqlite_type(None) == "TEXT"

        # test with collection types
        assert infer_sqlite_type(list) == "BLOB"
        assert infer_sqlite_type(dict) == "BLOB"
        assert infer_sqlite_type(tuple) == "BLOB"
        assert infer_sqlite_type(set) == "BLOB"

        # Test with an unsupported type
        assert infer_sqlite_type(Union) == "TEXT"
