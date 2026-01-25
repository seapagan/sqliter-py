"""ORM Features demos."""

from __future__ import annotations

import io

from sqliter import SqliterDB
from sqliter.orm import BaseDBModel, ForeignKey
from sqliter.tui.demos.base import Demo, DemoCategory, extract_demo_code


def _run_lazy_loading() -> str:
    """Load related objects on-demand using foreign keys.

    Accessing a ForeignKey field triggers a database query to fetch the
    related object only when you need it.
    """
    output = io.StringIO()

    class Author(BaseDBModel):
        name: str

    class Book(BaseDBModel):
        title: str
        author: ForeignKey[Author] = ForeignKey(Author)

    db = SqliterDB(memory=True)
    db.create_table(Author)
    db.create_table(Book)

    author = db.insert(Author(name="J.K. Rowling"))
    book1 = db.insert(Book(title="Harry Potter 1", author=author))
    book2 = db.insert(Book(title="Harry Potter 2", author=author))

    output.write(f"Author: {author.name}\n")
    output.write(f"Author ID: {author.pk}\n")

    # Access related author through foreign key - triggers lazy load
    output.write("\nAccessing book.author triggers lazy load:\n")
    book_author = book1.author  # LazyLoader fetches author from DB
    output.write(f"  '{book1.title}' was written by {book_author.name}\n")

    output.write(f"\n'{book2.title}' was written by {book2.author.name}\n")
    output.write("Related objects loaded on-demand from database\n")

    db.close()
    return output.getvalue()


def _run_orm_style_access() -> str:
    """Insert records with foreign key relationships.

    BaseDBModel provides attribute-style access to fields, with automatic
    primary key generation via the pk field. Foreign keys store related
    object primary keys.
    """
    output = io.StringIO()

    class Author(BaseDBModel):
        name: str

    class Book(BaseDBModel):
        title: str
        author: ForeignKey[Author] = ForeignKey(Author)

    db = SqliterDB(memory=True)
    db.create_table(Author)
    db.create_table(Book)

    author = db.insert(Author(name="Jane Austen"))
    book = db.insert(Book(title="Pride and Prejudice", author=author))

    output.write("Created book:\n")
    output.write(f"  title: {book.title}\n")
    output.write(f"  author: {book.author.name}\n")
    output.write(
        "\nForeign key stores the primary key internally,\n"
        "but access returns the object\n"
    )

    db.close()
    return output.getvalue()


def _run_relationship_navigation() -> str:
    """Navigate from one object to another using foreign keys.

    ForeignKey fields let you traverse relationships by accessing
    related objects as attributes.
    """
    output = io.StringIO()

    class Team(BaseDBModel):
        name: str

    class Player(BaseDBModel):
        name: str
        team: ForeignKey[Team] = ForeignKey(Team)

    db = SqliterDB(memory=True)
    db.create_table(Team)
    db.create_table(Player)

    team = db.insert(Team(name="Lakers"))
    player1 = db.insert(Player(name="LeBron", team=team))
    player2 = db.insert(Player(name="Davis", team=team))

    output.write(f"Team: {team.name}\n")

    # Navigate from player to team via FK
    output.write(f"\n{player1.name} plays for: {player1.team.name}\n")
    output.write(f"{player2.name} plays for: {player2.team.name}\n")
    output.write("Foreign keys enable relationship navigation\n")

    db.close()
    return output.getvalue()


def _run_reverse_relationships() -> str:
    """Access related objects in reverse using related_name.

    When you define a ForeignKey, SQLiter automatically creates a reverse
    relationship to access all objects that reference a given object.
    """
    output = io.StringIO()

    class Author(BaseDBModel):
        name: str

    class Book(BaseDBModel):
        title: str
        author: ForeignKey[Author] = ForeignKey(Author, related_name="books")

    db = SqliterDB(memory=True)
    db.create_table(Author)
    db.create_table(Book)

    author = db.insert(Author(name="Jane Austen"))
    db.insert(Book(title="Pride and Prejudice", author=author))
    db.insert(Book(title="Emma", author=author))
    db.insert(Book(title="Sense and Sensibility", author=author))

    output.write(f"Author: {author.name}\n")

    # Access reverse relationship - get all books by this author
    # Note: 'books' attribute added dynamically by ForeignKey descriptor
    output.write("\nAccessing author.books (reverse relationship):\n")
    books = author.books.fetch_all()  # type: ignore[attr-defined]
    for book in books:
        output.write(f"  - {book.title}\n")

    output.write(f"\nTotal books: {len(books)}\n")
    output.write("Reverse relationships auto-generated from FKs\n")

    db.close()
    return output.getvalue()


def get_category() -> DemoCategory:
    """Get the ORM Features demo category."""
    return DemoCategory(
        id="orm",
        title="ORM Features",
        icon="",
        demos=[
            Demo(
                id="orm_lazy",
                title="Lazy Loading",
                description="Load related data on demand",
                category="orm",
                code=extract_demo_code(_run_lazy_loading),
                execute=_run_lazy_loading,
            ),
            Demo(
                id="orm_fk_insert",
                title="Inserting with Foreign Keys",
                description="Create records linked to other records",
                category="orm",
                code=extract_demo_code(_run_orm_style_access),
                execute=_run_orm_style_access,
            ),
            Demo(
                id="orm_relationships",
                title="Relationship Navigation",
                description="Navigate using foreign keys",
                category="orm",
                code=extract_demo_code(_run_relationship_navigation),
                execute=_run_relationship_navigation,
            ),
            Demo(
                id="orm_reverse",
                title="Reverse Relationships",
                description="Access related objects via related_name",
                category="orm",
                code=extract_demo_code(_run_reverse_relationships),
                execute=_run_reverse_relationships,
            ),
        ],
    )
