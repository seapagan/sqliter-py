"""Define custom exceptions for the sqliter package."""


class SqliterError(Exception):
    """Base class for all exceptions raised by the sqliter package."""


class InvalidOffsetError(SqliterError):
    """Raised when an invalid offset value (0 or negative) is used."""

    def __init__(self, offset_value: int) -> None:
        """Pass the message up to the base Exception."""
        super().__init__(
            f"Invalid offset value: {offset_value}. "
            "Offset must be a positive integer."
        )


# In sqliter/exceptions.py
class DatabaseConnectionError(SqliterError):
    """Raised when the SQLite database connection fails."""

    def __init__(self, db_filename: str) -> None:
        """Pass a custom error message to the base Exception."""
        super().__init__(f"Failed to connect to the database: {db_filename}")
