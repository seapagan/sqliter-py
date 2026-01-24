"""Unique & Foreign Key constraint demos."""

from __future__ import annotations

import io
from typing import Optional

from sqliter import SqliterDB
from sqliter.model import BaseDBModel
from sqliter.model.unique import unique
from sqliter.orm.foreign_key import ForeignKey
from sqliter.tui.demos.base import Demo, DemoCategory


def _run_unique_field() -> str:
    """Execute the unique field demo."""
    output = io.StringIO()

    class User(BaseDBModel):
        email: str = unique()
        name: str

    db = SqliterDB(memory=True)
    db.create_table(User)

    user1 = db.insert(User(email="alice@example.com", name="Alice"))
    output.write(f"Created: {user1.name} ({user1.email})\n")

    user2 = db.insert(User(email="bob@example.com", name="Bob"))
    output.write(f"Created: {user2.name} ({user2.email})\n")

    db.close()
    return output.getvalue()


def _run_multi_field_unique() -> str:
    """Execute the composite unique key demo."""
    output = io.StringIO()

    class Enrollment(BaseDBModel):
        student_id: int = unique()
        course_id: int = unique()

    db = SqliterDB(memory=True)
    db.create_table(Enrollment)

    output.write("Table created with unique fields\n")
    enrollment = db.insert(Enrollment(student_id=1, course_id=101))
    output.write(
        f"Enrolled student {enrollment.student_id} in course "
        f"{enrollment.course_id}\n"
    )

    db.close()
    return output.getvalue()


def _run_foreign_key_cascade() -> str:
    """Execute the foreign key CASCADE demo."""
    output = io.StringIO()

    class Author(BaseDBModel):
        name: str

    class Book(BaseDBModel):
        title: str
        author_id: ForeignKey[Author] = ForeignKey(
            Author,
            on_delete="CASCADE",
            on_update="CASCADE",
            null=True,
        )

    db = SqliterDB(memory=True)
    db.create_table(Author)
    db.create_table(Book)

    author = db.insert(Author(name="Jane Austen"))
    book = db.insert(Book(title="Pride and Prejudice", author_id=author.pk))
    output.write(f"Book '{book.title}' linked to author {author.pk}\n")
    output.write("Foreign key: CASCADE on delete/update\n")

    db.close()
    return output.getvalue()


def _run_foreign_key_restrict() -> str:
    """Execute the foreign key RESTRICT demo."""
    output = io.StringIO()

    class Category(BaseDBModel):
        name: str

    class Product(BaseDBModel):
        name: str
        category_id: ForeignKey[Category] = ForeignKey(
            Category, on_delete="RESTRICT"
        )

    db = SqliterDB(memory=True)
    db.create_table(Category)
    db.create_table(Product)

    category = db.insert(Category(name="Electronics"))
    product = db.insert(Product(name="Laptop", category_id=category.pk))
    output.write(f"Product '{product.name}' in category '{category.name}'\n")
    output.write(
        "Foreign key: RESTRICT prevents deletion of referenced records\n"
    )

    db.close()
    return output.getvalue()


def _run_foreign_key_set_null() -> str:
    """Execute the foreign key SET NULL demo."""
    output = io.StringIO()

    class Department(BaseDBModel):
        name: str

    class Employee(BaseDBModel):
        name: str
        department_id: Optional[ForeignKey[Department]] = ForeignKey(
            Department,
            on_delete="SET NULL",
            null=True,
        )

    db = SqliterDB(memory=True)
    db.create_table(Department)
    db.create_table(Employee)

    dept = db.insert(Department(name="Engineering"))
    emp = db.insert(Employee(name="Alice", department_id=dept.pk))
    output.write(f"Employee '{emp.name}' in department {emp.department_id}\n")
    output.write("Foreign key: SET NULL on delete of referenced record\n")

    db.close()
    return output.getvalue()


UNIQUE_FIELD_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel
from sqliter.model.unique import unique

class User(BaseDBModel):
    email: str = unique()
    name: str

db = SqliterDB(memory=True)
db.create_table(User)

# Each email must be unique
user1 = db.insert(User(email="alice@example.com", name="Alice"))
user2 = db.insert(User(email="bob@example.com", name="Bob"))

# Duplicate email will raise error
# user3 = db.insert(User(email="alice@example.com", name="Carol"))
"""

MULTI_UNIQUE_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel
from sqliter.model.unique import unique

class Enrollment(BaseDBModel):
    student_id: int = unique()
    course_id: int = unique()

db = SqliterDB(memory=True)
db.create_table(Enrollment)

# Each field is unique individually
enrollment = db.insert(Enrollment(student_id=1, course_id=101))
"""

FK_CASCADE_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel
from sqliter.orm.foreign_key import ForeignKey

class Author(BaseDBModel):
    name: str

class Book(BaseDBModel):
    title: str
    author_id: ForeignKey[Author] = ForeignKey(
        Author,
        on_delete="CASCADE",
        on_update="CASCADE",
        null=True,
    )

db = SqliterDB(memory=True)
db.create_table(Author)
db.create_table(Book)

# Deleting author will delete their books
"""

FK_RESTRICT_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel
from sqliter.orm.foreign_key import ForeignKey

class Category(BaseDBModel):
    name: str

class Product(BaseDBModel):
    name: str
    category_id: ForeignKey[Category] = ForeignKey(
        Category, on_delete="RESTRICT"
    )

db = SqliterDB(memory=True)
db.create_table(Category)
db.create_table(Product)

# Cannot delete category if products reference it
"""

FK_SET_NULL_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel
from sqliter.orm.foreign_key import ForeignKey

class Department(BaseDBModel):
    name: str

class Employee(BaseDBModel):
    name: str
    department_id: Optional[int] = ForeignKey(
        Department,
        on_delete="SET NULL",
        null=True,
    )

db = SqliterDB(memory=True)
db.create_table(Department)
db.create_table(Employee)

# Deleting department sets employee.department_id to NULL
"""


def get_category() -> DemoCategory:
    """Get the Constraints demo category."""
    return DemoCategory(
        id="constraints",
        title="Constraints",
        icon="",
        demos=[
            Demo(
                id="constraint_unique_field",
                title="Unique Field",
                description="Enforce uniqueness on a field",
                category="constraints",
                code=UNIQUE_FIELD_CODE,
                execute=_run_unique_field,
            ),
            Demo(
                id="constraint_multi_unique",
                title="Multiple Unique Fields",
                description="Multiple unique fields in one table",
                category="constraints",
                code=MULTI_UNIQUE_CODE,
                execute=_run_multi_field_unique,
            ),
            Demo(
                id="constraint_fk_cascade",
                title="Foreign Key CASCADE",
                description="Cascade deletes to related records",
                category="constraints",
                code=FK_CASCADE_CODE,
                execute=_run_foreign_key_cascade,
            ),
            Demo(
                id="constraint_fk_restrict",
                title="Foreign Key RESTRICT",
                description="Prevent deletion of referenced records",
                category="constraints",
                code=FK_RESTRICT_CODE,
                execute=_run_foreign_key_restrict,
            ),
            Demo(
                id="constraint_fk_set_null",
                title="Foreign Key SET NULL",
                description="Set field to NULL on reference deletion",
                category="constraints",
                code=FK_SET_NULL_CODE,
                execute=_run_foreign_key_set_null,
            ),
        ],
    )
