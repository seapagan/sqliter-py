"""Utility functions for SQLiter internal operations.

This module provides helper functions used across the SQLiter library,
primarily for type inference and mapping between Python and SQLite
data types. These utilities support the core functionality of model
to database schema translation.
"""

from typing import Union

from sqliter.constants import SQLITE_TYPE_MAPPING


def infer_sqlite_type(field_type: Union[type, None]) -> str:
    """Infer the SQLite column type based on the Python type.

    This function maps Python types to their corresponding SQLite column
    types. It's used when creating database tables to ensure that the
    correct SQLite types are used for each field.

    Args:
        field_type: The Python type of the field, or None.

    Returns:
        A string representing the corresponding SQLite column type.

    Note:
        If the input type is None or not recognized, it defaults to 'TEXT'.
    """
    # If field_type is None, default to TEXT
    if field_type is None:
        return "TEXT"

    # Map the simplified type to an SQLite type
    return SQLITE_TYPE_MAPPING.get(field_type, "TEXT")
