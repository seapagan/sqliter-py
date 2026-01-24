# Caching Demos

These demos show how to use query result caching for improved performance.

## Enable Caching

Cache query results to avoid repeated database queries.

```python
# --8<-- [start:enable-cache]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    name: str
    email: str
    age: int

db = SqliterDB(memory=True)
db.create_table(User)

# Insert test data
for i in range(50):
    db.insert(User(name=f"User {i}", email=f"user{i}@example.com", age=20 + i))

# Enable caching with 60 second TTL
db.enable_cache(ttl=60)

# First query - cache miss, fetches from database
users1 = db.select(User).filter(age__gte=40).fetch_all()

# Second query - cache hit, returns cached result
users2 = db.select(User).filter(age__gte=40).fetch_all()
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

Set how long cache entries remain valid.

```python
# --8<-- [start:cache-ttl]
from sqliter import SqliterDB

# Cache for 30 seconds
db.enable_cache(ttl=30)

# Cache for 5 minutes
db.enable_cache(ttl=300)

# Cache for 1 hour
db.enable_cache(ttl=3600)
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

Turn off caching when you need fresh data.

```python
# --8<-- [start:disable-cache]
from sqliter import SqliterDB

db = SqliterDB(memory=True)
db.enable_cache(ttl=60)

# ... queries are cached ...

# Disable caching
db.disable_cache()

# Fresh data from database
results = db.select(User).fetch_all()
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

db = SqliterDB(memory=True)
db.enable_cache(ttl=60)

# Normal query (uses cache)
users1 = db.select(User).fetch_all()

# Bypass cache for this query
users2 = db.select(User).bypass_cache().fetch_all()
```

### Use Cases

- **Force refresh**: Get latest data without disabling cache entirely
- **Selective fresh data**: Most queries use cache, some need fresh data
- **Admin operations**: See current state while cache is active

## Cache Invalidation

Manually clear the cache.

```python
# --8<-- [start:clear-cache]
from sqliter import SqliterDB

db = SqliterDB(memory=True)
db.enable_cache(ttl=60)

# After making updates
db.update(user)

# Clear cache to force refresh
db.clear_cache()
```

### When to Clear Cache

- **After bulk updates**: Data has changed significantly
- **After deletes**: References may be stale
- **Manual changes**: Database modified externally

## Caching Strategies

### Always On (Recommended)

```python
db = SqliterDB(database="mydb.db")
db.enable_cache(ttl=60)  # Enable once at startup
```

### Conditional Caching

```python
# Enable for read-heavy operations
db.enable_cache(ttl=300)
reports = db.select(Sales).generate_report()

# Disable for write-heavy operations
db.disable_cache()
for record in new_records:
    db.insert(record)
```

### Per-Query Bypass

```python
db.enable_cache(ttl=60)

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
db.enable_cache(ttl=60)
for _ in range(100):
    users = db.select(User).fetch_all()  # 1 database query, 99 cache hits
```

### Real-World Example

- **Without cache**: 100ms × 100 = 10,000ms (10 seconds)
- **With cache**: 100ms + 1ms × 99 = 199ms (0.2 seconds)
- **Speedup**: 50x faster

## Best Practices

### DO

- Enable caching at application startup
- Set appropriate TTL for your data freshness needs
- Clear cache after bulk updates
- Use bypass_cache() for queries that need fresh data

### DON'T

- Set excessively long TTL for dynamic data
- Cache sensitive data that should always be fresh
- Forget that cached data doesn't reflect database changes

## Related Documentation

- [Database Connection](connection.md) - Connect and configure database
- [Query Results](results.md) - Fetch query results
- [Transactions](transactions.md) - Group operations atomically
