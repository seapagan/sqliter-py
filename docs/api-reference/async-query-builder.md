# AsyncQueryBuilder

Async fluent query API returned by `AsyncSqliterDB.select()`.

```python
results = await db.select(User).filter(active=True).fetch_all()
```

**Source:** `sqliter/asyncio/query.py`

See also: [Guide -- Asyncio Support](../guide/asyncio.md)

---

## Construction

Instances are created by:

```python
query = db.select(User)
```

Do not instantiate `AsyncQueryBuilder` directly.

---

## Chain-Building Methods

These methods mirror the sync query builder and return `self` for chaining:

- `filter(**conditions)`
- `fields(fields)`
- `exclude(fields)`
- `only(field)`
- `order(field, reverse=False)`
- `limit(count)`
- `offset(count)`
- `group_by(*fields)`
- `annotate(**aggregates)`
- `having(**conditions)`
- `select_related(*paths)`
- `prefetch_related(*paths)`
- `with_count(*paths)`

---

## Async Terminal Methods

These methods execute SQL and must be awaited:

### `fetch_all()`

```python
async def fetch_all(self) -> list[T]:
```

### `fetch_one()`

```python
async def fetch_one(self) -> T | None:
```

### `fetch_first()`

```python
async def fetch_first(self) -> T | None:
```

### `fetch_last()`

```python
async def fetch_last(self) -> T | None:
```

### `fetch_dicts()`

For projection and aggregate queries:

```python
async def fetch_dicts(self) -> list[dict[str, object]]:
```

### `count()`

```python
async def count(self) -> int:
```

### `exists()`

```python
async def exists(self) -> bool:
```

### `update()`

Bulk update matching rows:

```python
async def update(self, **updates: object) -> int:
```

### `delete()`

Bulk delete matching rows:

```python
async def delete(self) -> int:
```

---

## Example

```python
report = await (
    db.select(User)
    .group_by("status")
    .annotate(total=func.count())
    .fetch_dicts()
)
```

---

## Relationship Loading

`AsyncQueryBuilder` supports the same eager loading features as the sync query
builder:

- `select_related()` for forward foreign keys
- `prefetch_related()` for reverse relationships and many-to-many
- `with_count()` for relationship counts

When async ORM models are used, these return async-compatible relationship
wrappers on the fetched instances.
