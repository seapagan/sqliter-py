"""Define custom exceptions for the sqliter package."""

import os
import sys
import traceback


class SqliterError(Exception):
    """Base class for all exceptions raised by the sqliter package."""

    message_template: str = "An error occurred in the SQLiter package."

    def __init__(self, *args: object) -> None:
        """Format the message using the provided arguments.

        We also capture (and display) the current exception context and chain
        any previous exceptions.

        :param args: Arguments to format into the message template
        """
        if args:
            message = self.message_template.format(*args)
        else:
            message = (
                self.message_template.replace("'{}'", "")
                .replace(":", "")
                .strip()
            )

        # Capture the current exception context
        self.original_exception = sys.exc_info()[1]

        # If there's an active exception, append its information to our message
        if self.original_exception:
            original_type = type(self.original_exception).__name__
            original_module = type(self.original_exception).__module__

            # Get the traceback of the original exception
            tb = traceback.extract_tb(self.original_exception.__traceback__)
            if tb:
                last_frame = tb[-1]
                file_path = os.path.relpath(last_frame.filename)
                line_number = last_frame.lineno
                location = f"{file_path}:{line_number}"
            else:
                location = "unknown location"

            message += (
                f"\n  --> {original_module}.{original_type} "
                f"from {location}: {self.original_exception}"
            )

        # Call the parent constructor with our formatted message
        super().__init__(message)

        # Explicitly chain exceptions if there's an active one
        if self.original_exception:
            self.__cause__ = self.original_exception


class DatabaseConnectionError(SqliterError):
    """Raised when the SQLite database connection fails."""

    message_template = "Failed to connect to the database: '{}'"


class InvalidOffsetError(SqliterError):
    """Raised when an invalid offset value (0 or negative) is used."""

    message_template = (
        "Invalid offset value: '{}'. Offset must be a positive integer."
    )


class InvalidOrderError(SqliterError):
    """Raised when an invalid order value is used."""

    message_template = "Invalid order value - {}"


class TableCreationError(SqliterError):
    """Raised when a table cannot be created in the database."""

    message_template = "Failed to create the table: '{}'"


class RecordInsertionError(SqliterError):
    """Raised when an error occurs during record insertion."""

    message_template = "Failed to insert record into table: '{}'"


class RecordUpdateError(SqliterError):
    """Raised when an error occurs during record update."""

    message_template = "Failed to update record in table: '{}'"


class RecordNotFoundError(SqliterError):
    """Raised when a record with the specified primary key is not found."""

    message_template = "Failed to find a record for key '{}' "


class RecordFetchError(SqliterError):
    """Raised when an error occurs during record fetching."""

    message_template = "Failed to fetch record from table: '{}'"


class RecordDeletionError(SqliterError):
    """Raised when an error occurs during record deletion."""

    message_template = "Failed to delete record from table: '{}'"


class InvalidFilterError(SqliterError):
    """Raised when an invalid filter field is used in a query."""

    message_template = "Failed to apply filter: invalid field '{}'"
