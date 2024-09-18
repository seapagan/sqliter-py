"""Define the Base model class."""

from __future__ import annotations

from typing import Any, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T", bound="BaseDBModel")


class BaseDBModel(BaseModel):
    """Custom base model for database models."""

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        validate_assignment=False,
        from_attributes=True,
    )

    class Meta:
        """Configure the base model with default options."""

        create_id: bool = True  # Whether to create an auto-increment ID
        primary_key: str = "id"  # Default primary key field
        table_name: Optional[str] = (
            None  # Table name, defaults to class name if not set
        )

    @classmethod
    def model_validate_partial(cls: type[T], obj: dict[str, Any]) -> T:
        """Validate a partial model object.

        This would be in the case that we are only returning a subset of the
        fields.
        """
        return cls.model_validate(obj, strict=False)

    @classmethod
    def get_table_name(cls) -> str:
        """Get the table name from the Meta, or default to the classname."""
        table_name: str | None = getattr(cls.Meta, "table_name", None)
        if table_name is not None:
            return table_name
        return cls.__name__.lower()  # Default to class name in lowercase

    @classmethod
    def get_primary_key(cls) -> str:
        """Get the primary key from the Meta class or default to 'id'."""
        return getattr(cls.Meta, "primary_key", "id")

    @classmethod
    def should_create_id(cls) -> bool:
        """Check whether the model should create an auto-increment ID."""
        return getattr(cls.Meta, "create_id", True)
