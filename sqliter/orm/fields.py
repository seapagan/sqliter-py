"""Field descriptors for ORM relationships."""

from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar

T = TypeVar("T")


class LazyLoader(Generic[T]):
    """Proxy object that lazy loads a related object when accessed.

    When a FK field is accessed, returns a LazyLoader that queries the database
    on first access and caches the result.
    """

    def __init__(
        self,
        instance: Any,
        to_model: type[T],
        fk_id: Optional[int],
        db_context: Any,
    ) -> None:
        """Initialize lazy loader.

        Args:
            instance: The model instance with the FK
            to_model: The related model class to load
            fk_id: The foreign key ID value
            db_context: Database connection for queries
        """
        self._instance = instance
        self._to_model = to_model
        self._fk_id = fk_id
        self._db = db_context
        self._cached: Optional[T] = None

    def __getattr__(self, name: str) -> Any:
        """Load related object and delegate attribute access."""
        if self._cached is None:
            self._load()
        if self._cached is None:
            msg = (
                f"Cannot access {name} on None (FK is null or object not found)"
            )
            raise AttributeError(msg)
        return getattr(self._cached, name)

    def _load(self) -> None:
        """Load related object from database if not already cached."""
        if self._fk_id is None:
            self._cached = None
            return

        if self._cached is None and self._db is not None:
            # Use db_context to fetch the related object
            self._cached = self._db.get(self._to_model, self._fk_id)

    def __repr__(self) -> str:
        """Representation showing lazy state."""
        if self._cached is None:
            return (
                f"<LazyLoader unloaded for {self._to_model.__name__} "
                f"id={self._fk_id}>"
            )
        return f"<LazyLoader loaded: {self._cached!r}>"

    def __eq__(self, other: object) -> bool:
        """Compare based on loaded object."""
        if self._cached is None:
            self._load()
        if self._cached is None:
            return other is None
        return self._cached == other


class ForeignKeyDescriptor:
    """Descriptor for FK fields providing lazy loading.

    When a FK field is accessed on a model instance, returns a LazyLoader
    that queries the database for the related object.

    During class creation, __set_name__ is called to set up reverse
    relationships.
    """

    def __init__(
        self,
        to_model: type,
        on_delete: str = "RESTRICT",
        null: bool = False,
        unique: bool = False,
        related_name: Optional[str] = None,
        db_column: Optional[str] = None,
    ) -> None:
        """Initialize FK descriptor.

        Args:
            to_model: The related model class
            on_delete: Action when related object is deleted
            null: Whether FK can be null
            unique: Whether FK must be unique
            related_name: Name for reverse relationship (auto-generated if None)
            db_column: Custom column name for _id field
        """
        from sqliter.model.foreign_key import ForeignKeyInfo

        self.to_model = to_model
        self.fk_info = ForeignKeyInfo(
            to_model=to_model,
            on_delete=on_delete,  # type: ignore[arg-type]
            on_update="RESTRICT",
            null=null,
            unique=unique,
            related_name=related_name,
            db_column=db_column or f"{to_model.__name__.lower()}_id",
        )
        self.related_name = related_name
        self.name: Optional[str] = None  # Set by __set_name__
        self.owner: Optional[type] = None  # Set by __set_name__

    def __set_name__(self, owner: type, name: str) -> None:
        """Called automatically during class creation.

        Sets up reverse relationship on the related model immediately.
        If related model doesn't exist yet, stores as pending in ModelRegistry.
        """
        self.name = name
        self.owner = owner

        # Store descriptor in class's _fk_descriptors dict
        if not hasattr(owner, "_fk_descriptors"):
            owner._fk_descriptors = {}  # type: ignore[attr-defined]
        owner._fk_descriptors[name] = self  # type: ignore[attr-defined]

        # Auto-generate related_name if not provided
        if self.related_name is None:
            # Generate pluralized name from owner class name
            self.related_name = f"{owner.__name__.lower()}s"

        # Set up reverse relationship on related model
        from sqliter.orm.registry import ModelRegistry

        ModelRegistry.add_reverse_relationship(
            from_model=owner,
            to_model=self.to_model,
            fk_field=name,
            related_name=self.related_name,
        )

    def __get__(self, instance: Any, owner: type) -> Any:
        """Return LazyLoader that loads related object on attribute access.

        If accessed on class (not instance), return the descriptor itself.
        """
        if instance is None:
            return self

        # Get FK ID from instance
        fk_id = getattr(instance, f"{self.name}_id", None)

        # Return LazyLoader for lazy loading
        return LazyLoader(
            instance=instance,
            to_model=self.to_model,
            fk_id=fk_id,
            db_context=instance.db_context,
        )

    def __set__(self, instance: Any, value: Any) -> None:
        """Set FK value - handles model instances, ints, or None.

        Args:
            instance: Model instance
            value: New FK value (model instance, int ID, or None)
        """
        from sqliter.model.model import BaseDBModel

        if value is None:
            # Set to None
            setattr(instance, f"{self.name}_id", None)
        elif isinstance(value, BaseDBModel):
            # Extract pk from model instance
            setattr(instance, f"{self.name}_id", value.pk)
        elif isinstance(value, int):
            # Set ID directly
            setattr(instance, f"{self.name}_id", value)
        else:
            msg = f"FK value must be BaseModel, int, or None, got {type(value)}"
            raise TypeError(msg)
