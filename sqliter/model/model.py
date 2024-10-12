"""Defines the base model class for SQLiter ORM functionality.

This module provides the BaseDBModel class, which extends Pydantic's
BaseModel to add SQLiter-specific functionality. It includes methods
for table name inference, primary key management, and partial model
validation, forming the foundation for defining database-mapped models
in SQLiter applications.
"""

from __future__ import annotations

import re
from typing import (
    Any,
    ClassVar,
    Optional,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
)

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T", bound="BaseDBModel")


class BaseDBModel(BaseModel):
    """Base model class for SQLiter database models.

    This class extends Pydantic's BaseModel to provide additional functionality
    for database operations. It includes configuration options and methods
    specific to SQLiter's ORM-like functionality.

    This should not be used directly, but should be inherited by subclasses
    representing database models.
    """

    pk: int = Field(0, description="The mandatory primary key of the table.")

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        validate_assignment=False,
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
    def model_validate_partial(cls: type[T], obj: dict[str, Any]) -> T:
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

        return cast(T, cls.model_construct(**converted_obj))

    @classmethod
    def get_table_name(cls) -> str:
        """Get the database table name for the model.

        This method determines the table name based on the Meta configuration
        or derives it from the class name if not explicitly set.

        Returns:
            The name of the database table for this model.
        """
        table_name: str | None = getattr(cls.Meta, "table_name", None)
        if table_name is not None:
            return table_name

        # Get class name and remove 'Model' suffix if present
        class_name = cls.__name__.removesuffix("Model")

        # Convert to snake_case
        snake_case_name = re.sub(r"(?<!^)(?=[A-Z])", "_", class_name).lower()

        # Pluralize the table name
        try:
            import inflect

            p = inflect.engine()
            return p.plural(snake_case_name)
        except ImportError:
            # Fallback to simple pluralization by adding 's'
            return (
                snake_case_name
                if snake_case_name.endswith("s")
                else snake_case_name + "s"
            )

    @classmethod
    def get_primary_key(cls) -> str:
        """Returns the mandatory primary key, always 'pk'."""
        return "pk"

    @classmethod
    def should_create_pk(cls) -> bool:
        """Returns True since the primary key is always created."""
        return True
