"""ORM model with lazy loading and reverse relationships."""

from __future__ import annotations

from typing import Any, ClassVar, Optional

from pydantic import Field

from sqliter.model.model import BaseDBModel as _BaseDBModel
from sqliter.orm.fields import ForeignKeyDescriptor, LazyLoader
from sqliter.orm.registry import ModelRegistry

__all__ = ["BaseDBModel"]


class BaseDBModel(_BaseDBModel):
    """Extends BaseDBModel with ORM features.

    Adds:
    - Lazy loading of foreign key relationships
    - Automatic reverse relationship setup
    - db_context for query execution
    """

    # Store FK descriptors per class (not inherited)
    fk_descriptors: ClassVar[dict[str, ForeignKeyDescriptor]] = {}

    # Database context for lazy loading and reverse queries
    # Using Any since SqliterDB would cause circular import issues with Pydantic
    db_context: Optional[Any] = Field(default=None, exclude=True)

    def __init__(self, **kwargs: Any) -> None:  # noqa: ANN401
        """Initialize model, converting FK fields to _id fields."""
        # Convert FK field values to _id fields before validation
        for fk_field in self.fk_descriptors:
            if fk_field in kwargs:
                value = kwargs[fk_field]
                if isinstance(value, _BaseDBModel):
                    # Extract pk from model instance
                    kwargs[f"{fk_field}_id"] = value.pk
                    del kwargs[fk_field]
                elif isinstance(value, int):
                    # Already an ID, just move to _id field
                    kwargs[f"{fk_field}_id"] = value
                    del kwargs[fk_field]
                elif value is None:
                    # Keep None for nullable FKs
                    kwargs[f"{fk_field}_id"] = None
                    del kwargs[fk_field]

        super().__init__(**kwargs)

    def __getattribute__(self, name: str) -> object:
        """Intercept FK field access to provide lazy loading."""
        # Check if this is a FK field
        if name in object.__getattribute__(self, "fk_descriptors"):
            # Get the descriptor
            descriptor = object.__getattribute__(self, "fk_descriptors")[name]
            # Get FK ID
            fk_id = object.__getattribute__(self, f"{name}_id")
            # Get db_context
            db_context = object.__getattribute__(self, "db_context")
            # Return LazyLoader
            return LazyLoader(
                instance=self,
                to_model=descriptor.to_model,
                fk_id=fk_id,
                db_context=db_context,
            )
        # For non-FK fields, use normal attribute access
        return object.__getattribute__(self, name)

    def __init_subclass__(cls, **kwargs: Any) -> None:  # noqa: ANN401
        """Set up ORM-specific features for subclasses."""
        # Call parent __init_subclass__ FIRST
        super().__init_subclass__(**kwargs)

        # Collect FK descriptors from class dict
        if "fk_descriptors" not in cls.__dict__:
            cls.fk_descriptors = {}

        # Find all ForeignKeyDescriptors in the class
        for name, value in cls.__dict__.items():
            if isinstance(value, ForeignKeyDescriptor):
                cls.fk_descriptors[name] = value

        # Process FK descriptors - add _id fields, register FKs
        cls._setup_orm_fields()

        # Register model in global registry
        ModelRegistry.register_model(cls)

    @classmethod
    def _setup_orm_fields(cls) -> None:
        """Create _id fields and register FK relationships.

        Called during class creation to:
        1. Add _id fields for each FK descriptor
        2. Register FK relationships in ModelRegistry
        3. Set descriptor as class attribute (not as model field)
        """
        # Get FK descriptors for this class
        fk_descriptors_copy = cls.fk_descriptors.copy()

        for field_name in fk_descriptors_copy:
            descriptor = cls.fk_descriptors[field_name]

            # Create _id field name
            id_field_name = f"{field_name}_id"

            # Get ForeignKeyInfo from descriptor
            fk_info = descriptor.fk_info

            # Add _id field to model if not already present
            if id_field_name not in cls.model_fields:
                # Create the field with proper type and constraints
                default_value: Any = None if fk_info.null else ...
                id_field = Field(
                    default=default_value,
                    description=(f"Foreign key to {fk_info.to_model.__name__}"),
                )

                # Add to model_fields
                cls.model_fields[id_field_name] = id_field

                # Add to annotations if not present
                if not hasattr(cls, "__annotations__"):
                    cls.__annotations__ = {}
                if id_field_name not in cls.__annotations__:
                    cls.__annotations__[id_field_name] = Optional[int]

            # Register FK relationship
            ModelRegistry.register_foreign_key(
                from_model=cls,
                to_model=fk_info.to_model,
                fk_field=field_name,
                on_delete=fk_info.on_delete,
                related_name=descriptor.related_name,
            )

            # Remove descriptor from model_fields so Pydantic doesn't
            # validate it
            if field_name in cls.model_fields:
                del cls.model_fields[field_name]
