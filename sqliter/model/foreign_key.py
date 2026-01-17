"""Foreign key support for SQLiter ORM.

This module provides the ForeignKey factory function and ForeignKeyInfo
dataclass for defining foreign key relationships between models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, Optional

from pydantic import Field

from sqliter.exceptions import InvalidForeignKeyError

if TYPE_CHECKING:  # pragma: no cover
    from pydantic.fields import FieldInfo

    from sqliter.model.model import BaseDBModel

# Type alias for foreign key actions
FKAction = Literal["CASCADE", "SET NULL", "RESTRICT", "NO ACTION"]


@dataclass
class ForeignKeyInfo:
    """Metadata about a foreign key relationship.

    Attributes:
        to_model: The target model class that this foreign key references.
        on_delete: Action to take when the referenced record is deleted.
        on_update: Action to take when the referenced record's PK is updated.
        null: Whether the foreign key field can be NULL.
        unique: Whether the foreign key field must be unique (one-to-one).
        related_name: Optional name for the reverse relationship (Phase 2).
        db_column: Optional custom column name in the database.
    """

    to_model: type[BaseDBModel]
    on_delete: FKAction
    on_update: FKAction
    null: bool
    unique: bool
    related_name: Optional[str]
    db_column: Optional[str]


def ForeignKey(  # noqa: N802, PLR0913
    to: type[BaseDBModel],
    *,
    on_delete: FKAction = "RESTRICT",
    on_update: FKAction = "RESTRICT",
    null: bool = False,
    unique: bool = False,
    related_name: Optional[str] = None,
    db_column: Optional[str] = None,
    default: Any = ...,  # noqa: ANN401
    **kwargs: Any,  # noqa: ANN401
) -> Any:  # noqa: ANN401
    """Create a foreign key field.

    This function creates a Pydantic Field with foreign key metadata stored
    in json_schema_extra. In Phase 1, this provides FK constraint support.
    Phase 2 will add descriptor support for `book.author` style access.

    Args:
        to: The target model class that this foreign key references.
        on_delete: Action when referenced record is deleted.
            - CASCADE: Delete this record too.
            - SET NULL: Set this field to NULL (requires null=True).
            - RESTRICT: Prevent deletion if references exist (default).
            - NO ACTION: Similar to RESTRICT in SQLite.
        on_update: Action when referenced record's PK is updated.
            - CASCADE: Update this field to the new PK value.
            - SET NULL: Set this field to NULL (requires null=True).
            - RESTRICT: Prevent update if references exist (default).
            - NO ACTION: Similar to RESTRICT in SQLite.
        null: Whether the foreign key field can be NULL. Default is False.
        unique: Whether the field must be unique (creates one-to-one
            relationship). Default is False.
        related_name: Optional name for the reverse relationship. Reserved
            for Phase 2 implementation.
        db_column: Optional custom column name. If not specified, defaults
            to `{field_name}_id`.
        default: Default value for the field. If null=True and no default
            is provided, defaults to None.
        **kwargs: Additional keyword arguments passed to Pydantic Field.

    Returns:
        A Pydantic Field with foreign key metadata.

    Raises:
        InvalidForeignKeyError: If SET NULL action is used without null=True.

    Example:
        >>> class Book(BaseDBModel):
        ...     title: str
        ...     author_id: int = ForeignKey(Author, on_delete="CASCADE")
    """
    # Validate SET NULL requires null=True
    if on_delete == "SET NULL" and not null:
        msg = "on_delete='SET NULL' requires null=True"
        raise InvalidForeignKeyError(msg)
    if on_update == "SET NULL" and not null:
        msg = "on_update='SET NULL' requires null=True"
        raise InvalidForeignKeyError(msg)

    # Handle existing json_schema_extra
    existing_extra = kwargs.pop("json_schema_extra", {})
    if not isinstance(existing_extra, dict):
        existing_extra = {}

    # Create ForeignKeyInfo metadata
    fk_info = ForeignKeyInfo(
        to_model=to,
        on_delete=on_delete,
        on_update=on_update,
        null=null,
        unique=unique,
        related_name=related_name,
        db_column=db_column,
    )

    # Store FK metadata in json_schema_extra
    existing_extra["foreign_key"] = fk_info
    if unique:
        existing_extra["unique"] = True

    # Set default value
    if default is ... and "default_factory" not in kwargs:
        default = None if null else ...

    return Field(default=default, json_schema_extra=existing_extra, **kwargs)


def get_foreign_key_info(field_info: FieldInfo) -> Optional[ForeignKeyInfo]:
    """Extract ForeignKeyInfo from a field if it's a foreign key.

    Args:
        field_info: The Pydantic FieldInfo to examine.

    Returns:
        The ForeignKeyInfo if the field is a foreign key, None otherwise.
    """
    if not hasattr(field_info, "json_schema_extra"):
        return None
    extra = field_info.json_schema_extra
    if not isinstance(extra, dict):
        return None
    fk_info = extra.get("foreign_key")
    if isinstance(fk_info, ForeignKeyInfo):
        return fk_info
    return None
