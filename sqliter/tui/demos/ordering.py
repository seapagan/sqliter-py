"""Ordering & Pagination demos."""

from __future__ import annotations

import io

from sqliter import SqliterDB
from sqliter.model import BaseDBModel
from sqliter.tui.demos.base import Demo, DemoCategory


def _run_order_asc() -> str:
    """Execute the ascending order demo."""
    output = io.StringIO()

    class User(BaseDBModel):
        name: str
        age: int

    db = SqliterDB(memory=True)
    db.create_table(User)

    db.insert(User(name="Charlie", age=35))
    db.insert(User(name="Alice", age=25))
    db.insert(User(name="Bob", age=30))

    results = db.select(User).order("age").fetch_all()
    output.write("Users ordered by age (ascending):\n")
    for user in results:
        output.write(f"  - {user.name}: {user.age}\n")

    db.close()
    return output.getvalue()


def _run_order_desc() -> str:
    """Execute the descending order demo."""
    output = io.StringIO()

    class Product(BaseDBModel):
        name: str
        price: float

    db = SqliterDB(memory=True)
    db.create_table(Product)

    db.insert(Product(name="Item A", price=10.0))
    db.insert(Product(name="Item B", price=30.0))
    db.insert(Product(name="Item C", price=20.0))

    results = db.select(Product).order("-price").fetch_all()
    output.write("Products ordered by price (descending):\n")
    for product in results:
        output.write(f"  - {product.name}: ${product.price}\n")

    db.close()
    return output.getvalue()


def _run_limit() -> str:
    """Execute the limit demo."""
    output = io.StringIO()

    class Article(BaseDBModel):
        title: str

    db = SqliterDB(memory=True)
    db.create_table(Article)

    for i in range(1, 11):
        db.insert(Article(title=f"Article {i}"))

    results = db.select(Article).limit(3).fetch_all()
    output.write("Top 3 articles:\n")
    for article in results:
        output.write(f"  - {article.title}\n")

    db.close()
    return output.getvalue()


def _run_offset() -> str:
    """Execute the offset demo."""
    output = io.StringIO()

    class Item(BaseDBModel):
        name: str

    db = SqliterDB(memory=True)
    db.create_table(Item)

    for i in range(1, 11):
        db.insert(Item(name=f"Item {i}"))

    results = db.select(Item).limit(5).offset(5).fetch_all()
    output.write("Items 6-10:\n")
    for item in results:
        output.write(f"  - {item.name}\n")

    db.close()
    return output.getvalue()


ORDER_ASC_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    name: str
    age: int

db = SqliterDB(memory=True)
db.create_table(User)

# Order ascending by field
results = db.select(User).order("age").fetch_all()

for user in results:
    print(user.name, user.age)
"""

ORDER_DESC_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Product(BaseDBModel):
    name: str
    price: float

db = SqliterDB(memory=True)
db.create_table(Product)

# Order descending (prefix with -)
results = db.select(Product).order("-price").fetch_all()

for product in results:
    print(product.name, product.price)
"""

LIMIT_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Article(BaseDBModel):
    title: str

db = SqliterDB(memory=True)
db.create_table(Article)

# Get first 3 records
results = db.select(Article).limit(3).fetch_all()

for article in results:
    print(article.title)
"""

OFFSET_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Item(BaseDBModel):
    name: str

db = SqliterDB(memory=True)
db.create_table(Item)

# Get second page (skip first 5, take next 5)
results = (
    db.select(Item)
    .limit(5)
    .offset(5)
    .fetch_all()
)

for item in results:
    print(item.name)
"""


def get_category() -> DemoCategory:
    """Get the Ordering & Pagination demo category."""
    return DemoCategory(
        id="ordering",
        title="Ordering & Pagination",
        icon="",
        demos=[
            Demo(
                id="order_asc",
                title="Order Ascending",
                description="Sort results in ascending order",
                category="ordering",
                code=ORDER_ASC_CODE,
                execute=_run_order_asc,
            ),
            Demo(
                id="order_desc",
                title="Order Descending",
                description="Sort results in descending order",
                category="ordering",
                code=ORDER_DESC_CODE,
                execute=_run_order_desc,
            ),
            Demo(
                id="paginate_limit",
                title="Limit Results",
                description="Limit number of results",
                category="ordering",
                code=LIMIT_CODE,
                execute=_run_limit,
            ),
            Demo(
                id="paginate_offset",
                title="Offset Results",
                description="Skip records for pagination",
                category="ordering",
                code=OFFSET_CODE,
                execute=_run_offset,
            ),
        ],
    )
