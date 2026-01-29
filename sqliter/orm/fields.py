"""Field descriptors for ORM relationships."""

from __future__ import annotations

import logging
import types
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Optional,
    Protocol,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
    overload,
    runtime_checkable,
)

from pydantic_core import core_schema

from sqliter.model.foreign_key import ForeignKeyInfo

if TYPE_CHECKING:  # pragma: no cover
    from pydantic import GetCoreSchemaHandler

    from sqliter.model.foreign_key import FKAction
    from sqliter.model.model import BaseDBModel
    from sqliter.sqliter import SqliterDB

T = TypeVar("T")


logger = logging.getLogger(__name__)


def _split_top_level(text: str, sep: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    buf: list[str] = []
    for ch in text:
        if ch in "[(":
            depth += 1
        elif ch in "])":
            depth -= 1
        if ch == sep and depth == 0:
            parts.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf).strip())
    return parts


def _annotation_is_nullable(raw: str) -> bool:
    """Best-effort check for Optional or | None at top level."""
    s = raw.replace("typing.", "").replace("sqliter.orm.fields.", "").strip()

    if "[" not in s or "]" not in s:
        return False

    inner = s[s.find("[") + 1 : s.rfind("]")].strip()

    if inner.startswith("Optional["):
        return True

    if "|" in inner and any(
        part == "None" for part in _split_top_level(inner, "|")
    ):
        return True

    if inner.startswith("Union[") and inner.endswith("]"):
        union_inner = inner[len("Union[") : -1]
        if any(part == "None" for part in _split_top_level(union_inner, ",")):
            return True

    return False


@runtime_checkable
class HasPK(Protocol):
    """Protocol for objects that have a pk attribute."""

    pk: Optional[int]


class LazyLoader(Generic[T]):
    """Proxy object that lazy loads a related object when accessed.

    When a FK field is accessed, returns a LazyLoader that queries the database
    on first access and caches the result.

    Note: This class is an implementation detail. For type checking purposes,
    ForeignKey fields are typed as returning T (the type parameter), not
    LazyLoader[T]. This follows the standard ORM pattern used by SQLAlchemy,
    where the proxy is transparent to users. Use ForeignKey[Optional[Model]]
    for nullable foreign keys.
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

    @property
    def db_context(self) -> object:
        """Return the database context (for checking if loader is valid)."""
        return self._db

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
            # Catch DB errors (missing table, connection issues, etc.)
            # and treat as "not found" - AttributeError will be raised
            # by __getattr__ when accessing attributes on None
            from sqliter.exceptions import SqliterError  # noqa: PLC0415

            try:
                # Cast to type[BaseDBModel] for SqliterDB.get() - T is always
                # a BaseDBModel subclass in practice
                result = self._db.get(
                    cast("type[BaseDBModel]", self._to_model), self._fk_id
                )
                self._cached = cast("Optional[T]", result)
            except SqliterError as e:
                # DB errors (missing table, fetch errors) → treat as not found
                logger.debug(
                    "LazyLoader failed to fetch %s with pk=%s: %s",
                    self._to_model.__name__,
                    self._fk_id,
                    e,
                )
                self._cached = None

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

    # Unhashable due to mutable equality (based on cached object)
    __hash__ = None  # type: ignore[assignment]


class ForeignKey(Generic[T]):
    """Generic descriptor for FK fields providing lazy loading.

    When a FK field is accessed on a model instance, returns a LazyLoader
    that queries the database for the related object.

    Usage:
        class Book(BaseDBModel):
            title: str
            author: ForeignKey[Author] = ForeignKey(Author, on_delete="CASCADE")

    The generic parameter T represents the related model type, ensuring
    proper type checking when accessing the relationship.
    """

    def __init__(  # noqa: PLR0913
        self,
        to_model: type[T],
        *,
        on_delete: FKAction = "RESTRICT",
        on_update: FKAction = "RESTRICT",
        null: bool = False,
        unique: bool = False,
        related_name: Optional[str] = None,
        db_column: Optional[str] = None,
    ) -> None:
        """Initialize FK descriptor.

        Args:
            to_model: The related model class
            on_delete: Action when related object is deleted
            on_update: Action when related object's PK is updated
            null: Whether FK can be null
            unique: Whether FK must be unique
            related_name: Name for reverse relationship (auto-generated if None)
            db_column: Custom column name for _id field
        """
        self.to_model = to_model
        self.fk_info = ForeignKeyInfo(
            to_model=cast("type[BaseDBModel]", to_model),
            on_delete=on_delete,
            on_update=on_update,
            null=null,
            unique=unique,
            related_name=related_name,
            # Let _setup_orm_fields set default from actual field name
            db_column=db_column,
        )
        self.related_name = related_name
        self.name: Optional[str] = None  # Set by __set_name__
        self.owner: Optional[type] = None  # Set by __set_name__

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: type[Any],
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        """Tell Pydantic how to handle ForeignKey[T] type annotations.

        Uses no_info_plain_validator_function to prevent the descriptor from
        being stored in instance __dict__, which would break the descriptor
        protocol. The ForeignKey descriptor must remain at class level only.
        """
        # Return a validator that doesn't store anything in __dict__
        # This prevents Pydantic from copying the descriptor to instances
        return core_schema.no_info_plain_validator_function(
            function=lambda _: None  # Value is ignored
        )

    def _detect_nullable_from_annotation(self, owner: type, name: str) -> None:
        """Detect if FK is nullable from type annotation.

        If the annotation is ForeignKey[Optional[T]], automatically set
        null=True on the FK info. This allows users to declare nullability
        via the type annotation alone.
        """
        try:
            hints = get_type_hints(owner)
        except Exception:  # noqa: BLE001
            # Can fail with forward refs, NameError, etc. - fallback to raw
            raw = owner.__annotations__.get(name)
            if isinstance(raw, str) and _annotation_is_nullable(raw):
                self.fk_info.null = True
            return

        if name not in hints:
            return

        annotation = hints[name]  # e.g., ForeignKey[Optional[Author]]
        fk_args = get_args(annotation)  # e.g., (Optional[Author],)

        if not fk_args:
            return

        inner_type = fk_args[0]  # e.g., Optional[Author] or Author

        # Check if inner_type is Optional (Union with None)
        # Handle both typing.Union (Optional[T]) and types.UnionType
        # (T | None on Python 3.10+)
        origin = get_origin(inner_type)
        is_union = origin is Union
        if not is_union and hasattr(types, "UnionType"):
            is_union = isinstance(inner_type, types.UnionType)
        if is_union:
            args = get_args(inner_type)
            if type(None) in args:
                self.fk_info.null = True

    def __set_name__(self, owner: type, name: str) -> None:
        """Called automatically during class creation.

        Sets up reverse relationship on the related model immediately.
        If related model doesn't exist yet, stores as pending in ModelRegistry.

        If no `related_name` is provided, one is auto-generated by pluralizing
        the owner class name. If the `inflect` library is installed, it provides
        grammatically correct pluralization (e.g., "Person" becomes "people").
        Otherwise, a simple "s" suffix is added.

        Auto-detects nullable FKs from the type annotation: if the type is
        ForeignKey[Optional[T]], sets null=True automatically.
        """
        self.name = name
        self.owner = owner

        # Auto-detect nullable from type annotation
        # If user writes ForeignKey[Optional[Model]], set null=True
        self._detect_nullable_from_annotation(owner, name)

        # Store descriptor in class's OWN fk_descriptors dict (not inherited)
        # Check __dict__ to avoid getting inherited dict from parent class
        if "fk_descriptors" not in owner.__dict__:
            owner.fk_descriptors = {}  # type: ignore[attr-defined]
        owner.fk_descriptors[name] = self  # type: ignore[attr-defined]

        # Auto-generate related_name if not provided
        if self.related_name is None:
            # Generate pluralized name from owner class name
            base_name = owner.__name__.lower()
            try:
                import inflect  # noqa: PLC0415

                p = inflect.engine()
                self.related_name = p.plural(base_name)
            except ImportError:
                # Fallback to simple pluralization by adding 's'
                self.related_name = (
                    base_name if base_name.endswith("s") else base_name + "s"
                )

        # Set up reverse relationship on related model
        from sqliter.orm.registry import ModelRegistry  # noqa: PLC0415

        ModelRegistry.add_reverse_relationship(
            from_model=owner,
            to_model=self.to_model,
            fk_field=name,
            related_name=self.related_name,
        )

    @overload
    def __get__(self, instance: None, owner: type[object]) -> ForeignKey[T]: ...

    @overload
    def __get__(self, instance: object, owner: type[object]) -> T: ...

    def __get__(
        self, instance: Optional[object], owner: type[object]
    ) -> Union[ForeignKey[T], T]:
        """Return LazyLoader that loads related object on attribute access.

        If accessed on class (not instance), return the descriptor itself.

        Note: The return type is T (the type parameter). For nullable FKs,
        use ForeignKey[Optional[Model]] and T will be Optional[Model].
        The actual runtime return is a LazyLoader[T] proxy, but type checkers
        see T for proper attribute access inference.
        """
        if instance is None:
            return self

        # Get FK ID from instance
        fk_id = getattr(instance, f"{self.name}_id", None)

        # Return LazyLoader for lazy loading
        # Cast to T for type checking - LazyLoader is a transparent proxy
        # that behaves like T. For nullable FKs, T is Optional[Model].
        return cast(
            "T",
            LazyLoader(
                instance=instance,
                to_model=self.to_model,
                fk_id=fk_id,
                db_context=getattr(instance, "db_context", None),
            ),
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
        # Note: FK cache is cleared by BaseDBModel.__setattr__ when _id changes


# Backwards compatibility alias
ForeignKeyDescriptor = ForeignKey
