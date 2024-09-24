"""Define helper functions used in the library."""

from typing import Union

from sqliter.constants import SQLITE_TYPE_MAPPING


def infer_sqlite_type(field_type: Union[type, None]) -> str:
    """Infer the SQLite column type based on the Python/Pydantic type.

    Args:
        field_type: The type of the field (e.g., int, str, etc.)

    Returns:
        The corresponding SQLite type as a string (e.g., INTEGER, REAL, TEXT).
    """
    # If field_type is None, default to TEXT
    if field_type is None:
        return "TEXT"

    # Map the simplified type to an SQLite type
    return SQLITE_TYPE_MAPPING.get(field_type, "TEXT")
