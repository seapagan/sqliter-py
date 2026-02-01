# Many-to-Many (ORM)

The ORM module provides a `ManyToMany` descriptor and manager API for
many-to-many relationships. Junction tables are created automatically
when you call `SqliterDB.create_table()` on a model that defines an M2M
field.

```python
from sqliter.orm import BaseDBModel, ManyToMany
```

**Sources:** `sqliter/orm/m2m.py`, `sqliter/orm/registry.py`,
`sqliter/sqliter.py`

---

## `ManyToMany[T]`

Descriptor used on ORM models.

```python
class ManyToMany(Generic[T]):
    def __init__(
        self,
        to_model: type[T] | str,
        *,
        through: str | None = None,
        related_name: str | None = None,
        symmetrical: bool = False,
    ) -> None:
```

**Parameters:**

| Parameter      | Type                   | Default    | Description                  |
| -------------- | ---------------------- | ---------- | ---------------------------- |
| `to_model`     | `type[T]` &#124; `str` | *required* | Related model or forward ref |
| `through`      | `str` &#124; `None`    | `None`     | Custom junction table name   |
| `related_name` | `str` &#124; `None`    | `None`     | Reverse accessor name        |
| `symmetrical`  | `bool`                 | `False`    | Self-referential symmetry    |

**Notes:**

- When `symmetrical=True` and `to_model` is the same class, SQLiter
  stores a single row per pair and returns the relationship from either
  side. No reverse accessor is created for symmetrical self-relations.
- `to_model` can be a string forward ref. The relationship resolves when
  the target model class is registered.
- Reverse accessors are created automatically when `related_name` is set
  or auto-generated.

---

## `ManyToManyManager`

Returned when accessing the descriptor from an instance.

```python
tags = article.tags
```

**Methods:**

- `add(*instances) -> None`
- `remove(*instances) -> None`
- `clear() -> None`
- `set(*instances) -> None`
- `fetch_all() -> list[T]`
- `fetch_one() -> T | None`
- `count() -> int`
- `exists() -> bool`
- `filter(**kwargs) -> QueryBuilder[Any]`

All methods require a valid `db_context`, which is set on instances
returned from `SqliterDB` operations.

---

## `ReverseManyToMany`

Reverse accessor descriptor automatically installed on the target model
unless suppressed (symmetrical self-ref).

```python
articles = tag.articles.fetch_all()
```

---

## `PrefetchedM2MResult`

Returned when accessing an M2M relationship that was loaded via
`prefetch_related()`. Wraps a cached list of related instances and
provides the same interface as `ManyToManyManager`.

```python
from sqliter.orm.m2m import PrefetchedM2MResult
```

**Read methods** (served from cache, no DB query):

- `fetch_all() -> list[T]`
- `fetch_one() -> T | None`
- `count() -> int`
- `exists() -> bool`

**Write methods** (delegated to the real `ManyToManyManager`):

- `add(*instances) -> None`
- `remove(*instances) -> None`
- `clear() -> None`
- `set(*instances) -> None`

**Filter** (falls back to a real DB query via the manager):

- `filter(**kwargs) -> QueryBuilder[Any]`

**Example:**

```python
articles = db.select(Article).prefetch_related("tags").fetch_all()
guide = articles[0]

isinstance(guide.tags, PrefetchedM2MResult)  # True
guide.tags.count()       # served from cache
guide.tags.add(new_tag)  # delegates to ManyToManyManager
```

---

## `PrefetchedResult` (Reverse FK)

Returned when accessing a reverse FK relationship that was loaded via
`prefetch_related()`. Wraps a cached list of related instances.

```python
from sqliter.orm.query import PrefetchedResult
```

**Read methods** (served from cache):

- `fetch_all() -> list[BaseDBModel]`
- `fetch_one() -> BaseDBModel | None`
- `count() -> int`
- `exists() -> bool`

**Filter** (falls back to a real DB query via `ReverseQuery`):

- `filter(**kwargs) -> ReverseQuery`

---

## Junction Tables

By default, the junction table name is generated from the two table
names in alphabetical order (e.g., `articles_tags`). Use `through` to
override it.

Junction tables include:

- `CASCADE` FK constraints
- A unique constraint on the pair
- Indexes on both FK columns
