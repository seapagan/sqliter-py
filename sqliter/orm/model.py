"""ORM model with lazy loading and reverse relationships."""

from __future__ import annotations

from typing import Any, ClassVar, Optional

from pydantic import Field

from sqliter.model.model import BaseDBModel as _BaseDBModel
from sqliter.orm.fields import ForeignKey, HasPK, LazyLoader
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
    fk_descriptors: ClassVar[dict[str, ForeignKey[Any]]] = {}

    # Database context for lazy loading and reverse queries
    # Using Any since SqliterDB would cause circular import issues with Pydantic
    db_context: Optional[Any] = Field(default=None, exclude=True)

    def __init__(self, **kwargs: Any) -> None:  # noqa: ANN401
        """Initialize model, converting FK fields to _id fields."""
        # Convert FK field values to _id fields before validation
        for fk_field in self.fk_descriptors:
            if fk_field in kwargs:
                value = kwargs[fk_field]
                if isinstance(value, HasPK):
                    # Duck typing via Protocol: extract pk from model
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

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:  # noqa: ANN401
        """Dump model, excluding FK descriptor fields.

        FK descriptor fields (like 'author') are excluded from serialization.
        Only the _id fields (like 'author_id') are included.
        """
        data = super().model_dump(**kwargs)
        # Remove FK descriptor fields from the dump
        for fk_field in self.fk_descriptors:
            data.pop(fk_field, None)
        return data

    def __getattribute__(self, name: str) -> object:
        """Intercept FK field access to provide lazy loading."""
        # Check if this is a FK field
        if name in object.__getattribute__(self, "fk_descriptors"):
            # Get FK ID
            fk_id = object.__getattribute__(self, f"{name}_id")

            # Null FK returns None directly (standard ORM behavior)
            if fk_id is None:
                return None

            # Check instance cache for identity (same object on repeated access)
            instance_dict = object.__getattribute__(self, "__dict__")
            cache = instance_dict.setdefault("_fk_cache", {})
            db_context = object.__getattribute__(self, "db_context")

            # Check if we need to create or refresh the cached loader
            cached_loader = cache.get(name)
            needs_refresh = cached_loader is None or (
                cached_loader.db_context is None and db_context is not None
            )

            if needs_refresh:
                # Get the descriptor and create LazyLoader
                fk_descs = object.__getattribute__(self, "fk_descriptors")
                descriptor = fk_descs[name]
                cache[name] = LazyLoader(
                    instance=self,
                    to_model=descriptor.to_model,
                    fk_id=fk_id,
                    db_context=db_context,
                )
            return cache[name]
        # For non-FK fields, use normal attribute access
        return object.__getattribute__(self, name)

    def __setattr__(self, name: str, value: object) -> None:
        """Intercept FK field assignment to convert to _id field."""
        # Check if this is a FK field assignment
        fk_descs = getattr(self, "fk_descriptors", {})
        if name in fk_descs:
            # Convert FK assignment to _id field assignment
            # This bypasses Pydantic's validation for the FK field (which is
            # not in model_fields) and uses the _id field instead
            id_field_name = f"{name}_id"
            if value is None:
                setattr(self, id_field_name, None)
            elif isinstance(value, int):
                setattr(self, id_field_name, value)
            elif isinstance(value, HasPK):
                setattr(self, id_field_name, value.pk)
            else:
                msg = (
                    f"FK value must be BaseModel, int, or None, "
                    f"got {type(value)}"
                )
                raise TypeError(msg)
            return

        # If setting an _id field, clear corresponding FK cache
        if name.endswith("_id"):
            fk_name = name[:-3]  # Remove "_id" suffix
            if fk_name in fk_descs:
                cache = self.__dict__.get("_fk_cache")
                if cache and fk_name in cache:
                    del cache[fk_name]
        super().__setattr__(name, value)

    def __init_subclass__(cls, **kwargs: Any) -> None:  # noqa: ANN401
        """Set up ORM field annotations before Pydantic processes the class.

        This runs BEFORE Pydantic populates model_fields, so we add the _id
        field annotations here so Pydantic creates proper FieldInfo for them.
        """
        # Call parent __init_subclass__ FIRST
        super().__init_subclass__(**kwargs)

        # Collect FK descriptors from class dict
        if "fk_descriptors" not in cls.__dict__:
            cls.fk_descriptors = {}

        # Find all ForeignKeys in the class and add _id field annotations
        # Make a copy of items to avoid modifying dict during iteration
        class_items = list(cls.__dict__.items())
        for name, value in class_items:
            if isinstance(value, ForeignKey):
                cls.fk_descriptors[name] = value
                # Add _id field annotation so Pydantic creates a field for it
                id_field_name = f"{name}_id"
                if id_field_name not in cls.__annotations__:
                    if value.fk_info.null:
                        cls.__annotations__[id_field_name] = Optional[int]
                        # Nullable FKs default to None so they can be omitted
                        setattr(cls, id_field_name, None)
                    else:
                        cls.__annotations__[id_field_name] = int

                # Remove FK field annotation so Pydantic doesn't treat it as
                # a field to be copied to instance __dict__ (which breaks
                # the descriptor protocol)
                if name in cls.__annotations__:
                    del cls.__annotations__[name]

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:  # noqa: ANN401
        """Set up ORM FK metadata after Pydantic has created model_fields.

        This runs AFTER Pydantic populates model_fields, so we can add FK
        metadata to the _id fields that Pydantic created.
        """
        # Call parent __pydantic_init_subclass__ FIRST
        super().__pydantic_init_subclass__(**kwargs)

        # Process FK descriptors - add FK metadata, register relationships
        cls._setup_orm_fields()

        # Register model in global registry
        ModelRegistry.register_model(cls)

    @classmethod
    def _setup_orm_fields(cls) -> None:
        """Add FK metadata to _id fields and register FK relationships.

        Called during class creation (after Pydantic setup) to:
        1. Add FK metadata to _id fields for constraint generation
        2. Register FK relationships in ModelRegistry
        3. Remove descriptor from model_fields so Pydantic doesn't validate it
        """
        # Get FK descriptors for this class
        fk_descriptors_copy = cls.fk_descriptors.copy()

        for field_name in fk_descriptors_copy:
            descriptor = cls.fk_descriptors[field_name]

            # Create _id field name
            id_field_name = f"{field_name}_id"

            # Get ForeignKeyInfo from descriptor
            fk_info = descriptor.fk_info

            # The _id field should exist (created by Pydantic from annotation)
            # We need to add FK metadata for constraint generation
            if id_field_name in cls.model_fields:
                existing_field = cls.model_fields[id_field_name]

                # Create ForeignKeyInfo with proper db_column
                fk_info_for_field = type(fk_info)(
                    to_model=fk_info.to_model,
                    on_delete=fk_info.on_delete,
                    on_update=fk_info.on_update,
                    null=fk_info.null,
                    unique=fk_info.unique,
                    related_name=fk_info.related_name,
                    db_column=fk_info.db_column or id_field_name,
                )

                # Add FK metadata to existing field's json_schema_extra
                # The ForeignKeyInfo is stored for _build_field_definitions()
                if existing_field.json_schema_extra is None:
                    existing_field.json_schema_extra = {}
                if isinstance(existing_field.json_schema_extra, dict):
                    # ForeignKeyInfo stored for _build_field_definitions
                    existing_field.json_schema_extra["foreign_key"] = (
                        fk_info_for_field  # type: ignore[assignment]
                    )

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
