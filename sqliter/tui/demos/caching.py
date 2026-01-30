"""Caching demos."""

from __future__ import annotations

import io
import tempfile
import time
from pathlib import Path

from sqliter import SqliterDB
from sqliter.model import BaseDBModel
from sqliter.tui.demos.base import Demo, DemoCategory, extract_demo_code


def _run_enable_cache() -> str:
    """Demonstrate enabling query result caching for performance.

    Caching stores query results in memory, speeding up repeated queries
    by avoiding disk I/O. Benefits are most apparent with complex queries
    and large datasets.
    """
    output = io.StringIO()

    class User(BaseDBModel):
        name: str
        email: str
        age: int

    # Use file-based database to show real caching benefits
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    db = None
    try:
        db = SqliterDB(db_path, cache_enabled=True)
        db.create_table(User)

        # Insert more data for a more realistic demo
        for i in range(50):
            db.insert(
                User(
                    name=f"User {i}",
                    email=f"user{i}@example.com",
                    age=20 + i,
                )
            )

        output.write("Inserted 50 users\n")
        output.write("Caching stores query results to avoid repeated I/O\n\n")

        # Query with filter (more expensive than simple pk lookup)
        # First query - cache miss
        start = time.perf_counter()
        users = db.select(User).filter(age__gte=40).fetch_all()
        miss_time = (time.perf_counter() - start) * 1000
        output.write(f"First query (cache miss): {miss_time:.3f}ms\n")
        output.write(f"Found {len(users)} users age 40+\n")

        # Second query with same filter - cache hit
        start = time.perf_counter()
        users = db.select(User).filter(age__gte=40).fetch_all()
        hit_time = (time.perf_counter() - start) * 1000
        output.write(f"Second query (cache hit): {hit_time:.3f}ms\n")
        output.write(f"Found {len(users)} users age 40+\n")

        # Show speedup
        if hit_time > 0:
            speedup = miss_time / hit_time
            output.write(f"\nCache hit is {speedup:.1f}x faster!\n")
        output.write("(Benefits increase with query complexity and data size)")
    finally:
        if db is not None:
            db.close()
        # Cleanup
        Path(db_path).unlink(missing_ok=True)

    return output.getvalue()


def _run_cache_stats() -> str:
    """Show how to view cache hit/miss statistics.

    Use get_cache_stats() to monitor cache performance and see how
    effective your caching strategy is.
    """
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

    stats = db.get_cache_stats()
    output.write("Cache statistics:\n")
    output.write(f"  - Total queries: {stats['total']}\n")
    output.write(f"  - Cache hits: {stats['hits']}\n")
    output.write(f"  - Cache misses: {stats['misses']}\n")
    output.write(f"  - Hit rate: {stats['hit_rate']}%\n")

    db.close()
    return output.getvalue()


def _run_get_cache_controls() -> str:
    """Show get() caching, bypass, and TTL overrides."""
    output = io.StringIO()

    class Product(BaseDBModel):
        name: str
        price: float

    db = SqliterDB(memory=True, cache_enabled=True, cache_ttl=60)
    db.create_table(Product)

    product = db.insert(Product(name="Widget", price=19.99))

    db.get(Product, product.pk)
    stats = db.get_cache_stats()
    output.write("After first get (miss):\n")
    output.write(f"  - Hits: {stats['hits']}\n")
    output.write(f"  - Misses: {stats['misses']}\n")

    db.get(Product, product.pk)
    stats = db.get_cache_stats()
    output.write("After second get (hit):\n")
    output.write(f"  - Hits: {stats['hits']}\n")
    output.write(f"  - Misses: {stats['misses']}\n")

    db.get(Product, product.pk, bypass_cache=True)
    stats = db.get_cache_stats()
    output.write("After bypass_cache=True (stats unchanged):\n")
    output.write(f"  - Hits: {stats['hits']}\n")
    output.write(f"  - Misses: {stats['misses']}\n")

    db.get(Product, product.pk, cache_ttl=5)
    output.write("Per-call TTL override set to 5s for this lookup\n")

    db.close()
    return output.getvalue()


def _run_cache_bypass() -> str:
    """Bypass the cache to fetch fresh data from the database.

    Use bypass_cache() when you need to ensure you're getting the most
    up-to-date data, ignoring any cached results.
    """
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
    """Set a time-to-live (TTL) for cached entries.

    Cache entries automatically expire after the specified number of seconds,
    ensuring stale data isn't served indefinitely.
    """
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
    """Manually clear the cache to free memory or force refresh.

    Use clear_cache() when you need to invalidate all cached results
    and start fresh.
    """
    output = io.StringIO()

    class Document(BaseDBModel):
        title: str

    db = SqliterDB(memory=True, cache_enabled=True)
    db.create_table(Document)

    doc = db.insert(Document(title="Doc 1"))
    db.get(Document, doc.pk)
    output.write("Query executed and cached\n")

    db.clear_cache()
    output.write("Cache cleared\n")

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
                id="cache_get_controls",
                title="Get Cache Controls",
                description="Cache, bypass, and TTL for get()",
                category="caching",
                code=extract_demo_code(_run_get_cache_controls),
                execute=_run_get_cache_controls,
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
