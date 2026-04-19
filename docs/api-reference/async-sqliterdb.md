# AsyncSqliterDB

Async database entry point for SQLiter.

```python
from sqliter.asyncio import AsyncSqliterDB
```

**Source:** `sqliter/asyncio/db.py`

See also: [Guide -- Asyncio Support](../guide/asyncio.md)

---

## Constructor

```python
def __init__(
    self,
    db_filename: str | None = None,
    *,
    memory: bool = False,
    auto_commit: bool = True,
    debug: bool = False,
    logger: logging.Logger | None = None,
    reset: bool = False,
    return_local_time: bool = True,
    cache_enabled: bool = False,
    cache_max_size: int = 1000,
    cache_ttl: int | None = None,
    cache_max_memory_mb: int | None = None,
) -> None:
```

This matches the sync constructor closely, except `reset=True` is not supported
directly in `__init__()`.

> [!NOTE]
> Use `await AsyncSqliterDB.create(..., reset=True)` instead of passing
> `reset=True` to the constructor.

---

## Async Lifecycle Methods

### `create()`

Async factory that supports reset-on-create.

```python
@classmethod
async def create(
    cls,
    db_filename: str | None = None,
    *,
    memory: bool = False,
    auto_commit: bool = True,
    debug: bool = False,
    logger: logging.Logger | None = None,
    reset: bool = False,
    return_local_time: bool = True,
    cache_enabled: bool = False,
    cache_max_size: int = 1000,
    cache_ttl: int | None = None,
    cache_max_memory_mb: int | None = None,
) -> AsyncSqliterDB:
```

### `connect()`

```python
async def connect(self) -> aiosqlite.Connection:
```

### `close()`

```python
async def close(self) -> None:
```

### `commit()`

```python
async def commit(self) -> None:
```

### Async context manager

```python
async def __aenter__(self) -> AsyncSqliterDB:
async def __aexit__(self, exc_type, exc, tb) -> None:
```

Example:

```python
async with AsyncSqliterDB("app.db") as db:
    ...
```

---

## Table Methods

### `create_table()`

```python
async def create_table(
    self,
    model_class: type[BaseDBModel],
    *,
    exists_ok: bool = True,
    force: bool = False,
) -> None:
```

Creates tables, indexes, FK constraints, and ORM many-to-many junction tables.

### `drop_table()`

```python
async def drop_table(
    self,
    model_class: type[BaseDBModel],
) -> None:
```

### `get_table_names()`

```python
async def get_table_names(self) -> list[str]:
```

This is a method in the async API instead of a property because async
properties cannot be awaited.

## Read-Only Properties

### `auto_commit`

```python
@property
def auto_commit(self) -> bool:
```

### `is_autocommit`

```python
@property
def is_autocommit(self) -> bool:
```

Compatibility alias for the sync property name.

---

## CRUD Methods

### `insert()`

```python
async def insert(self, model_instance: T) -> T:
```

### `bulk_insert()`

```python
async def bulk_insert(
    self,
    instances: Sequence[T],
    *,
    timestamp_override: bool = False,
) -> list[T]:
```

### `get()`

```python
async def get(
    self,
    model_class: type[T],
    primary_key_value: int,
    *,
    bypass_cache: bool = False,
    cache_ttl: int | None = None,
) -> T | None:
```

### `update()`

```python
async def update(self, model_instance: BaseDBModel) -> None:
```

### `update_where()`

```python
async def update_where(
    self,
    model_class: type[T],
    where: dict[str, Any],
    values: dict[str, Any],
) -> int:
```

### `delete()`

```python
async def delete(
    self,
    model_class: type[BaseDBModel],
    primary_key_value: int | str,
) -> None:
```

### `select()`

```python
def select(
    self,
    model_class: type[T],
    fields: list[str] | None = None,
    exclude: list[str] | None = None,
) -> AsyncQueryBuilder[T]:
```

This is sync to construct the query object. The query's terminal methods are
awaited.

## Cache Methods

### `clear_cache()`

```python
def clear_cache(self) -> None:
```

Clears all cached query results.

### `reset_cache_stats()`

```python
def reset_cache_stats(self) -> None:
```

Resets cache hit/miss counters without changing current cached entries.

### `get_cache_stats()`

```python
def get_cache_stats(self) -> dict[str, int | float]:
```

Returns the same cache statistics as the sync API.

---

## Query Example

```python
users = await (
    db.select(User)
    .filter(active=True)
    .order("name")
    .limit(20)
    .fetch_all()
)
```

---

## Async ORM Example

```python
from sqliter.asyncio.orm import AsyncBaseDBModel, AsyncForeignKey


class Author(AsyncBaseDBModel):
    name: str


class Book(AsyncBaseDBModel):
    title: str
    author: AsyncForeignKey[Author] = AsyncForeignKey(
        Author,
        related_name="books",
        on_delete="CASCADE",
    )


book = await db.get(Book, 1)
author = await book.author.fetch()
```
