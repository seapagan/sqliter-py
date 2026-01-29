"""ORM Features demos."""

from __future__ import annotations

import io
from typing import Optional

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
    output.write(f"  '{book1.title}' was written by {book1.author.name}\n")

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


def _run_nullable_foreign_key() -> str:
    """Declare nullable FKs using Optional[T] in the type annotation.

    SQLiter auto-detects nullability from the annotation so you don't
    need to pass null=True explicitly.

    Note: this demo already uses ForeignKey[Optional[Author]], but
    annotation-based nullability is most reliable when models are defined at
    module level (especially if you use type aliases). We include null=True
    here for compatibility.
    """
    output = io.StringIO()

    class Author(BaseDBModel):
        name: str

    class Book(BaseDBModel):
        title: str
        author: ForeignKey[Optional[Author]] = ForeignKey(
            Author, on_delete="SET NULL", null=True
        )

    db = SqliterDB(memory=True)
    db.create_table(Author)
    db.create_table(Book)

    author = db.insert(Author(name="Jane Austen"))
    book_with = db.insert(Book(title="Pride and Prejudice", author=author))
    book_without = db.insert(Book(title="Anonymous Work", author=None))

    book1 = db.get(Book, book_with.pk)
    book2 = db.get(Book, book_without.pk)

    if book1 is not None:
        author_name = book1.author.name if book1.author else "None"
        output.write(f"'{book1.title}' author: {author_name}\n")
    if book2 is not None:
        output.write(f"'{book2.title}' author: {book2.author}\n")

    output.write("\nOptional[Author] auto-sets null=True on the FK column\n")

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
    reverse_attr = "books"  # Dynamic attribute added by FK descriptor
    books_query = getattr(author, reverse_attr)
    books = books_query.fetch_all()
    for book in books:
        output.write(f"  - {book.title}\n")

    output.write(f"\nTotal books: {len(books)}\n")
    output.write("Reverse relationships auto-generated from FKs\n")

    db.close()
    return output.getvalue()


def _run_select_related_basic() -> str:
    """Demonstrate eager loading with select_related().

    Shows how select_related() fetches related objects in a single JOIN query
    instead of lazy loading (which causes N+1 queries).
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

    # Insert test data
    author1 = db.insert(Author(name="Jane Austen"))
    author2 = db.insert(Author(name="Charles Dickens"))

    db.insert(Book(title="Pride and Prejudice", author=author1))
    db.insert(Book(title="Emma", author=author1))
    db.insert(Book(title="Oliver Twist", author=author2))

    # Eager load - single JOIN query
    output.write("Fetching books with eager loading:\n")
    books = db.select(Book).select_related("author").fetch_all()

    for book in books:
        output.write(f"  '{book.title}' by {book.author.name}\n")

    output.write("\nAll authors loaded in single query (no N+1 problem)\n")

    db.close()
    return output.getvalue()


def _run_select_related_nested() -> str:
    """Demonstrate nested relationship eager loading.

    Shows how to load nested relationships using double underscore syntax:
    select_related("book__author") loads both Book and Author in one query.
    """
    output = io.StringIO()

    class Author(BaseDBModel):
        name: str

    class Book(BaseDBModel):
        title: str
        author: ForeignKey[Author] = ForeignKey(Author)

    class Comment(BaseDBModel):
        text: str
        book: ForeignKey[Book] = ForeignKey(Book)

    db = SqliterDB(memory=True)
    db.create_table(Author)
    db.create_table(Book)
    db.create_table(Comment)

    # Insert nested test data
    author = db.insert(Author(name="Jane Austen"))
    book = db.insert(Book(title="Pride and Prejudice", author=author))
    db.insert(Comment(text="Amazing book!", book=book))

    # Load nested relationship - single query joins Comment -> Book -> Author
    output.write("Loading nested relationships:\n")
    comment = db.select(Comment).select_related("book__author").fetch_one()

    if comment is not None:
        output.write(f"Comment: {comment.text}\n")
        output.write(f"Book: {comment.book.title}\n")
        # Access author through book's foreign key relationship
        # Both book and author were loaded in a single JOIN query
        output.write(f"Author: {comment.book.author.name}\n")

    output.write("\nNested relationships loaded in single query\n")

    db.close()
    return output.getvalue()


def _run_relationship_filter_traversal() -> str:
    """Demonstrate relationship filter traversal.

    Shows how to filter by fields on related models using double underscore
    syntax: filter(author__name="Jane Austen")
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

    # Insert test data
    author1 = db.insert(Author(name="Jane Austen"))
    author2 = db.insert(Author(name="Charles Dickens"))

    db.insert(Book(title="Pride and Prejudice", author=author1))
    db.insert(Book(title="Emma", author=author1))
    db.insert(Book(title="Oliver Twist", author=author2))
    db.insert(Book(title="Great Expectations", author=author2))

    # Filter by related field
    output.write("Filtering by author name:\n")
    books = db.select(Book).filter(author__name="Jane Austen").fetch_all()

    for book in books:
        output.write(f"  {book.title}\n")

    output.write(f"\nFound {len(books)} book(s) by Jane Austen\n")
    output.write("(Automatic JOIN added behind the scenes)\n")

    db.close()
    return output.getvalue()


def _run_select_related_combined() -> str:
    """Demonstrate combining select_related() with relationship filters.

    Shows how to use select_related() with filter() for optimal performance:
    load related objects AND filter by them in a single query.
    """
    output = io.StringIO()

    class Author(BaseDBModel):
        name: str

    class Book(BaseDBModel):
        title: str
        year: int
        author: ForeignKey[Author] = ForeignKey(Author)

    db = SqliterDB(memory=True)
    db.create_table(Author)
    db.create_table(Book)

    # Insert test data
    author1 = db.insert(Author(name="Jane Austen"))
    author2 = db.insert(Author(name="Charles Dickens"))

    db.insert(Book(title="Pride and Prejudice", year=1813, author=author1))
    db.insert(Book(title="Emma", year=1815, author=author1))
    db.insert(Book(title="Oliver Twist", year=1838, author=author2))

    # Combine filter + eager load
    output.write("Filter and eager load in single query:\n")
    books = (
        db.select(Book)
        .select_related("author")
        .filter(author__name__startswith="Jane")
        .fetch_all()
    )

    for book in books:
        output.write(f"  {book.title} ({book.year}) by {book.author.name}\n")

    output.write(f"\n{len(books)} result(s) with authors preloaded\n")

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
                id="orm_nullable_fk",
                title="Nullable Foreign Keys",
                description="Auto-detect nullable FKs from annotations",
                category="orm",
                code=extract_demo_code(_run_nullable_foreign_key),
                execute=_run_nullable_foreign_key,
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
            Demo(
                id="orm_select_related",
                title="Eager Loading with select_related()",
                description="Fetch related objects in a single JOIN query",
                category="orm",
                code=extract_demo_code(_run_select_related_basic),
                execute=_run_select_related_basic,
            ),
            Demo(
                id="orm_select_related_nested",
                title="Nested Relationship Loading",
                description="Load nested relationships with double underscore",
                category="orm",
                code=extract_demo_code(_run_select_related_nested),
                execute=_run_select_related_nested,
            ),
            Demo(
                id="orm_filter_traversal",
                title="Relationship Filter Traversal",
                description="Filter by related object fields",
                category="orm",
                code=extract_demo_code(_run_relationship_filter_traversal),
                execute=_run_relationship_filter_traversal,
            ),
            Demo(
                id="orm_select_related_combined",
                title="Combining select_related with Filters",
                description="Eager load and filter by relationships",
                category="orm",
                code=extract_demo_code(_run_select_related_combined),
                execute=_run_select_related_combined,
            ),
        ],
    )
