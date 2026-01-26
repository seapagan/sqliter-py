"""Defines the base model class for SQLiter ORM functionality.

This module provides the BaseDBModel class, which extends Pydantic's
BaseModel to add SQLiter-specific functionality. It includes methods
for table name inference, primary key management, and partial model
validation, forming the foundation for defining database-mapped models
in SQLiter applications.
"""

from __future__ import annotations

import datetime
import pickle
import re
from typing import (
    Any,
    ClassVar,
    Optional,
    Protocol,
    Union,
    cast,
    get_args,
    get_origin,
)

from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import Self

from sqliter.helpers import from_unix_timestamp, to_unix_timestamp


class SerializableField(Protocol):
    """Protocol for fields that can be serialized or deserialized."""


class BaseDBModel(BaseModel):
    """Base model class for SQLiter database models.

    This class extends Pydantic's BaseModel to provide additional functionality
    for database operations. It includes configuration options and methods
    specific to SQLiter's ORM-like functionality.

    This should not be used directly, but should be inherited by subclasses
    representing database models.
    """

    pk: int = Field(0, description="The mandatory primary key of the table.")
    created_at: int = Field(
        default=0,
        description="Unix timestamp when the record was created.",
    )
    updated_at: int = Field(
        default=0,
        description="Unix timestamp when the record was last updated.",
    )

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        validate_assignment=True,
        from_attributes=True,
    )

    class Meta:
        """Metadata class for configuring database-specific attributes.

        Attributes:
            table_name (Optional[str]): The name of the database table. If not
                specified, the table name will be inferred from the model class
                name and converted to snake_case.
            indexes (ClassVar[list[Union[str, tuple[str]]]]): A list of fields
                or tuples of fields for which regular (non-unique) indexes
                should be created. Indexes improve query performance on these
                fields.
            unique_indexes (ClassVar[list[Union[str, tuple[str]]]]): A list of
                fields or tuples of fields for which unique indexes should be
                created. Unique indexes enforce that all values in these fields
                are distinct across the table.
        """

        table_name: Optional[str] = (
            None  # Table name, defaults to class name if not set
        )
        indexes: ClassVar[list[Union[str, tuple[str]]]] = []
        unique_indexes: ClassVar[list[Union[str, tuple[str]]]] = []

    @classmethod
    def model_validate_partial(cls, obj: dict[str, Any]) -> Self:
        """Validate and create a model instance from partial data.

        This method allows for the creation of a model instance even when
        not all fields are present in the input data.

        Args:
            obj: A dictionary of field names and values.

        Returns:
            An instance of the model class with the provided data.
        """
        converted_obj: dict[str, Any] = {}
        for field_name, value in obj.items():
            field = cls.model_fields[field_name]
            field_type: Optional[type] = field.annotation
            if (
                field_type is None or value is None
            ):  # Direct check for None values here
                converted_obj[field_name] = None
            else:
                origin = get_origin(field_type)
                if origin is Union:
                    args = get_args(field_type)
                    for arg in args:
                        try:
                            # Try converting the value to the type
                            converted_obj[field_name] = arg(value)
                            break
                        except (ValueError, TypeError):
                            pass
                    else:
                        converted_obj[field_name] = value
                else:
                    converted_obj[field_name] = field_type(value)

        return cast("Self", cls.model_construct(**converted_obj))

    @staticmethod
    def _validate_table_name(table_name: str) -> str:
        """Validate that a table name contains only safe characters.

        Table names must contain only alphanumeric characters and underscores,
        and must start with a letter or underscore. This prevents SQL injection
        through malicious table names.

        Args:
            table_name: The table name to validate.

        Returns:
            The validated table name.

        Raises:
            ValueError: If the table name contains invalid characters.
        """
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", table_name):
            msg = (
                f"Invalid table name '{table_name}'. "
                "Table names must start with a letter or underscore and "
                "contain only letters, numbers, and underscores."
            )
            raise ValueError(msg)
        return table_name

    @classmethod
    def get_table_name(cls) -> str:
        """Get the database table name for the model.

        This method determines the table name based on the Meta configuration
        or derives it from the class name if not explicitly set.

        When deriving the table name automatically, the class name is converted
        to snake_case and pluralized. If the `inflect` library is installed,
        it provides grammatically correct pluralization (e.g., "person" becomes
        "people", "category" becomes "categories"). Otherwise, a simple "s"
        suffix is added if the name doesn't already end in "s".

        Returns:
            The name of the database table for this model.

        Raises:
            ValueError: If the table name contains invalid characters.
        """
        table_name: str | None = getattr(cls.Meta, "table_name", None)
        if table_name is not None:
            # Validate custom table names
            return cls._validate_table_name(table_name)

        # Get class name and remove 'Model' suffix if present
        class_name = cls.__name__.removesuffix("Model")

        # Convert to snake_case
        snake_case_name = re.sub(r"(?<!^)(?=[A-Z])", "_", class_name).lower()

        # Pluralize the table name
        try:
            import inflect  # noqa: PLC0415

            p = inflect.engine()
            table_name = p.plural(snake_case_name)
        except ImportError:
            # Fallback to simple pluralization by adding 's'
            table_name = (
                snake_case_name
                if snake_case_name.endswith("s")
                else snake_case_name + "s"
            )

        # Validate auto-generated table names (should always pass)
        return cls._validate_table_name(table_name)

    @classmethod
    def get_primary_key(cls) -> str:
        """Returns the mandatory primary key, always 'pk'."""
        return "pk"

    @classmethod
    def should_create_pk(cls) -> bool:
        """Returns True since the primary key is always created."""
        return True

    @classmethod
    def serialize_field(cls, value: SerializableField) -> SerializableField:
        """Serialize datetime or date fields to Unix timestamp.

        Args:
            field_name: The name of the field.
            value: The value of the field.

        Returns:
            An integer Unix timestamp if the field is a datetime or date.
        """
        if isinstance(value, (datetime.datetime, datetime.date)):
            return to_unix_timestamp(value)
        if isinstance(value, (list, dict, set, tuple)):
            return pickle.dumps(value)
        return value  # Return value as-is for other fields

    # Deserialization after fetching from the database

    @classmethod
    def deserialize_field(
        cls,
        field_name: str,
        value: SerializableField,
        *,
        return_local_time: bool,
    ) -> object:
        """Deserialize fields from Unix timestamp to datetime or date.

        Args:
            field_name: The name of the field being deserialized.
            value: The Unix timestamp value fetched from the database.
            return_local_time: Flag to control whether the datetime is localized
                to the user's timezone.

        Returns:
            A datetime or date object if the field type is datetime or date,
            otherwise returns the value as-is.
        """
        if value is None:
            return None

        # Get field type if it exists in model_fields
        field_info = cls.model_fields.get(field_name)
        if field_info is None:
            # If field doesn't exist in model, return value as-is
            return value

        field_type = field_info.annotation

        if (
            isinstance(field_type, type)
            and issubclass(field_type, (datetime.datetime, datetime.date))
            and isinstance(value, int)
        ):
            return from_unix_timestamp(
                value, field_type, localize=return_local_time
            )

        origin_type = get_origin(field_type) or field_type
        if origin_type in (list, dict, set, tuple) and isinstance(value, bytes):
            try:
                return pickle.loads(value)
            except pickle.UnpicklingError:
                return value

        return value
