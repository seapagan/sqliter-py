"""ORM Features demos."""

from __future__ import annotations

import io

from sqliter import SqliterDB
from sqliter.model import BaseDBModel
from sqliter.tui.demos.base import Demo, DemoCategory


def _run_lazy_loading() -> str:
    """Execute the lazy loading demo."""
    output = io.StringIO()

    class Author(BaseDBModel):
        name: str

    class Book(BaseDBModel):
        title: str
        author_id: int

    db = SqliterDB(memory=True)
    db.create_table(Author)
    db.create_table(Book)

    author = db.insert(Author(name="J.K. Rowling"))
    db.insert(Book(title="Harry Potter 1", author_id=author.pk))
    db.insert(Book(title="Harry Potter 2", author_id=author.pk))

    output.write(f"Author: {author.name}\n")
    output.write(f"Author ID: {author.pk}\n")
    output.write("Access related books using LazyLoader when needed\n")

    db.close()
    return output.getvalue()


def _run_orm_style_access() -> str:
    """Execute the ORM-style access demo."""
    output = io.StringIO()

    class User(BaseDBModel):
        name: str
        email: str

    db = SqliterDB(memory=True)
    db.create_table(User)

    user = db.insert(User(name="Alice", email="alice@example.com"))
    output.write("Created user:\n")
    output.write(f"  name: {user.name}\n")
    output.write(f"  email: {user.email}\n")
    output.write(f"  pk: {user.pk}\n")
    output.write("\nAccess fields like object attributes\n")

    db.close()
    return output.getvalue()


def _run_relationship_navigation() -> str:
    """Execute the relationship navigation demo."""
    output = io.StringIO()

    class Team(BaseDBModel):
        name: str

    class Player(BaseDBModel):
        name: str
        team_id: int

    db = SqliterDB(memory=True)
    db.create_table(Team)
    db.create_table(Player)

    team = db.insert(Team(name="Lakers"))
    player1 = db.insert(Player(name="LeBron", team_id=team.pk))
    player2 = db.insert(Player(name="Davis", team_id=team.pk))

    output.write(f"Team: {team.name}\n")
    output.write(f"Players: {player1.name}, {player2.name}\n")
    output.write("\nNavigate relationships using foreign keys\n")

    db.close()
    return output.getvalue()


LAZY_LOADING_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Author(BaseDBModel):
    name: str

class Book(BaseDBModel):
    title: str
    author_id: int

db = SqliterDB(memory=True)
db.create_table(Author)
db.create_table(Book)

author = db.insert(Author(name="J.K. Rowling"))
db.insert(Book(title="Harry Potter 1", author_id=author.pk))

# Access related data through foreign keys
"""

ORM_ACCESS_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    name: str
    email: str

db = SqliterDB(memory=True)
db.create_table(User)

user = db.insert(User(name="Alice", email="alice@example.com"))

# Access fields as object attributes
print(user.name)
print(user.email)
print(user.pk)
"""

RELATIONSHIP_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Team(BaseDBModel):
    name: str

class Player(BaseDBModel):
    name: str
    team_id: int

db = SqliterDB(memory=True)
db.create_table(Team)
db.create_table(Player)

team = db.insert(Team(name="Lakers"))
player = db.insert(Player(name="LeBron", team_id=team.pk))

# Navigate relationships via foreign key
"""


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
                code=LAZY_LOADING_CODE,
                execute=_run_lazy_loading,
            ),
            Demo(
                id="orm_access",
                title="ORM-Style Access",
                description="Access fields as object attributes",
                category="orm",
                code=ORM_ACCESS_CODE,
                execute=_run_orm_style_access,
            ),
            Demo(
                id="orm_relationships",
                title="Relationship Navigation",
                description="Navigate using foreign keys",
                category="orm",
                code=RELATIONSHIP_CODE,
                execute=_run_relationship_navigation,
            ),
        ],
    )
