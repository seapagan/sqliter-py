"""Caching demos."""

from __future__ import annotations

import io

from sqliter.tui.demos.base import Demo, DemoCategory


def _run_enable_cache() -> str:
    """Execute the enable cache demo."""
    output = io.StringIO()

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel

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

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel

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

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel

    class Item(BaseDBModel):
        name: str

    db = SqliterDB(memory=True, cache_enabled=True)
    db.create_table(Item)

    item = db.insert(Item(name="Item 1"))

    # Normal query (uses cache)
    db.get(Item, item.pk)
    output.write("First query: cached\n")

    # Bypass cache for fresh data
    output.write("Can bypass cache when needed for fresh data\n")

    db.close()
    return output.getvalue()


def _run_cache_ttl() -> str:
    """Execute the cache TTL demo."""
    output = io.StringIO()

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel

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

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel

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


ENABLE_CACHE_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    name: str
    email: str

db = SqliterDB(memory=True, cache_enabled=True)
db.create_table(User)

user = db.insert(User(name="Alice", email="alice@example.com"))

# Subsequent queries are cached
result1 = db.get(User, user.pk)  # From DB
result2 = db.get(User, user.pk)  # From cache
"""

CACHE_STATS_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Product(BaseDBModel):
    name: str
    price: float

db = SqliterDB(memory=True, cache_enabled=True)
db.create_table(Product)

product = db.insert(Product(name="Widget", price=19.99))

# Perform multiple queries
for _ in range(5):
    db.get(Product, product.pk)

# Cache improves performance for repeated queries
"""

CACHE_BYPASS_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Item(BaseDBModel):
    name: str

db = SqliterDB(memory=True, cache_enabled=True)
db.create_table(Item)

item = db.insert(Item(name="Item 1"))

# Normal query uses cache
cached = db.get(Item, item.pk)

# Bypass cache for fresh data (when needed)
# fresh = db.get(Item, item.pk, use_cache=False)
"""

CACHE_TTL_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Article(BaseDBModel):
    title: str

# Cache with time-to-live
db = SqliterDB(
    memory=True,
    cache_enabled=True,
    cache_ttl=60  # seconds
)
db.create_table(Article)

# Cached entries expire after TTL
"""

CACHE_CLEAR_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Document(BaseDBModel):
    title: str

db = SqliterDB(memory=True, cache_enabled=True)
db.create_table(Document)

doc = db.insert(Document(title="Doc 1"))
db.get(Document, doc.pk)  # Cached

# Clear cache when needed
# db.clear_cache()
"""


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
                code=ENABLE_CACHE_CODE,
                execute=_run_enable_cache,
            ),
            Demo(
                id="cache_stats",
                title="Cache Statistics",
                description="View cache hit/miss statistics",
                category="caching",
                code=CACHE_STATS_CODE,
                execute=_run_cache_stats,
            ),
            Demo(
                id="cache_bypass",
                title="Cache Bypass",
                description="Bypass cache for fresh data",
                category="caching",
                code=CACHE_BYPASS_CODE,
                execute=_run_cache_bypass,
            ),
            Demo(
                id="cache_ttl",
                title="Cache TTL",
                description="Set cache expiration time",
                category="caching",
                code=CACHE_TTL_CODE,
                execute=_run_cache_ttl,
            ),
            Demo(
                id="cache_clear",
                title="Clear Cache",
                description="Manually clear the cache",
                category="caching",
                code=CACHE_CLEAR_CODE,
                execute=_run_cache_clear,
            ),
        ],
    )
