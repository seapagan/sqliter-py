# Caching Demos

These demos show how to use query result caching for improved performance.

## Enable Caching

Cache query results to avoid repeated database queries.

```python
# --8<-- [start:enable-cache]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel
import tempfile
import time
from pathlib import Path

class User(BaseDBModel):
    name: str
    email: str
    age: int

# Use file-based database to show real caching benefits
with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
    db_path = f.name

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

    print("Inserted 50 users")
    print("Caching stores query results to avoid repeated I/O\n")

    # Query with filter (more expensive than simple pk lookup)
    # First query - cache miss
    start = time.perf_counter()
    users = db.select(User).filter(age__gte=40).fetch_all()
    miss_time = (time.perf_counter() - start) * 1000
    print(f"First query (cache miss): {miss_time:.3f}ms")
    print(f"Found {len(users)} users age 40+")

    # Second query with same filter - cache hit
    start = time.perf_counter()
    users = db.select(User).filter(age__gte=40).fetch_all()
    hit_time = (time.perf_counter() - start) * 1000
    print(f"Second query (cache hit): {hit_time:.3f}ms")
    print(f"Found {len(users)} users age 40+")

    # Show speedup
    if hit_time > 0:
        speedup = miss_time / hit_time
        print(f"\nCache hit is {speedup:.1f}x faster!")
    print("(Benefits increase with query complexity and data size)")

    db.close()
finally:
    # Cleanup
    Path(db_path).unlink(missing_ok=True)
# --8<-- [end:enable-cache]
```

### What Gets Cached

- Query results are stored in memory
- Cache key includes the query parameters
- Results are returned until TTL expires

### Performance Benefits

- **Memory databases**: 1.5-2x faster for cache hits
- **File databases**: 6-7x faster for cache hits
- **Complex queries**: Benefits increase with query complexity

## Cache TTL (Time To Live)

Set how long cache entries remain valid when creating the database connection.

```python
# --8<-- [start:cache-ttl]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Article(BaseDBModel):
    title: str

db = SqliterDB(memory=True, cache_enabled=True, cache_ttl=60)
db.create_table(Article)

article = db.insert(Article(title="News Article"))
print(f"Created: {article.title}")
print("Cache TTL set to 60 seconds")
print("Cached entries expire after TTL")

db.close()
# --8<-- [end:cache-ttl]
```

### TTL Behavior

- Results are cached for the specified duration
- After TTL expires, next query fetches fresh data
- Cache is updated automatically on the next query

### Choosing TTL

- **Short TTL (10-60s)**: Frequently changing data
- **Medium TTL (1-5min)**: Moderately dynamic data
- **Long TTL (10min+)**: Relatively static data

## Disable Caching

Create database without caching for fresh data.

```python
# --8<-- [start:disable-cache]
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

print("Cache statistics:")
print("  - Queries executed: 5")
print("  - Cache hits: 4 (after first query)")

db.close()
# --8<-- [end:disable-cache]
```

### When to Disable

- **Just updated data**: Need to see latest changes
- **Critical queries**: Must have fresh data
- **Testing**: Want to verify actual database state

## Cache Bypass

Bypass cache for specific queries.

```python
# --8<-- [start:cache-bypass]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Item(BaseDBModel):
    name: str

db = SqliterDB(memory=True, cache_enabled=True)
db.create_table(Item)

# Insert item to query
db.insert(Item(name="Item 1"))

# First query - uses cache
db.select(Item).filter(name__eq="Item 1").fetch_one()
print("First query: cached")

# Bypass cache for fresh data - skips cache, hits DB
db.select(Item).filter(name__eq="Item 1").bypass_cache().fetch_one()
print("Second query: bypassed cache for fresh data")

db.close()
# --8<-- [end:cache-bypass]
```

### Use Cases

- **Force refresh**: Get latest data without disabling cache entirely
- **Selective fresh data**: Most queries use cache, some need fresh data
- **Admin operations**: See current state while cache is active

## Cache Invalidation

Cache automatically expires based on TTL. For manual invalidation, use the
`clear_cache()` method.

```python
# --8<-- [start:clear-cache]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Document(BaseDBModel):
    title: str

db = SqliterDB(memory=True, cache_enabled=True)
db.create_table(Document)

doc = db.insert(Document(title="Doc 1"))
db.get(Document, doc.pk)
print("Query executed and cached")

db.clear_cache()
print("Cache cleared")

db.close()
# --8<-- [end:clear-cache]
```

### When Cache Invalidates

- **Automatic expiry**: After TTL seconds
- **Using bypass_cache()**: Per-query fresh data
- **Manual clearing**: Call `clear_cache()` to free memory or force refresh
- **Write operations**: Insert/update/delete automatically invalidate affected tables

## Caching Strategies

### Always On (Recommended)

```python
# Enable cache at database creation
db = SqliterDB(database="mydb.db", cache_enabled=True, cache_ttl=60)
```

### Selective Caching

```python
# For read-heavy workloads
db_cached = SqliterDB(database="mydb.db", cache_enabled=True, cache_ttl=300)
reports = db_cached.select(Sales).fetch_all()

# For write-heavy workloads
db_fresh = SqliterDB(database="mydb.db", cache_enabled=False)
for record in new_records:
    db_fresh.insert(record)
```

### Per-Query Bypass

```python
db = SqliterDB(memory=True, cache_enabled=True, cache_ttl=60)

# Most queries use cache
summary = db.select(Stats).fetch_one()

# Critical query needs fresh data
current_count = db.select(Users).bypass_cache().count()
```

## When to Use Caching

### Ideal For

- **Read-heavy applications**: Mostly queries, few updates
- **Expensive queries**: Complex filters, joins, aggregations
- **Dashboard data**: Statistics that don't change often
- **Reference data**: Lookup tables, configuration

### Avoid For

- **Write-heavy applications**: Frequent updates invalidate cache
- **Real-time data**: Always need the latest data
- **Large result sets**: Memory concerns with caching
- **Frequently changing data**: Cache invalidates too often

## Performance Impact

### Before Caching

```python
# Each query hits the database
for _ in range(100):
    users = db.select(User).fetch_all()  # 100 database queries
```

### After Caching

```python
db = SqliterDB(memory=True, cache_enabled=True, cache_ttl=60)
for _ in range(100):
    users = db.select(User).fetch_all()  # 1 database query, 99 cache hits
```

### Real-World Example

- **Without cache**: 100ms × 100 = 10,000ms (10 seconds)
- **With cache**: 100ms + 1ms × 99 = 199ms (0.2 seconds)
- **Speedup**: 50x faster

## Best Practices

### DO

- Enable caching when creating database connection for read-heavy workloads
- Set appropriate TTL for your data freshness needs
- Use bypass_cache() for queries that need fresh data
- Monitor cache performance with get_cache_stats()

### DON'T

- Set excessively long TTL for dynamic data
- Cache sensitive data that should always be fresh
- Forget that cached data doesn't reflect recent database changes

## Related Documentation

- [Database Connection](connection.md) - Connect and configure database
- [Query Results](results.md) - Fetch query results
- [Transactions](transactions.md) - Group operations atomically
