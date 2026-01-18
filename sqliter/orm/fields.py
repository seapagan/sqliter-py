"""Field descriptors for ORM relationships."""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Generic,
    Optional,
    Protocol,
    TypeVar,
    Union,
    cast,
    overload,
    runtime_checkable,
)

from sqliter.model.foreign_key import ForeignKeyInfo
from sqliter.model.model import BaseDBModel

if TYPE_CHECKING:  # pragma: no cover
    from sqliter.model.foreign_key import FKAction
    from sqliter.sqliter import SqliterDB

T = TypeVar("T", bound=BaseDBModel)


@runtime_checkable
class HasPK(Protocol):
    """Protocol for objects that have a pk attribute."""

    pk: Optional[int]


class LazyLoader(Generic[T]):
    """Proxy object that lazy loads a related object when accessed.

    When a FK field is accessed, returns a LazyLoader that queries the database
    on first access and caches the result.
    """

    def __init__(
        self,
        instance: object,
        to_model: type[T],
        fk_id: Optional[int],
        db_context: Optional[SqliterDB],
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

    def __getattr__(self, name: str) -> object:
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
            result = self._db.get(self._to_model, self._fk_id)
            self._cached = cast("Optional[T]", result)

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

    def __hash__(self) -> int:
        """Hash based on instance and FK identity (not cached object)."""
        return hash((id(self._instance), self._to_model, self._fk_id))


class ForeignKeyDescriptor:
    """Descriptor for FK fields providing lazy loading.

    When a FK field is accessed on a model instance, returns a LazyLoader
    that queries the database for the related object.

    During class creation, __set_name__ is called to set up reverse
    relationships.
    """

    def __init__(
        self,
        to_model: type[BaseDBModel],
        on_delete: FKAction = "RESTRICT",
        *,
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
        self.to_model = to_model
        self.fk_info = ForeignKeyInfo(
            to_model=to_model,
            on_delete=on_delete,
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

        # Store descriptor in class's fk_descriptors dict
        fk_desc: dict[str, ForeignKeyDescriptor] = getattr(
            owner, "fk_descriptors", {}
        )
        if not fk_desc:
            owner.fk_descriptors = fk_desc  # type: ignore[attr-defined]
        fk_desc[name] = self

        # Auto-generate related_name if not provided
        if self.related_name is None:
            # Generate pluralized name from owner class name
            self.related_name = f"{owner.__name__.lower()}s"

        # Set up reverse relationship on related model
        from sqliter.orm.registry import ModelRegistry  # noqa: PLC0415

        ModelRegistry.add_reverse_relationship(
            from_model=owner,
            to_model=self.to_model,
            fk_field=name,
            related_name=self.related_name,
        )

    @overload
    def __get__(
        self, instance: None, owner: type[object]
    ) -> ForeignKeyDescriptor: ...

    @overload
    def __get__(
        self, instance: object, owner: type[object]
    ) -> LazyLoader[BaseDBModel]: ...

    def __get__(
        self, instance: Optional[object], owner: type[object]
    ) -> Union[ForeignKeyDescriptor, LazyLoader[BaseDBModel]]:
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
            db_context=getattr(instance, "db_context", None),
        )

    def __set__(self, instance: object, value: object) -> None:
        """Set FK value - handles model instances, ints, or None.

        Args:
            instance: Model instance
            value: New FK value (model instance, int ID, or None)
        """
        if value is None:
            # Set to None
            setattr(instance, f"{self.name}_id", None)
        elif isinstance(value, int):
            # Set ID directly
            setattr(instance, f"{self.name}_id", value)
        elif isinstance(value, HasPK):
            # Duck typing via Protocol: extract pk from model instance
            setattr(instance, f"{self.name}_id", value.pk)
        else:
            msg = f"FK value must be BaseModel, int, or None, got {type(value)}"
            raise TypeError(msg)
