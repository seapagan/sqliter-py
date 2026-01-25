"""Query Builder filter demos."""

from __future__ import annotations

import io
from typing import Optional

from sqliter import SqliterDB
from sqliter.model import BaseDBModel
from sqliter.tui.demos.base import Demo, DemoCategory, extract_demo_code


def _run_equals() -> str:
    """Filter records where a field exactly matches a value.

    Use __eq to find records with the specified exact value.
    """
    output = io.StringIO()

    class User(BaseDBModel):
        name: str
        age: int

    db = SqliterDB(memory=True)
    db.create_table(User)

    db.insert(User(name="Alice", age=30))
    db.insert(User(name="Bob", age=25))
    db.insert(User(name="Alice", age=35))

    results = db.select(User).filter(name__eq="Alice").fetch_all()
    output.write(f"Found {len(results)} users named 'Alice':\n")
    for user in results:
        output.write(f"  - {user.name}, age {user.age}\n")

    db.close()
    return output.getvalue()


def _run_comparison() -> str:
    """Filter records using comparison operators.

    Use __gt, __lt, __gte, __lte for greater/less than filtering.
    """
    output = io.StringIO()

    class Product(BaseDBModel):
        name: str
        price: float

    db = SqliterDB(memory=True)
    db.create_table(Product)

    db.insert(Product(name="Item A", price=10.0))
    db.insert(Product(name="Item B", price=20.0))
    db.insert(Product(name="Item C", price=30.0))

    # Greater than
    expensive = db.select(Product).filter(price__gt=15.0).fetch_all()
    output.write(f"Products > $15: {len(expensive)}\n")

    # Less than or equal
    cheap = db.select(Product).filter(price__lte=20.0).fetch_all()
    output.write(f"Products <= $20: {len(cheap)}\n")

    db.close()
    return output.getvalue()


def _run_in_operator() -> str:
    """Filter records matching any value in a list.

    Use __in to match records against multiple possible values.
    """
    output = io.StringIO()

    class Task(BaseDBModel):
        title: str
        status: str

    db = SqliterDB(memory=True)
    db.create_table(Task)

    db.insert(Task(title="Task 1", status="todo"))
    db.insert(Task(title="Task 2", status="done"))
    db.insert(Task(title="Task 3", status="in_progress"))
    db.insert(Task(title="Task 4", status="done"))

    results = (
        db.select(Task).filter(status__in=["todo", "in_progress"]).fetch_all()
    )
    output.write(f"Active tasks: {len(results)}\n")
    for task in results:
        output.write(f"  - {task.title}: {task.status}\n")

    db.close()
    return output.getvalue()


def _run_like_operator() -> str:
    """Filter strings using SQL LIKE pattern matching.

    Use __like with % wildcards for flexible string matching.
    """
    output = io.StringIO()

    class File(BaseDBModel):
        name: str

    db = SqliterDB(memory=True)
    db.create_table(File)

    db.insert(File(name="document.txt"))
    db.insert(File(name="image.png"))
    db.insert(File(name="data.csv"))
    db.insert(File(name="notes.txt"))

    results = db.select(File).filter(name__like="%.txt").fetch_all()
    output.write(f"Text files: {len(results)}\n")
    for file in results:
        output.write(f"  - {file.name}\n")

    db.close()
    return output.getvalue()


def _run_not_equals() -> str:
    """Filter records that don't match a specific value.

    Use __ne to exclude records with the specified value.
    """
    output = io.StringIO()

    class Item(BaseDBModel):
        name: str
        status: str

    db = SqliterDB(memory=True)
    db.create_table(Item)

    db.insert(Item(name="Item 1", status="active"))
    db.insert(Item(name="Item 2", status="archived"))
    db.insert(Item(name="Item 3", status="active"))

    results = db.select(Item).filter(status__ne="archived").fetch_all()
    output.write(f"Non-archived items: {len(results)}\n")

    db.close()
    return output.getvalue()


def _run_multiple_filters() -> str:
    """Chain multiple filters for complex queries.

    Combine multiple filter() calls to narrow results with AND logic.
    """
    output = io.StringIO()

    class User(BaseDBModel):
        name: str
        age: int
        city: str

    db = SqliterDB(memory=True)
    db.create_table(User)

    db.insert(User(name="Alice", age=30, city="NYC"))
    db.insert(User(name="Bob", age=25, city="LA"))
    db.insert(User(name="Charlie", age=30, city="NYC"))

    results = (
        db.select(User).filter(age__gte=30).filter(city__eq="NYC").fetch_all()
    )
    output.write(f"Users in NYC aged 30+: {len(results)}\n")
    for user in results:
        output.write(f"  - {user.name}, {user.age}\n")

    db.close()
    return output.getvalue()


def _run_range_filters() -> str:
    """Filter records within a specific value range.

    Combine __gte and __lte to find records in a range.
    """
    output = io.StringIO()

    class Product(BaseDBModel):
        name: str
        price: float

    db = SqliterDB(memory=True)
    db.create_table(Product)

    for i in range(1, 11):
        db.insert(Product(name=f"Product {i}", price=float(i * 10)))

    results = (
        db.select(Product)
        .filter(price__gte=30.0)
        .filter(price__lte=70.0)
        .fetch_all()
    )
    output.write(f"Products $30-$70: {len(results)}\n")

    db.close()
    return output.getvalue()


def _run_combined_operators() -> str:
    """Combine different filter types for precise queries.

    Mix equality, comparison, and other operators in a single query.
    """
    output = io.StringIO()

    class Order(BaseDBModel):
        id: str
        amount: float
        status: str

    db = SqliterDB(memory=True)
    db.create_table(Order)

    db.insert(Order(id="001", amount=100.0, status="pending"))
    db.insert(Order(id="002", amount=250.0, status="completed"))
    db.insert(Order(id="003", amount=50.0, status="pending"))
    db.insert(Order(id="004", amount=300.0, status="completed"))

    results = (
        db.select(Order)
        .filter(status__eq="pending")
        .filter(amount__gt=50.0)
        .fetch_all()
    )
    output.write(f"Pending orders > $50: {len(results)}\n")

    db.close()
    return output.getvalue()


def _run_isnull() -> str:
    """Find records with null (empty) field values.

    Use __isnull=True to find records where a field is None.
    """
    output = io.StringIO()

    class Task(BaseDBModel):
        title: str
        assigned_to: Optional[str] = None

    db = SqliterDB(memory=True)
    db.create_table(Task)

    db.insert(Task(title="Task 1", assigned_to="Alice"))
    db.insert(Task(title="Task 2", assigned_to=None))  # Unassigned
    db.insert(Task(title="Task 3", assigned_to="Bob"))
    db.insert(Task(title="Task 4", assigned_to=None))  # Unassigned

    # Find unassigned tasks
    unassigned = db.select(Task).filter(assigned_to__isnull=True).fetch_all()
    output.write(f"Unassigned tasks: {len(unassigned)}\n")
    for task in unassigned:
        output.write(f"  - {task.title}\n")

    db.close()
    return output.getvalue()


def _run_notnull() -> str:
    """Find records without null (empty) field values.

    Use __notnull=True to find records where a field has a value.
    """
    output = io.StringIO()

    class Task(BaseDBModel):
        title: str
        assigned_to: Optional[str] = None

    db = SqliterDB(memory=True)
    db.create_table(Task)

    db.insert(Task(title="Task 1", assigned_to="Alice"))
    db.insert(Task(title="Task 2", assigned_to=None))
    db.insert(Task(title="Task 3", assigned_to="Bob"))
    db.insert(Task(title="Task 4", assigned_to=None))

    # Find assigned tasks
    assigned = db.select(Task).filter(assigned_to__notnull=True).fetch_all()
    output.write(f"Assigned tasks: {len(assigned)}\n")
    for task in assigned:
        output.write(f"  - {task.title}: {task.assigned_to}\n")

    db.close()
    return output.getvalue()


def get_category() -> DemoCategory:
    """Get the Query Filters demo category."""
    return DemoCategory(
        id="filters",
        title="Query Filters",
        icon="",
        demos=[
            Demo(
                id="filter_eq",
                title="Equals (__eq)",
                description="Exact match filter",
                category="filters",
                code=extract_demo_code(_run_equals),
                execute=_run_equals,
            ),
            Demo(
                id="filter_comparison",
                title="Comparison Operators",
                description="__gt, __lt, __gte, __lte (less/greater than)",
                category="filters",
                code=extract_demo_code(_run_comparison),
                execute=_run_comparison,
            ),
            Demo(
                id="filter_in",
                title="IN Operator (__in)",
                description="Match against list of values",
                category="filters",
                code=extract_demo_code(_run_in_operator),
                execute=_run_in_operator,
            ),
            Demo(
                id="filter_like",
                title="LIKE Operator (__like)",
                description="Pattern matching with wildcards",
                category="filters",
                code=extract_demo_code(_run_like_operator),
                execute=_run_like_operator,
            ),
            Demo(
                id="filter_ne",
                title="Not Equals (__ne)",
                description="Exclude specific values",
                category="filters",
                code=extract_demo_code(_run_not_equals),
                execute=_run_not_equals,
            ),
            Demo(
                id="filter_multiple",
                title="Multiple Filters",
                description="Chain filters for AND logic",
                category="filters",
                code=extract_demo_code(_run_multiple_filters),
                execute=_run_multiple_filters,
            ),
            Demo(
                id="filter_range",
                title="Range Queries",
                description="Query within a value range",
                category="filters",
                code=extract_demo_code(_run_range_filters),
                execute=_run_range_filters,
            ),
            Demo(
                id="filter_combined",
                title="Combined Operators",
                description="Multiple filter types together",
                category="filters",
                code=extract_demo_code(_run_combined_operators),
                execute=_run_combined_operators,
            ),
            Demo(
                id="filter_isnull",
                title="IS NULL (__isnull)",
                description="Find records with null values",
                category="filters",
                code=extract_demo_code(_run_isnull),
                execute=_run_isnull,
            ),
            Demo(
                id="filter_notnull",
                title="IS NOT NULL (__notnull)",
                description="Find records without null values",
                category="filters",
                code=extract_demo_code(_run_notnull),
                execute=_run_notnull,
            ),
        ],
    )
