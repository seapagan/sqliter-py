"""Query Results & Aggregation demos."""

from __future__ import annotations

import io

from sqliter.tui.demos.base import Demo, DemoCategory


def _run_fetch_all() -> str:
    """Execute the fetch_all demo."""
    output = io.StringIO()

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel

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
    """Execute the fetch_one demo."""
    output = io.StringIO()

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel

    class Task(BaseDBModel):
        title: str
        priority: int

    db = SqliterDB(memory=True)
    db.create_table(Task)

    db.insert(Task(title="High priority", priority=1))
    db.insert(Task(title="Medium priority", priority=2))
    db.insert(Task(title="Low priority", priority=3))

    task = db.select(Task).filter(priority__eq=1).fetch_one()
    output.write(f"Single result: {task.title}\n")

    db.close()
    return output.getvalue()


def _run_fetch_first_last() -> str:
    """Execute the fetch_first and fetch_last demo."""
    output = io.StringIO()

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel

    class Item(BaseDBModel):
        name: str

    db = SqliterDB(memory=True)
    db.create_table(Item)

    for name in ["Alpha", "Beta", "Gamma", "Delta"]:
        db.insert(Item(name=name))

    first = db.select(Item).fetch_first()
    output.write(f"First: {first.name}\n")

    last = db.select(Item).fetch_last()
    output.write(f"Last: {last.name}\n")

    db.close()
    return output.getvalue()


def _run_count() -> str:
    """Execute the count demo."""
    output = io.StringIO()

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel

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
    """Execute the exists demo."""
    output = io.StringIO()

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel

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
    """Execute aggregate functions demo."""
    output = io.StringIO()

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel

    class Sale(BaseDBModel):
        amount: float

    db = SqliterDB(memory=True)
    db.create_table(Sale)

    for amount in [10.0, 20.0, 30.0, 40.0, 50.0]:
        db.insert(Sale(amount=amount))

    results = db.select(Sale).fetch_all()
    total = sum(s.amount for s in results)
    average = total / len(results)
    output.write(f"Total sales: ${total:.2f}\n")
    output.write(f"Average sale: ${average:.2f}\n")
    output.write(f"Count: {len(results)}\n")

    db.close()
    return output.getvalue()


FETCH_ALL_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    name: str
    age: int

db = SqliterDB(memory=True)
db.create_table(User)

# Get all records
results = db.select(User).fetch_all()

for user in results:
    print(user.name, user.age)
"""

FETCH_ONE_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Task(BaseDBModel):
    title: str
    priority: int

db = SqliterDB(memory=True)
db.create_table(Task)

# Get single record (or None)
task = (
    db.select(Task)
    .filter(priority__eq=1)
    .fetch_one()
)

if task:
    print(task.title)
"""

FETCH_FIRST_LAST_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Item(BaseDBModel):
    name: str

db = SqliterDB(memory=True)
db.create_table(Item)

# Get first record
first = db.select(Item).fetch_first()

# Get last record
last = db.select(Item).fetch_last()

print(f"First: {first.name}")
print(f"Last: {last.name}")
"""

COUNT_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Product(BaseDBModel):
    name: str
    category: str

db = SqliterDB(memory=True)
db.create_table(Product)

# Count all records
total = db.select(Product).count()

# Count with filter
count = (
    db.select(Product)
    .filter(category__eq="electronics")
    .count()
)
"""

EXISTS_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    username: str

db = SqliterDB(memory=True)
db.create_table(User)

# Check if record exists
exists = (
    db.select(User)
    .filter(username__eq="alice")
    .exists()
)

print(f"User exists: {exists}")
"""

AGGREGATES_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Sale(BaseDBModel):
    amount: float

db = SqliterDB(memory=True)
db.create_table(Sale)

results = db.select(Sale).fetch_all()

# Calculate aggregates in Python
total = sum(s.amount for s in results)
average = total / len(results)

print(f"Total: ${total}")
print(f"Average: ${average}")
"""


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
                code=FETCH_ALL_CODE,
                execute=_run_fetch_all,
            ),
            Demo(
                id="result_fetch_one",
                title="Fetch One",
                description="Get single record or None",
                category="results",
                code=FETCH_ONE_CODE,
                execute=_run_fetch_one,
            ),
            Demo(
                id="result_first_last",
                title="Fetch First/Last",
                description="Get first or last record",
                category="results",
                code=FETCH_FIRST_LAST_CODE,
                execute=_run_fetch_first_last,
            ),
            Demo(
                id="result_count",
                title="Count",
                description="Count matching records",
                category="results",
                code=COUNT_CODE,
                execute=_run_count,
            ),
            Demo(
                id="result_exists",
                title="Exists",
                description="Check if any records match",
                category="results",
                code=EXISTS_CODE,
                execute=_run_exists,
            ),
            Demo(
                id="result_aggregates",
                title="Aggregates",
                description="Calculate sum, average, etc.",
                category="results",
                code=AGGREGATES_CODE,
                execute=_run_aggregates,
            ),
        ],
    )
