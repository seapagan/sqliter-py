"""Custom exception classes for SQLiter error handling.

This module defines a hierarchy of exception classes specific to
SQLiter operations. These exceptions provide detailed error information
for various scenarios such as connection issues, invalid queries,
and CRUD operation failures, enabling more precise error handling
in applications using SQLiter.
"""

import os
import sys
import traceback


class SqliterError(Exception):
    """Base exception class for all SQLiter-specific errors.

    This class serves as the parent for all custom exceptions in SQLiter,
    providing a consistent interface and message formatting.

    Attributes:
        message_template (str): A template string for the error message.
        original_exception (Exception): The original exception that was caught.
    """

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
    """Exception raised when a database connection cannot be established."""

    message_template = "Failed to connect to the database: '{}'"


class InvalidOffsetError(SqliterError):
    """Exception raised when an invalid offset value is provided."""

    message_template = (
        "Invalid offset value: '{}'. Offset must be a positive integer."
    )


class InvalidOrderError(SqliterError):
    """Exception raised when an invalid order specification is provided."""

    message_template = "Invalid order value - {}"


class TableCreationError(SqliterError):
    """Exception raised when a table cannot be created in the database."""

    message_template = "Failed to create the table: '{}'"


class RecordInsertionError(SqliterError):
    """Exception raised when a record cannot be inserted into the database."""

    message_template = "Failed to insert record into table: '{}'"


class RecordUpdateError(SqliterError):
    """Exception raised when a record cannot be updated in the database."""

    message_template = "Failed to update record in table: '{}'"


class RecordNotFoundError(SqliterError):
    """Exception raised when a requested record is not found in the database."""

    message_template = "Failed to find that record in the table (key '{}') "


class RecordFetchError(SqliterError):
    """Exception raised on an error fetching records from the database."""

    message_template = "Failed to fetch record from table: '{}'"


class RecordDeletionError(SqliterError):
    """Exception raised when a record cannot be deleted from the database."""

    message_template = "Failed to delete record from table: '{}'"


class InvalidFilterError(SqliterError):
    """Exception raised when an invalid filter is applied to a query."""

    message_template = "Failed to apply filter: invalid field '{}'"


class TableDeletionError(SqliterError):
    """Raised when a table cannot be deleted from the database."""

    message_template = "Failed to delete the table: '{}'"


class SqlExecutionError(SqliterError):
    """Raised when an SQL execution fails."""

    message_template = "Failed to execute SQL: '{}'"


class InvalidIndexError(SqliterError):
    """Exception raised when an invalid index field is specified.

    This error is triggered if one or more fields specified for an index
    do not exist in the model's fields.

    Attributes:
        invalid_fields (list[str]): The list of fields that were invalid.
        model_class (str): The name of the model where the error occurred.
    """

    message_template = "Invalid fields for indexing in model '{}': {}"

    def __init__(self, invalid_fields: list[str], model_class: str) -> None:
        """Tidy up the error message by joining the invalid fields."""
        # Join invalid fields into a comma-separated string
        invalid_fields_str = ", ".join(invalid_fields)
        # Pass the formatted message to the parent class
        super().__init__(model_class, invalid_fields_str)


class ForeignKeyError(SqliterError):
    """Base exception for foreign key related errors."""

    message_template = "Foreign key error: {}"


class ForeignKeyConstraintError(ForeignKeyError):
    """Raised when a foreign key constraint is violated.

    This error occurs when attempting to insert/update a record with a
    foreign key value that doesn't exist in the referenced table, or
    when attempting to delete a record that is still referenced.
    """

    message_template = (
        "Foreign key constraint violation: Cannot {} record - "
        "referenced record {}"
    )


class InvalidForeignKeyError(ForeignKeyError):
    """Raised when an invalid foreign key configuration is detected.

    This error occurs when defining a foreign key with invalid parameters,
    such as using SET NULL without null=True.
    """

    message_template = "Invalid foreign key configuration: {}"


class InvalidRelationshipError(SqliterError):
    """Raised when an invalid relationship path is specified.

    This error occurs when using select_related() or relationship filter
    traversal with a non-existent relationship field or invalid path.
    """

    message_template = (
        "Invalid relationship path '{}': field '{}' is not a valid "
        "foreign key relationship on model {}"
    )
