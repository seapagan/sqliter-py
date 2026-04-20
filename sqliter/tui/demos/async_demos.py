"""Async Support demos."""

from __future__ import annotations

import asyncio
import concurrent.futures
import io
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from sqliter.model import BaseDBModel
from sqliter.tui.demos.base import Demo, DemoCategory, extract_demo_code

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable, Coroutine

    from sqliter.asyncio.orm import AsyncLazyLoader

try:
    from sqliter.asyncio import AsyncSqliterDB
    from sqliter.asyncio.orm import (
        AsyncBaseDBModel,
        AsyncForeignKey,
        AsyncReverseQuery,
    )

    _ASYNC_AVAILABLE = True
except ImportError:
    _ASYNC_AVAILABLE = False


def _run_async(coro: Coroutine[Any, Any, None]) -> None:
    """Run a coroutine in a fresh thread with its own event loop.

    asyncio.run() fails when Textual's event loop is already running.
    Running in a separate thread sidesteps that restriction.
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        pool.submit(asyncio.run, coro).result()


def _unavailable(name: str) -> str:
    """Return a helpful message when aiosqlite is not installed."""
    return (
        f"Async demo '{name}' requires aiosqlite.\n\n"
        "Install with:\n"
        "  pip install sqliter-py[async]\n"
        "         or:\n"
        "  pip install sqliter-py[full]\n"
    )


def _run_async_conn() -> str:
    """Create an async in-memory database connection.

    Use AsyncSqliterDB for async operations — all connection methods
    require await. The constructor parameters are identical to SqliterDB.
    """
    if not _ASYNC_AVAILABLE:
        return _unavailable("Async Connection")

    output = io.StringIO()

    async def main() -> None:
        db = AsyncSqliterDB(memory=True)
        output.write(f"Created database: {db}\n")
        output.write(f"Is memory: {db.is_memory}\n")
        output.write(f"Filename: {db.filename}\n")

        await db.connect()
        output.write(f"Connected: {db.is_connected}\n")

        await db.close()
        output.write(f"After close: {db.is_connected}\n")

    _run_async(main())
    return output.getvalue()


def _run_async_context() -> str:
    """Use async context manager for automatic transaction management.

    The `async with db:` block handles transaction scope. Note: you must use
    `async with`, not `with`.
    """
    if not _ASYNC_AVAILABLE:
        return _unavailable("Async Context Manager")

    output = io.StringIO()

    class Task(BaseDBModel):
        title: str
        done: bool = False

    async def main() -> None:
        db = AsyncSqliterDB(memory=True)

        async with db:
            await db.create_table(Task)
            task = await db.insert(Task(title="Learn async SQLiter"))
            output.write(f"Inserted: {task.title} (pk={task.pk})\n")
            output.write("Transaction auto-commits on exit\n")

        output.write(f"\nAfter context: connected={db.is_connected}\n")
        await db.close()

    _run_async(main())
    return output.getvalue()


def _run_async_crud() -> str:
    """Perform create, read, update, and delete with async/await.

    Every data operation — including create_table — must be awaited.
    The method signatures are otherwise identical to the sync API.
    """
    if not _ASYNC_AVAILABLE:
        return _unavailable("Async CRUD")

    output = io.StringIO()

    class Product(BaseDBModel):
        name: str
        price: float

    async def main() -> None:
        db = AsyncSqliterDB(memory=True)
        await db.create_table(Product)

        # Insert
        widget = await db.insert(Product(name="Widget", price=9.99))
        output.write(f"Inserted: {widget.name} pk={widget.pk}\n")

        # Get by primary key
        fetched = await db.get(Product, widget.pk)
        if fetched is not None:
            output.write(f"Fetched: {fetched.name}\n")

        # Update
        widget.price = 12.99
        await db.update(widget)
        updated = await db.get(Product, widget.pk)
        if updated is not None:
            output.write(f"Updated price: {updated.price}\n")

        # Delete
        await db.delete(Product, widget.pk)
        gone = await db.get(Product, widget.pk)
        output.write(f"After delete: {gone}\n")

        await db.close()

    _run_async(main())
    return output.getvalue()


def _run_async_bulk() -> str:
    """Insert multiple records in a single async transaction.

    bulk_insert batches all inserts into one transaction for better
    performance. It returns the list of inserted model instances.
    """
    if not _ASYNC_AVAILABLE:
        return _unavailable("Async Bulk Insert")

    output = io.StringIO()

    class Tag(BaseDBModel):
        label: str

    async def main() -> None:
        db = AsyncSqliterDB(memory=True)
        await db.create_table(Tag)

        tags = await db.bulk_insert(
            [
                Tag(label="python"),
                Tag(label="async"),
                Tag(label="sqlite"),
            ]
        )

        output.write(f"Inserted {len(tags)} tags:\n")
        for tag in tags:
            output.write(f"  pk={tag.pk}  {tag.label}\n")

        count = await db.select(Tag).count()
        output.write(f"\nTotal in DB: {count}\n")

        await db.close()

    _run_async(main())
    return output.getvalue()


def _run_async_query() -> str:
    """Build queries with filter, order, and pagination — all async.

    Chaining methods (filter, limit, offset, order) are synchronous.
    Terminal methods that hit the database (fetch_all, fetch_one, count,
    exists) are all coroutines and must be awaited.
    """
    if not _ASYNC_AVAILABLE:
        return _unavailable("Async Queries")

    output = io.StringIO()

    class Item(BaseDBModel):
        name: str
        qty: int

    async def main() -> None:
        db = AsyncSqliterDB(memory=True)
        await db.create_table(Item)
        await db.bulk_insert(
            [
                Item(name="Apple", qty=5),
                Item(name="Banana", qty=12),
                Item(name="Cherry", qty=3),
                Item(name="Date", qty=8),
            ]
        )

        # fetch_all, fetch_one, count, exists all require await
        all_items = await db.select(Item).fetch_all()
        output.write(f"All items: {len(all_items)}\n")

        in_stock = await db.select(Item).filter(qty__gt=4).fetch_all()
        output.write(f"qty > 4: {[i.name for i in in_stock]}\n")

        first = await db.select(Item).order("qty", "DESC").fetch_first()
        if first:
            output.write(f"Most stock: {first.name} ({first.qty})\n")

        count = await db.select(Item).filter(qty__lt=6).count()
        output.write(f"Low-stock count: {count}\n")

        has_apple = await db.select(Item).filter(name__eq="Apple").exists()
        output.write(f"Apple exists: {has_apple}\n")

        await db.close()

    _run_async(main())
    return output.getvalue()


def _run_async_fk_lazy() -> str:
    """Load related objects with explicit async fetch.

    In sync mode, accessing book.author triggers an automatic lazy load.
    In async mode, FK fields return an AsyncLazyLoader — you must call
    `await loader.fetch()` to get the related object.
    """
    if not _ASYNC_AVAILABLE:
        return _unavailable("FK Lazy Loading")

    output = io.StringIO()

    class Author(AsyncBaseDBModel):
        name: str

    class Book(AsyncBaseDBModel):
        title: str
        author: AsyncForeignKey[Author] = AsyncForeignKey(Author)

    async def main() -> None:
        db = AsyncSqliterDB(memory=True)
        try:
            await db.create_table(Author)
            await db.create_table(Book)

            tolkien = await db.insert(Author(name="J.R.R. Tolkien"))
            book = await db.insert(Book(title="The Hobbit", author=tolkien))

            # Re-fetch from DB to get a fresh instance (no in-memory cache)
            fresh = await db.get(Book, book.pk)
            if fresh is None:
                return

            # WRONG — raises AttributeError in async mode:
            # fresh.author.name
            # AttributeError: Async foreign key 'name' is not loaded.
            # Use `await relation.fetch()` first.

            # CORRECT — explicitly fetch the loader, then await it
            #
            # mypy note: AsyncForeignKey is typed to return T (Author) so
            # that eager-loaded access (book.author.name) type-checks. At
            # runtime the lazy-loaded value is AsyncLazyLoader[T], not T,
            # so strict mypy requires a cast. This is a known trade-off —
            # see the async guide for a full explanation.
            loader = cast("AsyncLazyLoader[Author]", fresh.author)
            fetched_author = await loader.fetch()
            output.write(f"Book: {fresh.title}\n")
            if fetched_author is not None:
                output.write(f"Author: {fetched_author.name}\n")
            output.write("Loaded via: await book.author.fetch()\n")
        finally:
            await db.close()

    _run_async(main())
    return output.getvalue()


def _run_async_fk_eager() -> str:
    """Load related objects in one query with select_related.

    select_related performs a JOIN so the related object is available
    immediately — no extra fetch() call needed. Best when you know you
    will always need the related data.
    """
    if not _ASYNC_AVAILABLE:
        return _unavailable("FK Eager Loading")

    output = io.StringIO()

    class Author(AsyncBaseDBModel):
        name: str

    class Book(AsyncBaseDBModel):
        title: str
        author: AsyncForeignKey[Author] = AsyncForeignKey(Author)

    async def main() -> None:
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
            output.write(f"  {b.title} by {b.author.name}\n")

        output.write(f"\nLoaded {len(books)} books with eager FK\n")

        await db.close()

    _run_async(main())
    return output.getvalue()


def _run_async_reverse() -> str:
    """Access reverse FK relationships with async query managers.

    When a FK has related_name set, the related model gets a reverse
    accessor. In async mode it returns an AsyncReverseQuery — call
    await accessor.fetch_all() to get results.
    """
    if not _ASYNC_AVAILABLE:
        return _unavailable("Reverse Relationships")

    output = io.StringIO()

    class Author(AsyncBaseDBModel):
        name: str

    class Book(AsyncBaseDBModel):
        title: str
        author: AsyncForeignKey[Author] = AsyncForeignKey(
            Author, related_name="books"
        )

    async def main() -> None:
        db = AsyncSqliterDB(memory=True)
        try:
            await db.create_table(Author)
            await db.create_table(Book)

            dickens = await db.insert(Author(name="Charles Dickens"))
            await db.insert(Book(title="Oliver Twist", author=dickens))
            await db.insert(Book(title="Great Expectations", author=dickens))

            author = await db.get(Author, dickens.pk)
            if author is None:
                return

            # mypy note: reverse accessors are set dynamically via setattr,
            # so __getattribute__ returns `object`. Cast to AsyncReverseQuery
            # for strict mypy. fetch_all() returns list[BaseDBModel], so a
            # second cast to the concrete type is also needed.
            books_query: AsyncReverseQuery = cast(
                "AsyncReverseQuery", author.books
            )
            fetched_books = cast("list[Book]", await books_query.fetch_all())
            output.write(f"Author: {author.name}\n")
            output.write(f"Books ({len(fetched_books)}):\n")
            for b in fetched_books:
                output.write(f"  - {b.title}\n")

            count = await books_query.count()
            output.write(f"Total via .count(): {count}\n")
        finally:
            await db.close()

    _run_async(main())
    return output.getvalue()


def _run_async_txn() -> str:
    """Demonstrate async transaction rollback on error.

    When an exception occurs inside `async with db:`, all changes made
    within that transaction are automatically rolled back — same
    semantics as the sync context manager.
    """
    if not _ASYNC_AVAILABLE:
        return _unavailable("Async Transactions")

    output = io.StringIO()

    class Account(BaseDBModel):
        name: str
        balance: float

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    async def main() -> None:
        db = AsyncSqliterDB(db_filename=db_path)
        await db.create_table(Account)

        alice = await db.insert(Account(name="Alice", balance=100.0))
        output.write(f"Initial: Alice=${alice.balance}\n")

        try:
            async with db:
                alice.balance -= 50.0
                await db.update(alice)
                output.write("Inside txn: deducted $50\n")
                error_msg = "Simulated payment failure"
                raise RuntimeError(error_msg)  # noqa: TRY301
        except RuntimeError:
            output.write("Error — transaction rolled back\n")

        # Verify rollback with a fresh connection
        initial_balance = 100.0
        db2 = AsyncSqliterDB(db_filename=db_path)
        restored = await db2.get(Account, alice.pk)
        if restored is not None:
            output.write(f"Restored: Alice=${restored.balance}\n")
            if restored.balance == initial_balance:
                output.write("Rollback confirmed\n")
        await db2.close()
        await db.close()

    _run_async(main())
    Path(db_path).unlink(missing_ok=True)
    return output.getvalue()


def _demo_code(func: Callable[[], str]) -> str:
    """Extract display code, stripping async demo boilerplate."""
    lines = extract_demo_code(func).splitlines()
    filtered: list[str] = []
    skip_next = False

    for line in lines:
        stripped = line.strip()

        # Skip the availability guard (if line) and its body (next line)
        if "not _ASYNC_AVAILABLE" in stripped:
            skip_next = True
            continue
        if skip_next:
            skip_next = False
            continue

        # Skip the internal run call and the file cleanup line
        if stripped.startswith("_run_async(") or ".unlink(" in stripped:
            continue

        filtered.append(line)

    # Collapse multiple consecutive blank lines into one
    result: list[str] = []
    prev_blank = False
    for line in filtered:
        is_blank = not line.strip()
        if is_blank and prev_blank:
            continue
        result.append(line)
        prev_blank = is_blank

    # Remove any leading/trailing blank lines
    while result and not result[0].strip():
        result.pop(0)
    while result and not result[-1].strip():
        result.pop()

    return "\n".join(result)


def get_category() -> DemoCategory:
    """Get the Async Support demo category."""
    return DemoCategory(
        id="async_support",
        title="Async Support",
        icon="",
        demos=[
            Demo(
                id="async_conn",
                title="Async Connection",
                description="Connect with AsyncSqliterDB using await",
                category="async_support",
                code=_demo_code(_run_async_conn),
                execute=_run_async_conn,
            ),
            Demo(
                id="async_context",
                title="Async Context Manager",
                description="Use 'async with db:' for auto commit/rollback",
                category="async_support",
                code=_demo_code(_run_async_context),
                execute=_run_async_context,
            ),
            Demo(
                id="async_crud",
                title="Async CRUD",
                description="All data operations require await",
                category="async_support",
                code=_demo_code(_run_async_crud),
                execute=_run_async_crud,
            ),
            Demo(
                id="async_bulk",
                title="Async Bulk Insert",
                description="Insert multiple records in one transaction",
                category="async_support",
                code=_demo_code(_run_async_bulk),
                execute=_run_async_bulk,
            ),
            Demo(
                id="async_query",
                title="Async Queries",
                description="Terminal query methods all require await",
                category="async_support",
                code=_demo_code(_run_async_query),
                execute=_run_async_query,
            ),
            Demo(
                id="async_fk_lazy",
                title="FK Lazy Loading",
                description="Explicit await needed — unlike sync auto-load",
                category="async_support",
                code=_demo_code(_run_async_fk_lazy),
                execute=_run_async_fk_lazy,
            ),
            Demo(
                id="async_fk_eager",
                title="FK Eager Loading",
                description="Load FK in one JOIN with select_related",
                category="async_support",
                code=_demo_code(_run_async_fk_eager),
                execute=_run_async_fk_eager,
            ),
            Demo(
                id="async_reverse",
                title="Reverse Relationships",
                description="Async reverse FK access via related_name",
                category="async_support",
                code=_demo_code(_run_async_reverse),
                execute=_run_async_reverse,
            ),
            Demo(
                id="async_txn",
                title="Async Transactions",
                description="Rollback on error with async with",
                category="async_support",
                code=_demo_code(_run_async_txn),
                execute=_run_async_txn,
            ),
        ],
    )
