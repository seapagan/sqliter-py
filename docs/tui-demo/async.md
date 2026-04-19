# Async Support Demos

These demos show how to use SQLiter's async API via `AsyncSqliterDB`. The async
interface mirrors the sync API almost exactly — the main differences are the
`await` keyword before every database operation and `async with` for context
managers.

!!! tip "Installation"
    Async support requires the `aiosqlite` package. Install it with:

    ```bash
    pip install sqliter-py[async]
    # or, for everything:
    pip install sqliter-py[full]
    ```

---

## Async Connection

Create an async database connection. The constructor parameters are identical to
`SqliterDB` — only the method calls need `await`.

```python
# --8<-- [start:async-conn]
import asyncio
from sqliter.asyncio import AsyncSqliterDB

async def main():
    db = AsyncSqliterDB(memory=True)
    print(f"Created database: {db}")
    print(f"Is memory: {db.is_memory}")
    print(f"Filename: {db.filename}")

    await db.connect()
    print(f"Connected: {db.is_connected}")

    await db.close()
    print(f"After close: {db.is_connected}")

asyncio.run(main())
# --8<-- [end:async-conn]
```

### What Happens

`AsyncSqliterDB` creates the database object but does not open a connection
until `await db.connect()` is called (or an `async with` block is entered). All
properties — `is_memory`, `filename`, `is_connected` — behave the same as the
sync version.

### When to Use

Use `AsyncSqliterDB` whenever your application already runs an async event loop
(FastAPI, aiohttp, asyncio-based CLI tools). Mixing sync SQLiter inside an async
context can block the event loop.

---

## Async Context Manager

The `async with db:` block manages the connection, transaction, and cleanup
automatically — identical semantics to the sync `with db:`, but you must use
the `async` form.

```python
# --8<-- [start:async-context]
import asyncio
from sqliter.asyncio import AsyncSqliterDB
from sqliter.model import BaseDBModel

class Task(BaseDBModel):
    title: str
    done: bool = False

async def main():
    db = AsyncSqliterDB(memory=True)

    async with db:
        await db.create_table(Task)
        task = await db.insert(Task(title="Learn async SQLiter"))
        print(f"Inserted: {task.title} (pk={task.pk})")
        print("Transaction auto-commits on exit")

    print(f"\nAfter context: connected={db.is_connected}")

asyncio.run(main())
# --8<-- [end:async-context]
```

### What Happens

On entry, `async with db:` opens the connection and begins a transaction. On
clean exit, the transaction is committed. If an exception escapes the block, all
changes are rolled back automatically.

### When to Use

Prefer `async with db:` over manually calling `await db.connect()` and
`await db.close()`. It ensures cleanup even when exceptions occur.

!!! warning "Must use `async with`, not `with`"
    Using the plain `with db:` on an `AsyncSqliterDB` instance will raise a
    `TypeError`. Always use `async with db:`.

---

## Async CRUD Operations

All data operations — including `create_table` — are coroutines that must be
awaited. The method signatures are otherwise identical to the sync API.

```python
# --8<-- [start:async-crud]
import asyncio
from sqliter.asyncio import AsyncSqliterDB
from sqliter.model import BaseDBModel

class Product(BaseDBModel):
    name: str
    price: float

async def main():
    db = AsyncSqliterDB(memory=True)
    await db.create_table(Product)

    # Insert
    widget = await db.insert(Product(name="Widget", price=9.99))
    print(f"Inserted: {widget.name} pk={widget.pk}")

    # Get by primary key
    fetched = await db.get(Product, widget.pk)
    if fetched is not None:
        print(f"Fetched: {fetched.name}")

    # Update
    widget.price = 12.99
    await db.update(widget)
    updated = await db.get(Product, widget.pk)
    if updated is not None:
        print(f"Updated price: {updated.price}")

    # Delete
    await db.delete(Product, widget.pk)
    gone = await db.get(Product, widget.pk)
    print(f"After delete: {gone}")

    await db.close()

asyncio.run(main())
# --8<-- [end:async-crud]
```

### What Happens

Each database call suspends the coroutine while the I/O completes, letting
the event loop run other tasks. The returned objects are the same Pydantic
model instances as the sync API.

---

## Async Bulk Insert

Insert multiple records efficiently in a single async transaction.

```python
# --8<-- [start:async-bulk]
import asyncio
from sqliter.asyncio import AsyncSqliterDB
from sqliter.model import BaseDBModel

class Tag(BaseDBModel):
    label: str

async def main():
    db = AsyncSqliterDB(memory=True)
    await db.create_table(Tag)

    tags = await db.bulk_insert([
        Tag(label="python"),
        Tag(label="async"),
        Tag(label="sqlite"),
    ])

    print(f"Inserted {len(tags)} tags:")
    for tag in tags:
        print(f"  pk={tag.pk}  {tag.label}")

    count = await db.select(Tag).count()
    print(f"\nTotal in DB: {count}")

    await db.close()

asyncio.run(main())
# --8<-- [end:async-bulk]
```

### What Happens

All inserts are wrapped in a single transaction for performance. The method
returns the list of inserted instances, each with its `pk` populated. Passing
an empty list is a no-op that returns `[]`.

---

## Async Queries

Query builder chaining methods (`filter`, `limit`, `offset`, `order`) are
synchronous and return the builder. Only the terminal methods that actually
touch the database are coroutines.

```python
# --8<-- [start:async-query]
import asyncio
from sqliter.asyncio import AsyncSqliterDB
from sqliter.model import BaseDBModel

class Item(BaseDBModel):
    name: str
    qty: int

async def main():
    db = AsyncSqliterDB(memory=True)
    await db.create_table(Item)
    await db.bulk_insert([
        Item(name="Apple", qty=5),
        Item(name="Banana", qty=12),
        Item(name="Cherry", qty=3),
        Item(name="Date", qty=8),
    ])

    # Terminal methods require await
    all_items = await db.select(Item).fetch_all()
    print(f"All items: {len(all_items)}")

    in_stock = await db.select(Item).filter(qty__gt=4).fetch_all()
    print(f"qty > 4: {[i.name for i in in_stock]}")

    first = await db.select(Item).order("qty", "DESC").fetch_first()
    if first:
        print(f"Most stock: {first.name} ({first.qty})")

    count = await db.select(Item).filter(qty__lt=6).count()
    print(f"Low-stock count: {count}")

    has_apple = await db.select(Item).filter(name__eq="Apple").exists()
    print(f"Apple exists: {has_apple}")

    await db.close()

asyncio.run(main())
# --8<-- [end:async-query]
```

### Async Terminal Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `await .fetch_all()` | `list[T]` | All matching records |
| `await .fetch_one()` | `T \| None` | First match or None |
| `await .fetch_first()` | `T \| None` | First by ordering |
| `await .fetch_last()` | `T \| None` | Last by ordering |
| `await .fetch_dicts()` | `list[dict]` | Results as dicts (field selection) |
| `await .count()` | `int` | Number of matching records |
| `await .exists()` | `bool` | True if any match found |
| `await .delete()` | `int` | Deletes matches, returns count |
| `await .update(values)` | `int` | Bulk-updates matches, returns count |

---

## FK Lazy Loading

This is the most important difference between sync and async mode. In sync mode,
accessing `book.author` triggers an automatic lazy load. In async mode, FK fields
return an `AsyncLazyLoader` object — you must explicitly call
`await loader.fetch()` to retrieve the related object.

```python
# --8<-- [start:async-fk-lazy]
import asyncio
from sqliter.asyncio import AsyncSqliterDB
from sqliter.asyncio.orm import AsyncBaseDBModel, AsyncForeignKey

class Author(AsyncBaseDBModel):
    name: str

class Book(AsyncBaseDBModel):
    title: str
    author: AsyncForeignKey[Author] = AsyncForeignKey(Author)

async def main():
    db = AsyncSqliterDB(memory=True)
    await db.create_table(Author)
    await db.create_table(Book)

    tolkien = await db.insert(Author(name="J.R.R. Tolkien"))
    book = await db.insert(Book(title="The Hobbit", author=tolkien))

    # Re-fetch to simulate loading from DB (no in-memory state)
    fresh = await db.get(Book, book.pk)

    # WRONG — raises AttributeError in async mode:
    # fresh.author.name
    # AttributeError: Async foreign key 'name' is not loaded.
    #   Use `await relation.fetch()` first.

    # CORRECT — get the loader, then await it
    loader = fresh.author    # AsyncLazyLoader (not the Author yet)
    author = await loader.fetch()    # now we have the Author
    print(f"Book: {fresh.title}")
    print(f"Author: {author.name}")
    print("Loaded via: await book.author.fetch()")

    await db.close()

asyncio.run(main())
# --8<-- [end:async-fk-lazy]
```

!!! warning "Async FK access is always explicit"
    Unlike sync mode where `book.author.name` triggers an automatic database
    query, in async mode you **must** call `await book.author.fetch()` first.
    Accessing any attribute on an unloaded `AsyncLazyLoader` raises:

    ```
    AttributeError: Async foreign key 'name' is not loaded.
      Use `await relation.fetch()` first.
    ```

    This is intentional — hidden I/O inside property access is not safe in
    async code.

### Sync vs Async FK Access

| | Sync | Async |
|-|------|-------|
| **Model base** | `BaseDBModel` | `AsyncBaseDBModel` |
| **FK field** | `ForeignKey[T]` | `AsyncForeignKey[T]` |
| **Access pattern** | `book.author.name` | `author = await book.author.fetch()` then `author.name` |
| **Already loaded?** | Cached automatically | Cached after first `fetch()` |

---

## FK Eager Loading

Use `select_related()` to load the FK in the same query via a JOIN. The related
object is immediately available without any extra `fetch()` call — the closest
async equivalent to sync lazy loading ergonomics.

```python
# --8<-- [start:async-fk-eager]
import asyncio
from sqliter.asyncio import AsyncSqliterDB
from sqliter.asyncio.orm import AsyncBaseDBModel, AsyncForeignKey

class Author(AsyncBaseDBModel):
    name: str

class Book(AsyncBaseDBModel):
    title: str
    author: AsyncForeignKey[Author] = AsyncForeignKey(Author)

async def main():
    db = AsyncSqliterDB(memory=True)
    await db.create_table(Author)
    await db.create_table(Book)

    austen = await db.insert(Author(name="Jane Austen"))
    await db.insert(Book(title="Pride and Prejudice", author=austen))
    await db.insert(Book(title="Emma", author=austen))

    # select_related performs a JOIN — author is loaded immediately
    books = await db.select(Book).select_related("author").fetch_all()
    for b in books:
        # No await needed — already loaded via JOIN
        print(f"  {b.title} by {b.author.name}")

    print(f"\nLoaded {len(books)} books with eager FK")

    await db.close()

asyncio.run(main())
# --8<-- [end:async-fk-eager]
```

### When to Use Each Approach

| Approach | When to use |
|----------|-------------|
| **Lazy** (`await loader.fetch()`) | You only sometimes need the related object, or are fetching a large list where not every item needs its FK |
| **Eager** (`select_related()`) | You know you will always access the related object — avoids N+1 queries |

---

## Reverse Relationships

When a `AsyncForeignKey` has `related_name` set, the related model gains a
reverse accessor. In async mode this returns an `AsyncReverseQuery` — call
`await accessor.fetch_all()` (or any other terminal method) to get results.

```python
# --8<-- [start:async-reverse]
import asyncio
from sqliter.asyncio import AsyncSqliterDB
from sqliter.asyncio.orm import AsyncBaseDBModel, AsyncForeignKey

class Author(AsyncBaseDBModel):
    name: str

class Book(AsyncBaseDBModel):
    title: str
    author: AsyncForeignKey[Author] = AsyncForeignKey(
        Author, related_name="books"
    )

async def main():
    db = AsyncSqliterDB(memory=True)
    await db.create_table(Author)
    await db.create_table(Book)

    dickens = await db.insert(Author(name="Charles Dickens"))
    await db.insert(Book(title="Oliver Twist", author=dickens))
    await db.insert(Book(title="Great Expectations", author=dickens))

    # Reverse accessor returns AsyncReverseQuery, not a list
    author = await db.get(Author, dickens.pk)
    books = await author.books.fetch_all()
    print(f"Author: {author.name}")
    print(f"Books ({len(books)}):")
    for b in books:
        print(f"  - {b.title}")

    count = await author.books.count()
    print(f"Total via .count(): {count}")

    await db.close()

asyncio.run(main())
# --8<-- [end:async-reverse]
```

### What Happens

`author.books` returns an `AsyncReverseQuery` — a lazy query builder, not a
list. Only when you call a terminal method (`fetch_all()`, `fetch_one()`,
`count()`, `exists()`) is the database queried. You can also call `.filter()`
on it before fetching to narrow the results.

---

## Async Transactions

The `async with db:` context manager provides the same atomic transaction
semantics as the sync version: commits on clean exit, rolls back on any
unhandled exception.

```python
# --8<-- [start:async-txn]
import asyncio
import tempfile
from pathlib import Path
from sqliter.asyncio import AsyncSqliterDB
from sqliter.model import BaseDBModel

class Account(BaseDBModel):
    name: str
    balance: float

async def main():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    db = AsyncSqliterDB(db_filename=db_path)
    await db.create_table(Account)

    alice = await db.insert(Account(name="Alice", balance=100.0))
    print(f"Initial: Alice=${alice.balance}")

    try:
        async with db:
            alice.balance -= 50.0
            await db.update(alice)
            print("Inside txn: deducted $50")
            raise RuntimeError("Simulated payment failure")
    except RuntimeError:
        print("Error — transaction rolled back")

    # Verify with a fresh connection
    db2 = AsyncSqliterDB(db_filename=db_path)
    restored = await db2.get(Account, alice.pk)
    if restored is not None:
        print(f"Restored: Alice=${restored.balance}")
        if restored.balance == 100.0:
            print("Rollback confirmed")
    await db2.close()
    await db.close()
    Path(db_path).unlink(missing_ok=True)

asyncio.run(main())
# --8<-- [end:async-txn]
```

### What Happens

The `async with db:` block begins an implicit transaction. When `RuntimeError`
is raised, the context manager catches it, rolls back all changes, then
re-raises. The second connection confirms the original balance was preserved.

### When to Use

Use `async with db:` whenever you need atomicity: either all operations in the
block succeed, or none are persisted.

---

## Sync vs Async Quick Reference

| Feature | Sync | Async |
|---------|------|-------|
| **Import** | `from sqliter import SqliterDB` | `from sqliter.asyncio import AsyncSqliterDB` |
| **Model base (FK/M2M)** | `BaseDBModel` | `AsyncBaseDBModel` |
| **FK field** | `ForeignKey[T]` | `AsyncForeignKey[T]` |
| **Context manager** | `with db:` | `async with db:` |
| **Connect** | `db.connect()` | `await db.connect()` |
| **Create table** | `db.create_table(M)` | `await db.create_table(M)` |
| **Insert** | `db.insert(obj)` | `await db.insert(obj)` |
| **Get** | `db.get(M, pk)` | `await db.get(M, pk)` |
| **Update** | `db.update(obj)` | `await db.update(obj)` |
| **Delete** | `db.delete(M, pk)` | `await db.delete(M, pk)` |
| **Bulk insert** | `db.bulk_insert([...])` | `await db.bulk_insert([...])` |
| **Query terminal** | `.fetch_all()` | `await .fetch_all()` |
| **FK access** | `book.author.name` | `author = await book.author.fetch()` |
| **Eager FK** | `.select_related("x")` | `await .select_related("x").fetch_all()` |
| **Reverse FK** | `author.books.fetch_all()` | `await author.books.fetch_all()` |

## Related Documentation

- [Async Guide](../guide/asyncio.md) - Full async usage guide
- [AsyncSqliterDB API](../api-reference/async-sqliterdb.md) - API reference
- [AsyncQueryBuilder API](../api-reference/async-query-builder.md) - Query builder reference
- [Async ORM API](../api-reference/async-orm.md) - FK, reverse, M2M async API
- [Connection Demos](connection.md) - Sync connection patterns
- [ORM Features](orm.md) - Sync ORM and relationship demos
- [Transactions](transactions.md) - Sync transaction demos
