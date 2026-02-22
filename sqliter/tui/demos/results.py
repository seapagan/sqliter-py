"""Query Results & Aggregation demos."""

from __future__ import annotations

import io

from sqliter import SqliterDB
from sqliter.exceptions import InvalidProjectionError
from sqliter.model import BaseDBModel
from sqliter.query import func
from sqliter.tui.demos.base import Demo, DemoCategory, extract_demo_code


def _run_fetch_all() -> str:
    """Fetch all records matching a query.

    Use fetch_all() to get a list of all matching records.
    """
    output = io.StringIO()

    class User(BaseDBModel):
        name: str
        age: int

    db = SqliterDB(memory=True)
    db.create_table(User)

    for i in range(5):
        db.insert(User(name=f"User {i}", age=20 + i))

    results = db.select(User).fetch_all()
    output.write(f"Total users: {len(results)}\n")
    for user in results:
        output.write(f"  - {user.name}, age {user.age}\n")

    db.close()
    return output.getvalue()


def _run_fetch_one() -> str:
    """Fetch a single record or return None if not found.

    Use fetch_one() to get one matching record, returning None if
    no records match the query.
    """
    output = io.StringIO()

    class Task(BaseDBModel):
        title: str
        priority: int

    db = SqliterDB(memory=True)
    db.create_table(Task)

    db.insert(Task(title="High priority", priority=1))
    db.insert(Task(title="Medium priority", priority=2))
    db.insert(Task(title="Low priority", priority=3))

    task = db.select(Task).filter(priority__eq=1).fetch_one()
    if task is not None:
        output.write(f"Single result: {task.title}\n")

    # Also test no results case
    no_task = db.select(Task).filter(priority__eq=999).fetch_one()
    if no_task is None:
        output.write("No task found with priority 999\n")

    db.close()
    return output.getvalue()


def _run_fetch_first_last() -> str:
    """Fetch the first or last record from results.

    Use fetch_first() or fetch_last() to get a single record
    from the beginning or end of the result set.
    """
    output = io.StringIO()

    class Item(BaseDBModel):
        name: str

    db = SqliterDB(memory=True)
    db.create_table(Item)

    for name in ["Alpha", "Beta", "Gamma", "Delta"]:
        db.insert(Item(name=name))

    first = db.select(Item).fetch_first()
    if first is not None:
        output.write(f"First: {first.name}\n")

    last = db.select(Item).fetch_last()
    if last is not None:
        output.write(f"Last: {last.name}\n")

    db.close()
    return output.getvalue()


def _run_count() -> str:
    """Count the number of matching records.

    Use count() to efficiently count records without fetching them.
    """
    output = io.StringIO()

    class Product(BaseDBModel):
        name: str
        category: str

    db = SqliterDB(memory=True)
    db.create_table(Product)

    db.insert(Product(name="Laptop", category="electronics"))
    db.insert(Product(name="Phone", category="electronics"))
    db.insert(Product(name="Desk", category="furniture"))

    total = db.select(Product).count()
    output.write(f"Total products: {total}\n")

    electronics = db.select(Product).filter(category__eq="electronics").count()
    output.write(f"Electronics: {electronics}\n")

    db.close()
    return output.getvalue()


def _run_exists() -> str:
    """Check if any records match the query.

    Use exists() to efficiently check for matching records without
    fetching them - returns True/False.
    """
    output = io.StringIO()

    class User(BaseDBModel):
        username: str

    db = SqliterDB(memory=True)
    db.create_table(User)

    db.insert(User(username="alice"))
    db.insert(User(username="bob"))

    exists = db.select(User).filter(username__eq="alice").exists()
    output.write(f"User 'alice' exists: {exists}\n")

    not_exists = db.select(User).filter(username__eq="charlie").exists()
    output.write(f"User 'charlie' exists: {not_exists}\n")

    db.close()
    return output.getvalue()


def _run_aggregates() -> str:
    """Calculate grouped aggregates using SQL projection queries."""
    output = io.StringIO()

    class Sale(BaseDBModel):
        category: str
        amount: float

    db = SqliterDB(memory=True)
    db.create_table(Sale)

    db.insert(Sale(category="books", amount=10.0))
    db.insert(Sale(category="books", amount=15.0))
    db.insert(Sale(category="games", amount=40.0))
    db.insert(Sale(category="games", amount=5.0))

    grouped = (
        db.select(Sale)
        .group_by("category")
        .annotate(
            total=func.sum("amount"),
            average=func.avg("amount"),
            entries=func.count(),
        )
        .order("category")
        .fetch_dicts()
    )

    for row in grouped:
        output.write(
            f"{row['category']}: total=${row['total']:.2f}, "
            f"avg=${row['average']:.2f}, count={row['entries']}\n"
        )

    db.close()
    return output.getvalue()


def _run_group_by_only() -> str:
    """Group rows without aggregates using projection results."""
    output = io.StringIO()

    class Sale(BaseDBModel):
        category: str
        amount: float

    db = SqliterDB(memory=True)
    db.create_table(Sale)

    db.insert(Sale(category="books", amount=10.0))
    db.insert(Sale(category="books", amount=15.0))
    db.insert(Sale(category="games", amount=40.0))

    grouped = (
        db.select(Sale).group_by("category").order("category").fetch_dicts()
    )
    output.write("Unique categories:\n")
    for row in grouped:
        output.write(f"  - {row['category']}\n")

    db.close()
    return output.getvalue()


def _run_projection_mode_guard() -> str:
    """Show projection-mode fetch guard and correct fetch_dicts usage."""
    output = io.StringIO()

    class Sale(BaseDBModel):
        category: str
        amount: float

    db = SqliterDB(memory=True)
    db.create_table(Sale)

    db.insert(Sale(category="books", amount=10.0))
    db.insert(Sale(category="games", amount=40.0))

    query = db.select(Sale).group_by("category").order("category")

    try:
        query.fetch_all()
    except InvalidProjectionError as exc:
        output.write(f"fetch_all() blocked: {exc}\n")

    grouped = query.fetch_dicts()
    output.write(f"fetch_dicts() returned {len(grouped)} rows\n")

    db.close()
    return output.getvalue()


def get_category() -> DemoCategory:
    """Get the Query Results demo category."""
    return DemoCategory(
        id="results",
        title="Query Results",
        icon="",
        demos=[
            Demo(
                id="result_fetch_all",
                title="Fetch All",
                description="Get all matching records",
                category="results",
                code=extract_demo_code(_run_fetch_all),
                execute=_run_fetch_all,
            ),
            Demo(
                id="result_fetch_one",
                title="Fetch One",
                description="Get single record or None",
                category="results",
                code=extract_demo_code(_run_fetch_one),
                execute=_run_fetch_one,
            ),
            Demo(
                id="result_first_last",
                title="Fetch First/Last",
                description="Get first or last record",
                category="results",
                code=extract_demo_code(_run_fetch_first_last),
                execute=_run_fetch_first_last,
            ),
            Demo(
                id="result_count",
                title="Count",
                description="Count matching records",
                category="results",
                code=extract_demo_code(_run_count),
                execute=_run_count,
            ),
            Demo(
                id="result_exists",
                title="Exists",
                description="Check if any records match",
                category="results",
                code=extract_demo_code(_run_exists),
                execute=_run_exists,
            ),
            Demo(
                id="result_aggregates",
                title="Aggregates",
                description="Calculate sum, average, etc.",
                category="results",
                code=extract_demo_code(_run_aggregates),
                execute=_run_aggregates,
            ),
            Demo(
                id="result_group_by_only",
                title="Group By Only",
                description="Group rows and return distinct keys",
                category="results",
                code=extract_demo_code(_run_group_by_only),
                execute=_run_group_by_only,
            ),
            Demo(
                id="result_projection_guard",
                title="Projection Guard",
                description="Show why projection queries use fetch_dicts()",
                category="results",
                code=extract_demo_code(_run_projection_mode_guard),
                execute=_run_projection_mode_guard,
            ),
        ],
    )
