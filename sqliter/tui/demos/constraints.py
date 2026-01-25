"""Unique & Foreign Key constraint demos."""

from __future__ import annotations

import io
from typing import Annotated, Optional

from sqliter import SqliterDB
from sqliter.model import BaseDBModel
from sqliter.model.unique import unique
from sqliter.orm.foreign_key import ForeignKey
from sqliter.tui.demos.base import Demo, DemoCategory, extract_demo_code


def _run_unique_field() -> str:
    """Enforce uniqueness on a field to prevent duplicate values.

    Use unique() to ensure no two records have the same value for
    a specific field (like email).
    """
    output = io.StringIO()

    class User(BaseDBModel):
        email: Annotated[str, unique()]
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
    """Enforce uniqueness on multiple fields.

    Each unique() field is constrained independently (not a composite
    unique constraint).
    """
    output = io.StringIO()

    class Enrollment(BaseDBModel):
        student_id: Annotated[int, unique()]
        course_id: Annotated[int, unique()]

    db = SqliterDB(memory=True)
    db.create_table(Enrollment)

    output.write("Table created with unique fields (each column independent)\n")
    enrollment = db.insert(Enrollment(student_id=1, course_id=101))
    output.write(
        f"Enrolled student {enrollment.student_id} in course "
        f"{enrollment.course_id}\n"
    )

    db.close()
    return output.getvalue()


def _run_foreign_key_cascade() -> str:
    """Automatically delete related records when parent is deleted.

    CASCADE on_delete means deleting a record also deletes all
    records that reference it via foreign key.
    """
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
    """Prevent deletion of records that are referenced by others.

    RESTRICT on_delete prevents deleting a record if other records
    reference it via foreign key.
    """
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
    """Set foreign key to NULL when referenced record is deleted.

    SET NULL on_delete sets the foreign key field to None when the
    referenced record is deleted (requires nullable FK).
    """
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
                code=extract_demo_code(_run_unique_field),
                execute=_run_unique_field,
            ),
            Demo(
                id="constraint_multi_unique",
                title="Multiple Unique Fields",
                description="Multiple unique fields in one table",
                category="constraints",
                code=extract_demo_code(_run_multi_field_unique),
                execute=_run_multi_field_unique,
            ),
            Demo(
                id="constraint_fk_cascade",
                title="Foreign Key CASCADE",
                description="Cascade deletes to related records",
                category="constraints",
                code=extract_demo_code(_run_foreign_key_cascade),
                execute=_run_foreign_key_cascade,
            ),
            Demo(
                id="constraint_fk_restrict",
                title="Foreign Key RESTRICT",
                description="Prevent deletion of referenced records",
                category="constraints",
                code=extract_demo_code(_run_foreign_key_restrict),
                execute=_run_foreign_key_restrict,
            ),
            Demo(
                id="constraint_fk_set_null",
                title="Foreign Key SET NULL",
                description="Set field to NULL on reference deletion",
                category="constraints",
                code=extract_demo_code(_run_foreign_key_set_null),
                execute=_run_foreign_key_set_null,
            ),
        ],
    )
