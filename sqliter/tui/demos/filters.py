"""Query Builder filter demos."""

from __future__ import annotations

import io

from sqliter.tui.demos.base import Demo, DemoCategory


def _run_equals() -> str:
    """Execute the equals filter demo."""
    output = io.StringIO()

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel

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
    """Execute the comparison operators demo."""
    output = io.StringIO()

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel

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
    cheap = db.select(Product).filter(price__le=20.0).fetch_all()
    output.write(f"Products <= $20: {len(cheap)}\n")

    db.close()
    return output.getvalue()


def _run_in_operator() -> str:
    """Execute the IN operator demo."""
    output = io.StringIO()

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel

    class Task(BaseDBModel):
        title: str
        status: str

    db = SqliterDB(memory=True)
    db.create_table(Task)

    db.insert(Task(title="Task 1", status="todo"))
    db.insert(Task(title="Task 2", status="done"))
    db.insert(Task(title="Task 3", status="in_progress"))
    db.insert(Task(title="Task 4", status="done"))

    results = db.select(Task).filter(status__in=["todo", "in_progress"]).fetch_all()
    output.write(f"Active tasks: {len(results)}\n")
    for task in results:
        output.write(f"  - {task.title}: {task.status}\n")

    db.close()
    return output.getvalue()


def _run_like_operator() -> str:
    """Execute the LIKE operator demo."""
    output = io.StringIO()

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel

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
    """Execute the not equals demo."""
    output = io.StringIO()

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel

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
    """Execute multiple filters demo."""
    output = io.StringIO()

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel

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
        db.select(User)
        .filter(age__gte=30)
        .filter(city__eq="NYC")
        .fetch_all()
    )
    output.write(f"Users in NYC aged 30+: {len(results)}\n")
    for user in results:
        output.write(f"  - {user.name}, {user.age}\n")

    db.close()
    return output.getvalue()


def _run_range_filters() -> str:
    """Execute range filter demo."""
    output = io.StringIO()

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel

    class Product(BaseDBModel):
        name: str
        price: float

    db = SqliterDB(memory=True)
    db.create_table(Product)

    for i in range(1, 11):
        db.insert(Product(name=f"Product {i}", price=float(i * 10)))

    results = db.select(Product).filter(price__gte=30.0).filter(price__lte=70.0).fetch_all()
    output.write(f"Products $30-$70: {len(results)}\n")

    db.close()
    return output.getvalue()


def _run_combined_operators() -> str:
    """Execute combined filter operators demo."""
    output = io.StringIO()

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel

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


EQUALS_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    name: str
    age: int

db = SqliterDB(memory=True)
db.create_table(User)

# Find users named 'Alice'
results = db.select(User).filter(name__eq="Alice").fetch_all()
for user in results:
    print(user.name, user.age)
"""

COMPARISON_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Product(BaseDBModel):
    name: str
    price: float

db = SqliterDB(memory=True)
db.create_table(Product)

# Greater than: price > 15
expensive = db.select(Product).filter(price__gt=15.0).fetch_all()

# Less than or equal: price <= 20
cheap = db.select(Product).filter(price__le=20.0).fetch_all()
"""

IN_OPERATOR_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Task(BaseDBModel):
    title: str
    status: str

db = SqliterDB(memory=True)
db.create_table(Task)

# Find tasks in specific statuses
results = db.select(Task).filter(
    status__in=["todo", "in_progress"]
).fetch_all()
"""

LIKE_OPERATOR_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class File(BaseDBModel):
    name: str

db = SqliterDB(memory=True)
db.create_table(File)

# Find files ending in .txt
# Use % as wildcard
results = db.select(File).filter(name__like="%.txt").fetch_all()
"""

NOT_EQUALS_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Item(BaseDBModel):
    name: str
    status: str

db = SqliterDB(memory=True)
db.create_table(Item)

# Find items not archived
results = db.select(Item).filter(status__ne="archived").fetch_all()
"""

MULTIPLE_FILTERS_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    name: str
    age: int
    city: str

db = SqliterDB(memory=True)
db.create_table(User)

# Chain multiple filters (AND logic)
results = (
    db.select(User)
    .filter(age__gte=30)
    .filter(city__eq="NYC")
    .fetch_all()
)
"""

RANGE_FILTERS_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Product(BaseDBModel):
    name: str
    price: float

db = SqliterDB(memory=True)
db.create_table(Product)

# Range query: price between 30 and 70
results = (
    db.select(Product)
    .filter(price__gte=30.0)
    .filter(price__lte=70.0)
    .fetch_all()
)
"""

COMBINED_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Order(BaseDBModel):
    id: str
    amount: float
    status: str

db = SqliterDB(memory=True)
db.create_table(Order)

# Combine status and amount filters
results = (
    db.select(Order)
    .filter(status__eq="pending")
    .filter(amount__gt=50.0)
    .fetch_all()
)
"""


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
                code=EQUALS_CODE,
                execute=_run_equals,
            ),
            Demo(
                id="filter_comparison",
                title="Comparison Operators",
                description="__gt, __lt, __gte, __lte",
                category="filters",
                code=COMPARISON_CODE,
                execute=_run_comparison,
            ),
            Demo(
                id="filter_in",
                title="IN Operator (__in)",
                description="Match against list of values",
                category="filters",
                code=IN_OPERATOR_CODE,
                execute=_run_in_operator,
            ),
            Demo(
                id="filter_like",
                title="LIKE Operator (__like)",
                description="Pattern matching with wildcards",
                category="filters",
                code=LIKE_OPERATOR_CODE,
                execute=_run_like_operator,
            ),
            Demo(
                id="filter_ne",
                title="Not Equals (__ne)",
                description="Exclude specific values",
                category="filters",
                code=NOT_EQUALS_CODE,
                execute=_run_not_equals,
            ),
            Demo(
                id="filter_multiple",
                title="Multiple Filters",
                description="Chain filters for AND logic",
                category="filters",
                code=MULTIPLE_FILTERS_CODE,
                execute=_run_multiple_filters,
            ),
            Demo(
                id="filter_range",
                title="Range Queries",
                description="Query within a value range",
                category="filters",
                code=RANGE_FILTERS_CODE,
                execute=_run_range_filters,
            ),
            Demo(
                id="filter_combined",
                title="Combined Operators",
                description="Multiple filter types together",
                category="filters",
                code=COMBINED_CODE,
                execute=_run_combined_operators,
            ),
        ],
    )
