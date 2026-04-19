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
