"""Many-to-many relationship support for ORM mode."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Optional,
    Protocol,
    TypeVar,
    Union,
    cast,
    overload,
    runtime_checkable,
)

from pydantic_core import core_schema

from sqliter.exceptions import ManyToManyIntegrityError, TableCreationError

if TYPE_CHECKING:  # pragma: no cover
    from pydantic import GetCoreSchemaHandler

    from sqliter.model.model import BaseDBModel
    from sqliter.query.query import QueryBuilder
    from sqliter.sqliter import SqliterDB

T = TypeVar("T")


@runtime_checkable
class HasPKAndContext(Protocol):
    """Protocol for model instances with pk and db_context."""

    pk: Optional[int]
    db_context: Optional[Any]


@dataclass
class ManyToManyInfo:
    """Metadata for a many-to-many relationship.

    Attributes:
        to_model: The target model class.
        through: Custom junction table name (auto-generated if None).
        related_name: Name for the reverse accessor on the target model.
    """

    to_model: type[Any]
    through: Optional[str] = None
    related_name: Optional[str] = field(default=None)


class ManyToManyManager(Generic[T]):
    """Manager for M2M relationships on a model instance.

    Provides methods to add, remove, clear, set, and query related
    objects through a junction table.
    """

    def __init__(
        self,
        instance: HasPKAndContext,
        to_model: type[T],
        from_model: type[Any],
        m2m_field: str,
        junction_table: str,
        db_context: Optional[SqliterDB],
    ) -> None:
        """Initialize M2M manager.

        Args:
            instance: The model instance owning this relationship.
            to_model: The target model class.
            from_model: The source model class.
            m2m_field: Name of the M2M field.
            junction_table: Name of the junction table.
            db_context: Database connection for queries.
        """
        self._instance = instance
        self._to_model = to_model
        self._from_model = from_model
        self._m2m_field = m2m_field
        self._junction_table = junction_table
        self._db = db_context

        # Column names based on alphabetically sorted table names
        from_table = cast("type[BaseDBModel]", from_model).get_table_name()
        to_table = cast("type[BaseDBModel]", to_model).get_table_name()
        self._from_col = f"{from_table}_pk"
        self._to_col = f"{to_table}_pk"

    def _check_context(self) -> SqliterDB:
        """Verify db_context and pk are available.

        Returns:
            The database context.

        Raises:
            ManyToManyIntegrityError: If no db_context or no pk.
        """
        if self._db is None:
            msg = (
                "No database context available. "
                "Insert the instance first or use within a db context."
            )
            raise ManyToManyIntegrityError(msg)
        pk = getattr(self._instance, "pk", None)
        if not pk:
            msg = (
                "Instance has no primary key. "
                "Insert the instance before managing relationships."
            )
            raise ManyToManyIntegrityError(msg)
        return self._db

    def _get_instance_pk(self) -> int:
        """Get the primary key of the owning instance.

        Returns:
            The primary key value.
        """
        # pk is guaranteed non-None after _check_context()
        return int(self._instance.pk)  # type: ignore[arg-type]

    @staticmethod
    def _as_filter_list(
        pks: list[int],
    ) -> list[Union[str, int, float, bool]]:
        """Cast pk list for QueryBuilder.filter() compatibility.

        Args:
            pks: List of integer primary keys.

        Returns:
            The same list cast to the FilterValue list type.
        """
        return cast("list[Union[str, int, float, bool]]", pks)

    def _fetch_related_pks(self) -> list[int]:
        """Fetch PKs of related objects from the junction table.

        Returns:
            List of related object primary keys.
        """
        if self._db is None:
            return []
        pk = getattr(self._instance, "pk", None)
        if not pk:
            return []

        sql = (
            f'SELECT "{self._to_col}" FROM "{self._junction_table}" '  # noqa: S608
            f'WHERE "{self._from_col}" = ?'
        )
        conn = self._db.connect()
        cursor = conn.cursor()
        cursor.execute(sql, (pk,))
        return [row[0] for row in cursor.fetchall()]

    def add(self, *instances: T) -> None:
        """Add one or more related objects.

        Duplicates are silently ignored (INSERT OR IGNORE).

        Args:
            *instances: Model instances to relate.

        Raises:
            ManyToManyIntegrityError: If no db_context, no pk, or
                a target instance has no pk.
        """
        db = self._check_context()
        from_pk = self._get_instance_pk()

        sql = (
            f'INSERT OR IGNORE INTO "{self._junction_table}" '  # noqa: S608
            f'("{self._from_col}", "{self._to_col}") VALUES (?, ?)'
        )

        conn = db.connect()
        cursor = conn.cursor()
        for inst in instances:
            to_pk = getattr(inst, "pk", None)
            if not to_pk:
                msg = (
                    "Related instance has no primary key. "
                    "Insert it before adding to a relationship."
                )
                raise ManyToManyIntegrityError(msg)
            cursor.execute(sql, (from_pk, to_pk))

        db._maybe_commit()  # noqa: SLF001

    def remove(self, *instances: T) -> None:
        """Remove one or more related objects.

        Nonexistent relationships are silently ignored.

        Args:
            *instances: Model instances to unrelate.

        Raises:
            ManyToManyIntegrityError: If no db_context or no pk.
        """
        db = self._check_context()
        from_pk = self._get_instance_pk()

        sql = (
            f'DELETE FROM "{self._junction_table}" '  # noqa: S608
            f'WHERE "{self._from_col}" = ? AND "{self._to_col}" = ?'
        )

        conn = db.connect()
        cursor = conn.cursor()
        for inst in instances:
            to_pk = getattr(inst, "pk", None)
            if to_pk:
                cursor.execute(sql, (from_pk, to_pk))

        db._maybe_commit()  # noqa: SLF001

    def clear(self) -> None:
        """Remove all relationships for this instance.

        Raises:
            ManyToManyIntegrityError: If no db_context or no pk.
        """
        db = self._check_context()
        from_pk = self._get_instance_pk()

        sql = (
            f'DELETE FROM "{self._junction_table}" WHERE "{self._from_col}" = ?'  # noqa: S608
        )

        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(sql, (from_pk,))
        db._maybe_commit()  # noqa: SLF001

    def set(self, *instances: T) -> None:
        """Replace all relationships with the given instances.

        Clears existing relationships then adds the new ones.

        Args:
            *instances: Model instances to set as the new related set.

        Raises:
            ManyToManyIntegrityError: If no db_context or no pk.
        """
        self.clear()
        if instances:
            self.add(*instances)

    def fetch_all(self) -> list[T]:
        """Fetch all related objects.

        Returns:
            List of related model instances.
        """
        pks = self._fetch_related_pks()
        if not pks or self._db is None:
            return []

        model = cast("type[BaseDBModel]", self._to_model)
        return cast(
            "list[T]",
            self._db.select(model)
            .filter(pk__in=self._as_filter_list(pks))
            .fetch_all(),
        )

    def fetch_one(self) -> Optional[T]:
        """Fetch a single related object.

        Returns:
            A related model instance, or None.
        """
        pks = self._fetch_related_pks()
        if not pks or self._db is None:
            return None

        model = cast("type[BaseDBModel]", self._to_model)
        pk_filter = self._as_filter_list(pks)
        results = (
            self._db.select(model).filter(pk__in=pk_filter).limit(1).fetch_all()
        )
        return cast("Optional[T]", results[0]) if results else None

    def count(self) -> int:
        """Count related objects via the junction table.

        Returns:
            Number of related objects.
        """
        if self._db is None:
            return 0
        pk = getattr(self._instance, "pk", None)
        if not pk:
            return 0

        sql = (
            f'SELECT COUNT(*) FROM "{self._junction_table}" '  # noqa: S608
            f'WHERE "{self._from_col}" = ?'
        )
        conn = self._db.connect()
        cursor = conn.cursor()
        cursor.execute(sql, (pk,))
        row = cursor.fetchone()
        return int(row[0]) if row else 0

    def exists(self) -> bool:
        """Check if any related objects exist.

        Returns:
            True if at least one related object exists.
        """
        return self.count() > 0

    def filter(
        self,
        **kwargs: Any,  # noqa: ANN401
    ) -> QueryBuilder[Any]:
        """Return a QueryBuilder filtered to related objects.

        Allows full chaining (order_by, limit, offset, etc.).

        Args:
            **kwargs: Additional filter criteria.

        Returns:
            A QueryBuilder instance.

        Raises:
            ManyToManyIntegrityError: If no db_context or no pk.
        """
        db = self._check_context()
        model = cast("type[BaseDBModel]", self._to_model)
        pks = self._fetch_related_pks()
        pk_filter = self._as_filter_list(pks)
        return db.select(model).filter(pk__in=pk_filter, **kwargs)


class ManyToMany(Generic[T]):
    """Descriptor for many-to-many relationship fields.

    Usage:
        class Article(BaseDBModel):
            title: str
            tags: ManyToMany[Tag] = ManyToMany(Tag)
    """

    def __init__(
        self,
        to_model: type[T],
        *,
        through: Optional[str] = None,
        related_name: Optional[str] = None,
    ) -> None:
        """Initialize M2M descriptor.

        Args:
            to_model: The related model class.
            through: Custom junction table name.
            related_name: Name for the reverse accessor on the target.
        """
        self.to_model = to_model
        self.m2m_info = ManyToManyInfo(
            to_model=to_model,
            through=through,
            related_name=related_name,
        )
        self.related_name = related_name
        self.name: Optional[str] = None
        self.owner: Optional[type] = None
        self._junction_table: Optional[str] = None

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: type[Any],
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        """Prevent Pydantic from copying descriptor to instance."""
        return core_schema.no_info_plain_validator_function(
            function=lambda _: None
        )

    def _get_junction_table_name(self, owner: type[Any]) -> str:
        """Compute the junction table name.

        Alphabetically sorts the two table names and joins with '_'.

        Args:
            owner: The model class owning this descriptor.

        Returns:
            The junction table name.
        """
        if self.m2m_info.through:
            return self.m2m_info.through

        owner_model = cast("type[BaseDBModel]", owner)
        target_model = cast("type[BaseDBModel]", self.to_model)
        owner_table = owner_model.get_table_name()
        target_table = target_model.get_table_name()
        sorted_names = sorted([owner_table, target_table])
        return f"{sorted_names[0]}_{sorted_names[1]}"

    def __set_name__(self, owner: type, name: str) -> None:
        """Called during class creation to register the M2M field.

        Args:
            owner: The model class.
            name: The attribute name.
        """
        self.name = name
        self.owner = owner
        self._junction_table = self._get_junction_table_name(owner)

        # Store in class's own m2m_descriptors
        if "m2m_descriptors" not in owner.__dict__:
            owner.m2m_descriptors = {}  # type: ignore[attr-defined]
        owner.m2m_descriptors[name] = self  # type: ignore[attr-defined]

        # Auto-generate related_name if not provided
        if self.related_name is None:
            base_name = owner.__name__.lower()
            try:
                import inflect  # noqa: PLC0415

                p = inflect.engine()
                self.related_name = p.plural(base_name)
            except ImportError:
                self.related_name = (
                    base_name if base_name.endswith("s") else base_name + "s"
                )

        self.m2m_info.related_name = self.related_name

        # Register with ModelRegistry
        from sqliter.orm.registry import ModelRegistry  # noqa: PLC0415

        ModelRegistry.add_m2m_relationship(
            from_model=owner,
            to_model=self.to_model,
            m2m_field=name,
            junction_table=self._junction_table,
            related_name=self.related_name,
        )

    @overload
    def __get__(self, instance: None, owner: type[object]) -> ManyToMany[T]: ...

    @overload
    def __get__(
        self, instance: object, owner: type[object]
    ) -> ManyToManyManager[T]: ...

    def __get__(
        self, instance: Optional[object], owner: type[object]
    ) -> Union[ManyToMany[T], ManyToManyManager[T]]:
        """Return ManyToManyManager on instance, descriptor on class.

        Args:
            instance: Model instance or None.
            owner: Model class.

        Returns:
            ManyToManyManager for instance access, self for class access.
        """
        if instance is None:
            return self

        return ManyToManyManager(
            instance=cast("HasPKAndContext", instance),
            to_model=self.to_model,
            from_model=owner,
            m2m_field=self.name or "",
            junction_table=self._junction_table or "",
            db_context=getattr(instance, "db_context", None),
        )

    def __set__(self, instance: object, value: object) -> None:
        """Prevent direct assignment to M2M fields.

        Args:
            instance: Model instance.
            value: The value being assigned.

        Raises:
            AttributeError: Always, directing users to use
                add()/remove()/clear()/set().
        """
        msg = (
            f"Cannot assign to ManyToMany field '{self.name}'. "
            f"Use .add(), .remove(), .clear(), or .set() instead."
        )
        raise AttributeError(msg)


class ReverseManyToMany:
    """Descriptor for the reverse side of a M2M relationship.

    Placed automatically on the target model by ModelRegistry.
    """

    def __init__(
        self,
        from_model: type[Any],
        to_model: type[Any],
        m2m_field: str,
        junction_table: str,
        related_name: str,
    ) -> None:
        """Initialize reverse M2M descriptor.

        Args:
            from_model: The model that defined the ManyToMany field.
            to_model: The target model (where this descriptor lives).
            m2m_field: Name of the M2M field on from_model.
            junction_table: Name of the junction table.
            related_name: Name of this reverse accessor.
        """
        self._from_model = from_model
        self._to_model = to_model
        self._m2m_field = m2m_field
        self._junction_table = junction_table
        self._related_name = related_name

    @overload
    def __get__(
        self, instance: None, owner: type[object]
    ) -> ReverseManyToMany: ...

    @overload
    def __get__(
        self, instance: object, owner: type[object]
    ) -> ManyToManyManager[Any]: ...

    def __get__(
        self, instance: Optional[object], owner: type[object]
    ) -> Union[ReverseManyToMany, ManyToManyManager[Any]]:
        """Return ManyToManyManager with from/to swapped.

        Args:
            instance: Model instance or None.
            owner: Model class.

        Returns:
            ManyToManyManager (reversed) on instance, self on class.
        """
        if instance is None:
            return self

        # Swap from/to so queries work from the reverse side
        return ManyToManyManager(
            instance=cast("HasPKAndContext", instance),
            to_model=self._from_model,
            from_model=self._to_model,
            m2m_field=self._m2m_field,
            junction_table=self._junction_table,
            db_context=getattr(instance, "db_context", None),
        )

    def __set__(self, instance: object, value: object) -> None:
        """Prevent direct assignment to reverse M2M.

        Args:
            instance: Model instance.
            value: The value being assigned.

        Raises:
            AttributeError: Always.
        """
        msg = (
            f"Cannot assign to reverse ManyToMany "
            f"'{self._related_name}'. "
            f"Use .add(), .remove(), .clear(), or .set() instead."
        )
        raise AttributeError(msg)


def create_junction_table(
    db: SqliterDB,
    junction_table: str,
    table_a: str,
    table_b: str,
) -> None:
    """Create a junction table for a M2M relationship.

    The table has FK columns for both sides with CASCADE constraints
    and a UNIQUE constraint on the pair.

    Args:
        db: The database instance.
        junction_table: Name of the junction table.
        table_a: First table name (alphabetically first).
        table_b: Second table name (alphabetically second).
    """
    col_a = f"{table_a}_pk"
    col_b = f"{table_b}_pk"

    create_sql = (
        f'CREATE TABLE IF NOT EXISTS "{junction_table}" ('
        f'"id" INTEGER PRIMARY KEY AUTOINCREMENT, '
        f'"{col_a}" INTEGER NOT NULL, '
        f'"{col_b}" INTEGER NOT NULL, '
        f'FOREIGN KEY ("{col_a}") REFERENCES "{table_a}"("pk") '
        f"ON DELETE CASCADE ON UPDATE CASCADE, "
        f'FOREIGN KEY ("{col_b}") REFERENCES "{table_b}"("pk") '
        f"ON DELETE CASCADE ON UPDATE CASCADE, "
        f'UNIQUE ("{col_a}", "{col_b}")'
        f")"
    )

    try:
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(create_sql)
        conn.commit()
    except sqlite3.Error as exc:
        raise TableCreationError(junction_table) from exc

    # Create indexes on both FK columns
    for col in (col_a, col_b):
        index_sql = (
            f"CREATE INDEX IF NOT EXISTS "
            f'"idx_{junction_table}_{col}" '
            f'ON "{junction_table}" ("{col}")'
        )
        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(index_sql)
            conn.commit()
        except sqlite3.Error:
            pass  # Non-critical: index creation failure
