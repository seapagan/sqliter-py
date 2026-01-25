"""Field Selection demos."""

from __future__ import annotations

import io

from sqliter import SqliterDB
from sqliter.model import BaseDBModel
from sqliter.tui.demos.base import Demo, DemoCategory, extract_demo_code


def _run_select_fields() -> str:
    """Select specific fields from a query to reduce data transfer.

    Use fields() to fetch only the columns you need, leaving unspecified
    fields as None.
    """
    output = io.StringIO()

    class User(BaseDBModel):
        name: str
        email: str
        age: int
        city: str

    db = SqliterDB(memory=True)
    db.create_table(User)

    db.insert(User(name="Alice", email="alice@example.com", age=30, city="NYC"))
    db.insert(User(name="Bob", email="bob@example.com", age=25, city="LA"))

    # Select only name and email
    users = db.select(User).fields(["name", "email"]).fetch_all()
    output.write("Selected only name and email fields:\n")
    for user in users:
        output.write(f"  - {user.name}, {user.email}\n")

    # Note: age and city are None since they weren't selected
    output.write("(age and city not selected, set to None)\n")

    db.close()
    return output.getvalue()


def _run_exclude_fields() -> str:
    """Exclude specific fields from query results.

    Use exclude() to fetch all fields except the ones you specify,
    useful for hiding large or sensitive fields.
    """
    output = io.StringIO()

    class Product(BaseDBModel):
        name: str
        price: float
        description: str
        stock: int

    db = SqliterDB(memory=True)
    db.create_table(Product)

    db.insert(
        Product(
            name="Laptop",
            price=999.99,
            description="Fast laptop",
            stock=10,
        )
    )

    # Exclude description and stock
    product = db.select(Product).exclude(["description", "stock"]).fetch_one()
    if product is not None:
        output.write(f"Product: {product.name}\n")
        output.write(f"Price: ${product.price}\n")
        output.write("(description and stock excluded)\n")

    db.close()
    return output.getvalue()


def _run_only_field() -> str:
    """Select a single field from query results.

    Use only() when you only need one specific field from your query,
    useful for getting IDs or names.
    """
    output = io.StringIO()

    class Task(BaseDBModel):
        title: str
        status: str
        priority: int
        assigned_to: str

    db = SqliterDB(memory=True)
    db.create_table(Task)

    db.insert(
        Task(title="Fix bug", status="todo", priority=1, assigned_to="Alice")
    )
    db.insert(
        Task(title="Add feature", status="done", priority=2, assigned_to="Bob")
    )

    # Select only the title field
    tasks = db.select(Task).only("title").fetch_all()
    output.write("Selected only title field:\n")
    for task in tasks:
        output.write(f"  - {task.title}\n")

    output.write("(status, priority, assigned_to not selected)\n")

    db.close()
    return output.getvalue()


def get_category() -> DemoCategory:
    """Get the Field Selection demo category."""
    return DemoCategory(
        id="field_selection",
        title="Field Selection",
        icon="",
        demos=[
            Demo(
                id="field_select",
                title="Select Fields",
                description="Choose specific fields to fetch",
                category="field_selection",
                code=extract_demo_code(_run_select_fields),
                execute=_run_select_fields,
            ),
            Demo(
                id="field_exclude",
                title="Exclude Fields",
                description="Exclude specific fields from results",
                category="field_selection",
                code=extract_demo_code(_run_exclude_fields),
                execute=_run_exclude_fields,
            ),
            Demo(
                id="field_only",
                title="Select Single Field",
                description="Fetch only one specific field",
                category="field_selection",
                code=extract_demo_code(_run_only_field),
                execute=_run_only_field,
            ),
        ],
    )
