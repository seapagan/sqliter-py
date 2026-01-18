"""ForeignKey function for ORM mode.

This returns a ForeignKeyDescriptor (NOT a Pydantic Field like Phase 1).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqliter.orm.fields import ForeignKeyDescriptor

if TYPE_CHECKING:  # pragma: no cover
    from sqliter.model.foreign_key import FKAction
    from sqliter.model.model import BaseDBModel


def ForeignKey(  # noqa: N802
    to: type[BaseDBModel],
    on_delete: FKAction = "RESTRICT",
    *,
    null: bool = False,
    unique: bool = False,
    related_name: Optional[str] = None,
    db_column: Optional[str] = None,
) -> ForeignKeyDescriptor:
    """Create a FK field with lazy loading (ORM mode).

    Returns a ForeignKeyDescriptor (NOT a Pydantic Field like Phase 1).

    Args:
        to: The related model class
        on_delete: Action when related object is deleted (CASCADE, RESTRICT,
            SET_NULL)
        null: Whether FK can be null
        unique: Whether FK must be unique
        related_name: Name for reverse relationship (auto-generated if None)
        db_column: Custom column name for _id field

    Returns:
        ForeignKeyDescriptor for lazy loading

    Example:
        class Author(BaseDBModel):
            name: str

        class Book(BaseDBModel):
            title: str
            author: Author = ForeignKey(Author, on_delete="CASCADE")

        # Usage
        author = db.insert(Author(name="John"))
        book = db.insert(Book(title="My Book", author=author))

        # Lazy loading
        print(book.author.name)  # Queries DB for Author

        # Reverse relationship (auto-generated)
        books = author.books.fetch_all()
    """
    return ForeignKeyDescriptor(
        to_model=to,
        on_delete=on_delete,
        null=null,
        unique=unique,
        related_name=related_name,
        db_column=db_column,
    )
