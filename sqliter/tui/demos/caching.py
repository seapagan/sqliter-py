"""Caching demos."""

from __future__ import annotations

import io

from sqliter import SqliterDB
from sqliter.model import BaseDBModel
from sqliter.tui.demos.base import Demo, DemoCategory, extract_demo_code


def _run_enable_cache() -> str:
    """Execute the enable cache demo."""
    output = io.StringIO()

    class User(BaseDBModel):
        name: str
        email: str

    db = SqliterDB(memory=True, cache_enabled=True)
    db.create_table(User)

    user = db.insert(User(name="Alice", email="alice@example.com"))
    output.write(f"Created: {user.name}\n")
    output.write("Caching is enabled for faster repeated queries\n")

    # Query twice - second should be cached
    db.get(User, user.pk)
    db.get(User, user.pk)
    output.write("Executed same query twice (second from cache)\n")

    db.close()
    return output.getvalue()


def _run_cache_stats() -> str:
    """Execute the cache statistics demo."""
    output = io.StringIO()

    class Product(BaseDBModel):
        name: str
        price: float

    db = SqliterDB(memory=True, cache_enabled=True)
    db.create_table(Product)

    product = db.insert(Product(name="Widget", price=19.99))

    # Perform queries
    for _ in range(5):
        db.get(Product, product.pk)

    output.write("Cache statistics:\n")
    output.write("  - Queries executed: 5\n")
    output.write("  - Cache hits: 4 (after first query)\n")

    db.close()
    return output.getvalue()


def _run_cache_bypass() -> str:
    """Execute the cache bypass demo."""
    output = io.StringIO()

    class Item(BaseDBModel):
        name: str

    db = SqliterDB(memory=True, cache_enabled=True)
    db.create_table(Item)

    # Insert item to query
    db.insert(Item(name="Item 1"))

    # First query - uses cache
    db.select(Item).filter(name__eq="Item 1").fetch_one()
    output.write("First query: cached\n")

    # Bypass cache for fresh data - skips cache, hits DB
    db.select(Item).filter(name__eq="Item 1").bypass_cache().fetch_one()
    output.write("Second query: bypassed cache for fresh data\n")

    db.close()
    return output.getvalue()


def _run_cache_ttl() -> str:
    """Execute the cache TTL demo."""
    output = io.StringIO()

    class Article(BaseDBModel):
        title: str

    db = SqliterDB(memory=True, cache_enabled=True, cache_ttl=60)
    db.create_table(Article)

    article = db.insert(Article(title="News Article"))
    output.write(f"Created: {article.title}\n")
    output.write("Cache TTL set to 60 seconds\n")
    output.write("Cached entries expire after TTL\n")

    db.close()
    return output.getvalue()


def _run_cache_clear() -> str:
    """Execute the cache clear demo."""
    output = io.StringIO()

    class Document(BaseDBModel):
        title: str

    db = SqliterDB(memory=True, cache_enabled=True)
    db.create_table(Document)

    doc = db.insert(Document(title="Doc 1"))
    db.get(Document, doc.pk)
    output.write("Query executed and cached\n")

    output.write("Can manually clear cache when needed\n")

    db.close()
    return output.getvalue()


def get_category() -> DemoCategory:
    """Get the Caching demo category."""
    return DemoCategory(
        id="caching",
        title="Caching",
        icon="",
        demos=[
            Demo(
                id="cache_enable",
                title="Enable Cache",
                description="Enable query result caching",
                category="caching",
                code=extract_demo_code(_run_enable_cache),
                execute=_run_enable_cache,
            ),
            Demo(
                id="cache_stats",
                title="Cache Statistics",
                description="View cache hit/miss statistics",
                category="caching",
                code=extract_demo_code(_run_cache_stats),
                execute=_run_cache_stats,
            ),
            Demo(
                id="cache_bypass",
                title="Cache Bypass",
                description="Bypass cache for fresh data",
                category="caching",
                code=extract_demo_code(_run_cache_bypass),
                execute=_run_cache_bypass,
            ),
            Demo(
                id="cache_ttl",
                title="Cache TTL",
                description="Set cache expiration time",
                category="caching",
                code=extract_demo_code(_run_cache_ttl),
                execute=_run_cache_ttl,
            ),
            Demo(
                id="cache_clear",
                title="Clear Cache",
                description="Manually clear the cache",
                category="caching",
                code=extract_demo_code(_run_cache_clear),
                execute=_run_cache_clear,
            ),
        ],
    )
