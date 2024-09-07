"""Define the Base model class."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class BaseDBModel(BaseModel):
    """Custom base model for database models."""

    class Meta:
        """Configure the base model with default options."""

        create_id: bool = True  # Whether to create an auto-increment ID
        primary_key: str = "id"  # Default primary key field
        table_name: Optional[str] = (
            None  # Table name, defaults to class name if not set
        )

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
