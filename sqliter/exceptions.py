"""Define custom exceptions for the sqliter package."""


class SqliterError(Exception):
    """Base class for all exceptions raised by the sqliter package."""

    message_template: str = "An error occurred in the SQLiter package."

    def __init__(self, *args: object) -> None:
        """Format the message using the provided arguments."""
        if args:
            message = self.message_template.format(*args)
        else:
            message = (
                self.message_template.replace("'{}'", "")
                .replace(":", "")
                .strip()
            )
        super().__init__(message)


class DatabaseConnectionError(SqliterError):
    """Raised when the SQLite database connection fails."""

    message_template = "Failed to connect to the database: '{}'"


class InvalidOffsetError(SqliterError):
    """Raised when an invalid offset value (0 or negative) is used."""

    message_template = (
        "Invalid offset value: '{}'. Offset must be a positive integer."
    )
