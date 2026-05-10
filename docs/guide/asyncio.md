# Asyncio Support

SQLiter provides optional async support through `sqliter.asyncio` and
`sqliter.asyncio.orm`.

Install the async extra first:

```bash
uv add 'sqliter-py[async]'
```

## Async Database

Use `AsyncSqliterDB` for async CRUD and query execution:

```python
from sqliter.asyncio import AsyncSqliterDB
from sqliter.model import BaseDBModel


class User(BaseDBModel):
    name: str


async def main() -> None:
    db = AsyncSqliterDB("example.db")
    await db.create_table(User)

    user = await db.insert(User(name="Ada"))
    fetched = await db.get(User, user.pk)
    users = await db.select(User).filter(name="Ada").fetch_all()

    await db.delete(User, user.pk)
    await db.close()
```

You can also use the async context manager:

```python
async with AsyncSqliterDB("example.db") as db:
    await db.create_table(User)
```

## Async Queries

`AsyncQueryBuilder` keeps the same chain-building style as the sync query API,
but terminal operations are awaited:

```python
results = await (
    db.select(User)
    .filter(name="Ada")
    .order("name")
    .limit(10)
    .fetch_all()
)
```

These query terminal methods are async:

- `fetch_all()`
- `fetch_one()`
- `fetch_first()`
- `fetch_last()`
- `fetch_dicts()`
- `count()`
- `exists()`
- `update()`
- `delete()`

Async query builders also support the same chain methods as sync, including
`fields()`, `only()`, and aggregate filtering via `having()`.

`AsyncSqliterDB.get_table_names()` is a method rather than a property because
async properties cannot be awaited.

## Async ORM

For async ORM usage, define models with `AsyncBaseDBModel` and the async
relationship descriptors:

```python
from sqliter.asyncio import AsyncSqliterDB
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
```

### Forward Foreign Keys

Async forward foreign keys use explicit lazy loading:

```python
book = await db.get(Book, 1)
author = await book.author.fetch()
```

If the relationship was eager loaded with `select_related()`, the related model
instance is available directly:

```python
book = await db.select(Book).select_related("author").fetch_one()
print(book.author.name)
```

### Reverse Relationships

Reverse relationships return async query wrappers:

```python
author = await db.get(Author, 1)
books = await author.books.fetch_all()
count = await author.books.count()
```

If reverse relationships are prefetched, the same async read methods still
work:

```python
author = await db.select(Author).prefetch_related("books").fetch_one()
books = await author.books.fetch_all()
```

### Many-to-Many

Async many-to-many relationships return async managers:

```python
from sqliter.asyncio.orm import AsyncManyToMany


class Tag(AsyncBaseDBModel):
    name: str


class Article(AsyncBaseDBModel):
    title: str
    tags: AsyncManyToMany[Tag] = AsyncManyToMany(
        Tag,
        related_name="articles",
    )


article = await db.insert(Article(title="Guide"))
tag = await db.insert(Tag(name="python"))

await article.tags.add(tag)
tags = await article.tags.fetch_all()
```

Available async many-to-many operations include:

- `fetch_all()`
- `fetch_one()`
- `count()`
- `exists()`
- `filter()`
- `add()`
- `remove()`
- `clear()`
- `set()`

## Differences From Sync ORM

The main intentional difference is foreign-key lazy loading:

- Sync ORM: `post.author.name`
- Async ORM lazy loading: `author = await post.author.fetch()`

This difference is required because Python attribute access cannot implicitly
`await`.

## mypy and Static Type Checking

Two areas require explicit `cast()` calls when using strict mypy.

### FK lazy loading

`AsyncForeignKey` is typed to return the related model type (`T`) so that
eager-loaded access — `book.author.name` after `select_related()` — type-checks
without any extra annotation. At runtime the **lazy-loaded** value is an
`AsyncLazyLoader[T]`, not `T` itself. The two return types cannot both be
expressed accurately as a single overload without breaking one of the two use
cases, so the eager-loading path was chosen as the ergonomic default.

When using `--strict` mypy, lazy FK access requires a `cast`:

```python
from typing import cast
from sqliter.asyncio.orm import AsyncLazyLoader

# mypy sees book.author as Author, not AsyncLazyLoader[Author]
loader = cast(AsyncLazyLoader[Author], book.author)
author = await loader.fetch()
```

Without `--strict` (or with `# type: ignore[union-attr]`) you can write the
simpler form directly:

```python
author = await book.author.fetch()
```

### Reverse FK accessors

Reverse relationship accessors (`author.books`, `post.tags`, etc.) are
installed dynamically via `setattr`, so `AsyncBaseDBModel.__getattribute__`
returns `object` for them. Under strict mypy, cast to the appropriate manager
type:

```python
from typing import cast
from sqliter.asyncio.orm import AsyncReverseQuery

books_query = cast(AsyncReverseQuery, author.books)
books = cast(list[Book], await books_query.fetch_all())
```

!!! note
    These are **mypy-only** workarounds. At runtime `book.author` is always
    an `AsyncLazyLoader` (lazy) or the model instance (eager), and
    `author.books` is always an `AsyncReverseQuery`. No cast is needed if
    you are not running strict type checking.
