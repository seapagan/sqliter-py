# Async ORM

Async ORM support lives under `sqliter.asyncio.orm`.

```python
from sqliter.asyncio.orm import (
    AsyncBaseDBModel,
    AsyncForeignKey,
    AsyncManyToMany,
)
```

**Sources:** `sqliter/asyncio/orm/model.py`, `sqliter/asyncio/orm/fields.py`,
`sqliter/asyncio/orm/query.py`, `sqliter/asyncio/orm/m2m.py`

See also: [Guide -- Asyncio Support](../guide/asyncio.md)

> [!NOTE]
> Async ORM intentionally differs from sync ORM for lazy FK access:
> sync uses `book.author.name`, while async lazy loading uses
> `author = await book.author.fetch()`.

---

## `AsyncBaseDBModel`

Base model for async ORM usage.

```python
from sqliter.asyncio.orm import AsyncBaseDBModel
```

Use this instead of `sqliter.orm.BaseDBModel` when the model is meant to be
used with `AsyncSqliterDB`.

### Behavior

- forward FK fields return async-aware values
- reverse FK accessors return async reverse query wrappers
- many-to-many accessors return async managers
- eager-loaded relations are returned directly from caches

---

## `AsyncForeignKey[T]`

Async FK descriptor.

```python
class AsyncForeignKey(Generic[T]):
    def __init__(
        self,
        to_model: type[T],
        *,
        on_delete: FKAction = "RESTRICT",
        on_update: FKAction = "RESTRICT",
        null: bool = False,
        unique: bool = False,
        related_name: str | None = None,
        db_column: str | None = None,
    ) -> None:
```

### Lazy access

Accessing a forward FK on an instance returns either:

- `None` for null FK values
- the eager-loaded related object if already cached
- an `AsyncLazyLoader[T]` otherwise

Example:

```python
book = await db.get(Book, 1)
loader = book.author
author = await loader.fetch()
```

---

## `AsyncLazyLoader[T]`

Explicit async FK loader.

### `fetch()`

```python
async def fetch(self) -> T | None:
```

Loads the related object and caches it on the loader.

### `db_context`

Read-only property exposing the current DB context.

### `__getattr__()`

Raises `AttributeError` with guidance to call `await relation.fetch()` first.

---

## `AsyncReverseQuery`

Returned by reverse FK accessors such as `author.books`.

### Query-building methods

- `filter(**kwargs)`
- `limit(count)`
- `offset(count)`

### Async terminal methods

- `await fetch_all()`
- `await fetch_one()`
- `await count()`
- `await exists()`

Example:

```python
author = await db.get(Author, 1)
books = await author.books.filter(title="Guide").fetch_all()
```

---

## `AsyncPrefetchedResult`

Returned when a reverse FK relation was loaded through `prefetch_related()`.

Read methods:

- `await fetch_all()`
- `await fetch_one()`
- `await count()`
- `await exists()`

`filter(**kwargs)` falls back to a real `AsyncReverseQuery`.

---

## `AsyncManyToMany[T]`

Async many-to-many descriptor.

```python
class AsyncManyToMany(Generic[T]):
    def __init__(
        self,
        to_model: type[T] | str,
        *,
        through: str | None = None,
        related_name: str | None = None,
        symmetrical: bool = False,
    ) -> None:
```

Accessing the descriptor from an instance returns an async manager or a
prefetched wrapper.

---

## `AsyncManyToManyManager[T]`

Returned by many-to-many accessors such as `article.tags`.

### Read/query methods

- `await fetch_all()`
- `await fetch_one()`
- `await count()`
- `await exists()`
- `await filter(**kwargs)`

### Write methods

- `await add(*instances)`
- `await remove(*instances)`
- `await clear()`
- `await set(*instances)`

### Property

- `sql_metadata`

Example:

```python
await article.tags.add(tag)
tags = await article.tags.fetch_all()
```

---

## `AsyncPrefetchedM2MResult[T]`

Returned when an M2M relation was loaded through `prefetch_related()`.

Read methods are served from cache:

- `await fetch_all()`
- `await fetch_one()`
- `await count()`
- `await exists()`

Write methods delegate to the real manager:

- `await add(*instances)`
- `await remove(*instances)`
- `await clear()`
- `await set(*instances)`

`await filter(**kwargs)` falls back to a real async query.

---

## `AsyncReverseManyToMany`

Reverse-side async many-to-many descriptor installed on the related model when
`related_name` is defined.

Example:

```python
articles = await tag.articles.fetch_all()
```
