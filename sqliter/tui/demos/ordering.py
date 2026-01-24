"""Ordering & Pagination demos."""

from __future__ import annotations

import io

from sqliter import SqliterDB
from sqliter.model import BaseDBModel
from sqliter.tui.demos.base import Demo, DemoCategory, extract_demo_code


def _run_order_asc() -> str:
    """Sort query results in ascending order.

    Use order(field_name) to sort results from lowest to highest.
    """
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
    """Sort query results in descending order.

    Use order(field_name, reverse=True) to sort from highest to lowest.
    """
    output = io.StringIO()

    class Product(BaseDBModel):
        name: str
        price: float

    db = SqliterDB(memory=True)
    db.create_table(Product)

    db.insert(Product(name="Item A", price=10.0))
    db.insert(Product(name="Item B", price=30.0))
    db.insert(Product(name="Item C", price=20.0))

    results = db.select(Product).order("price", reverse=True).fetch_all()
    output.write("Products ordered by price (descending):\n")
    for product in results:
        output.write(f"  - {product.name}: ${product.price}\n")

    db.close()
    return output.getvalue()


def _run_limit() -> str:
    """Limit the number of results returned.

    Use limit(count) to fetch only the first N records.
    """
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
    """Skip a specified number of results.

    Use offset(count) with limit() for pagination, skipping first N records.
    """
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
                code=extract_demo_code(_run_order_asc),
                execute=_run_order_asc,
            ),
            Demo(
                id="order_desc",
                title="Order Descending",
                description="Sort results in descending order",
                category="ordering",
                code=extract_demo_code(_run_order_desc),
                execute=_run_order_desc,
            ),
            Demo(
                id="paginate_limit",
                title="Limit Results",
                description="Limit number of results",
                category="ordering",
                code=extract_demo_code(_run_limit),
                execute=_run_limit,
            ),
            Demo(
                id="paginate_offset",
                title="Offset Results",
                description="Skip records for pagination",
                category="ordering",
                code=extract_demo_code(_run_offset),
                execute=_run_offset,
            ),
        ],
    )
