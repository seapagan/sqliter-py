"""Utility functions for SQLiter internal operations.

This module provides helper functions used across the SQLiter library,
primarily for type inference and mapping between Python and SQLite
data types. These utilities support the core functionality of model
to database schema translation.
"""

from __future__ import annotations

import datetime
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


def to_unix_timestamp(value: datetime.date | datetime.datetime) -> int:
    """Convert datetime or date to a Unix timestamp in UTC.

    Args:
        value: The datetime or date object to convert.

    Returns:
        An integer Unix timestamp.

    Raises:
        TypeError: If the value is not a datetime or date object.
    """
    if isinstance(value, datetime.datetime):
        # If no timezone is provided, assume local time and convert to UTC
        if value.tzinfo is None:
            value = value.astimezone()  # Convert to user's local timezone
        # Convert to UTC before storing
        value = value.astimezone(datetime.timezone.utc)
        return int(value.timestamp())
    if isinstance(value, datetime.date):
        # Convert date to datetime at midnight in UTC
        dt = datetime.datetime.combine(
            value, datetime.time(0, 0), tzinfo=datetime.timezone.utc
        )
        return int(dt.timestamp())

    err_msg = "Expected datetime or date object."
    raise TypeError(err_msg)


def from_unix_timestamp(
    value: int, to_type: type, *, localize: bool = True
) -> datetime.date | datetime.datetime:
    """Convert a Unix timestamp to datetime or date, optionally to local time.

    Args:
        value: The Unix timestamp as an integer.
        to_type: The expected output type, either datetime or date.
        localize: If True, convert the datetime to the user's local timezone.

    Returns:
        The corresponding datetime or date object.

    Raises:
        TypeError: If to_type is not datetime or date.
    """
    if to_type is datetime.datetime:
        # Convert the Unix timestamp to UTC datetime
        dt = datetime.datetime.fromtimestamp(value, tz=datetime.timezone.utc)
        # Convert to local time if requested
        return dt.astimezone() if localize else dt
    if to_type is datetime.date:
        # Convert to UTC datetime first
        dt = datetime.datetime.fromtimestamp(value, tz=datetime.timezone.utc)
        # Convert to local time if requested, then return the date part
        dt_local = dt.astimezone() if localize else dt
        return dt_local.date()  # Extract the date part

    err_msg = "Expected datetime or date type."
    raise TypeError(err_msg)
