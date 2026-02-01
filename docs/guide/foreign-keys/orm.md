# ORM Foreign Keys

ORM-style foreign keys provide lazy loading and reverse relationships, similar
to Django or SQLAlchemy. This approach allows you to access related objects
directly (e.g., `book.author.name`) without manual queries.

For the simpler explicit approach with manual ID management, see
[Explicit Foreign Keys](explicit.md).

## Defining ORM Foreign Keys

Import from `sqliter.orm` instead of `sqliter.model`:

```python
from sqliter import SqliterDB
from sqliter.orm import BaseDBModel, ForeignKey

class Author(BaseDBModel):
    name: str
    email: str

class Book(BaseDBModel):
    title: str
    author: ForeignKey[Author] = ForeignKey(Author, on_delete="CASCADE")

db = SqliterDB(":memory:")
db.create_table(Author)
db.create_table(Book)
```

> [!NOTE]
>
> When using ORM foreign keys, SQLiter automatically creates an `author_id`
> field in the database. You define `author` (without `_id`) in your model and
> access it for lazy loading.

## Database Context

ORM features require a database context to execute queries. SQLiter
automatically sets `db_context` on model instances returned from database
operations:

```python
# db_context is set automatically
book = db.get(Book, 1)
print(book.author.name)  # Works - db_context was set by db.get()

# Manual instances need db_context set explicitly
book = Book(title="My Book", author_id=1)
book.db_context = db  # Set manually for lazy loading to work
print(book.author.name)
```

## Lazy Loading

When you access a foreign key field, SQLiter automatically loads the related
object from the database:

```python
# Insert data
author = db.insert(Author(name="Jane Austen", email="jane@example.com"))
book = db.insert(Book(title="Pride and Prejudice", author=author))

# Fetch the book
book = db.get(Book, book.pk)

# Lazy loading - queries database on first access
print(book.author.name)  # "Jane Austen"
print(book.author.email)  # "jane@example.com"
```

The related object is only loaded when you access an attribute. If you never
access `book.author`, no additional query is made.

## Caching Behavior

Once loaded, the related object is cached on the instance. Repeated access
returns the same object:

```python
book = db.get(Book, 1)

# First access loads from database
author1 = book.author
# Second access returns cached object (no query)
author2 = book.author

# Same object instance
assert author1 is author2
```

## Performance Considerations

### The N+1 Query Problem

When iterating over multiple objects and accessing their foreign key relationships,
you can encounter the **N+1 query problem**. This happens when you make 1 query
to fetch N objects, then N additional queries to fetch each related object:

```python
# Fetch 100 books (1 query)
books = db.select(Book).fetch_all()

# Accessing author for each book triggers a separate query (100 queries!)
for book in books:
    print(f"{book.title} by {book.author.name}")  # ⚠️ N+1 problem
```

In this example, SQLiter makes 101 database queries total: 1 to fetch all books,
then 100 more queries (one per book) to fetch each author.

### Eager Loading with select_related()

Use `select_related()` to fetch related objects in a single JOIN query instead
of lazy loading:

```python
# Fetch books with authors in ONE query
books = db.select(Book).select_related("author").fetch_all()

# Access authors without triggering additional queries
for book in books:
    print(f"{book.title} by {book.author.name}")  # ✅ No N+1 problem
```

This executes a single JOIN query instead of 101 separate queries (1 for books,
100 for authors).

#### Single-Level Relationships

```python
# Load single relationship
book = db.select(Book).select_related("author").fetch_one()
print(book.author.name)  # "Jane Austen" - already loaded
```

#### Nested Relationships

```python
class Comment(BaseDBModel):
    text: str
    book: ForeignKey[Book] = ForeignKey(Book, on_delete="CASCADE")

db.create_table(Comment)

# Load nested relationships using double underscore
comment = db.select(Comment).select_related("book__author").fetch_one()
print(comment.book.author.name)  # "Jane" - already loaded
```

#### Multiple Relationships

```python
class Publisher(BaseDBModel):
    name: str

class Book(BaseDBModel):
    title: str
    author: ForeignKey[Author] = ForeignKey(Author, on_delete="CASCADE")
    publisher: ForeignKey[Publisher] = ForeignKey(Publisher, on_delete="CASCADE")

# Load multiple relationships at once
book = db.select(Book).select_related("author", "publisher").fetch_one()
print(f"{book.title} by {book.author.name} from {book.publisher.name}")
```

### Eager Loading Reverse Relationships with prefetch_related()

`select_related()` solves the N+1 problem for **forward** FK relationships
(e.g., `book.author`) using JOINs. For **reverse** relationships (e.g.,
`author.books`), use `prefetch_related()` instead. It executes a second query
to fetch all related objects and maps them back to the parent instances:

```python
# Fetch authors with all their books prefetched (2 queries total)
authors = db.select(Author).prefetch_related("books").fetch_all()

for author in authors:
    # No additional query - data is already loaded
    print(f"{author.name} wrote {author.books.count()} books")
    for book in author.books.fetch_all():
        print(f"  - {book.title}")
```

Without `prefetch_related()`, the loop above would execute 1 + N queries (one
per author). With it, only 2 queries run regardless of how many authors exist.

#### Multiple Prefetch Paths

You can prefetch several reverse relationships at once:

```python
authors = (
    db.select(Author)
    .prefetch_related("books", "reviews")
    .fetch_all()
)

for author in authors:
    print(f"{author.name}: {author.books.count()} books, "
          f"{author.reviews.count()} reviews")
```

#### Combining with select_related()

`prefetch_related()` and `select_related()` can coexist on the same query.
Use `select_related()` for forward FKs and `prefetch_related()` for reverse
FKs:

```python
authors = (
    db.select(Author)
    .select_related("publisher")     # forward FK - JOIN
    .prefetch_related("books")       # reverse FK - 2nd query
    .fetch_all()
)
```

#### Chaining with filter, order, and limit

`prefetch_related()` works with all standard query methods:

```python
authors = (
    db.select(Author)
    .filter(name__startswith="J")
    .prefetch_related("books")
    .order("name")
    .limit(10)
    .fetch_all()
)
```

#### Prefetched Data API

Accessing a prefetched reverse relationship returns a `PrefetchedResult`
instead of the usual `ReverseQuery`. It provides the same read interface:

```python
author.books.fetch_all()   # list of Book instances
author.books.fetch_one()   # first Book or None
author.books.count()       # number of books
author.books.exists()      # True if any books exist
```

If you call `filter()` on a prefetched relationship, it falls back to a real
database query:

```python
# Falls back to a DB query with a WHERE clause
recent = author.books.filter(year__gt=2000).fetch_all()
```

> [!NOTE]
>
> `prefetch_related()` only works with **reverse** FK relationships and M2M
> relationships. For forward FKs (e.g., `book.author`), use
> `select_related()` instead. Passing a forward FK path raises
> `InvalidPrefetchError`.

> [!TIP]
>
> `prefetch_related()` also works with many-to-many relationships. See
> [Many-to-Many](../many-to-many.md#eager-loading-with-prefetch_related) for
> details.

### Relationship Filter Traversal

Filter on related object fields using double underscore (`__`) syntax:

```python
# Filter by related field
books = db.select(Book).filter(author__name="Jane Austen").fetch_all()

# Supports all comparison operators
books = db.select(Book).filter(author__name__like="Jane%").fetch_all()
books = db.select(Book).filter(author__name__in=["Jane", "Charles"]).fetch_all()

# Works with nested relationships
comments = db.select(Comment).filter(book__author__name="Charles").fetch_all()
```

This automatically adds the necessary JOINs behind the scenes.

#### Combining with select_related()

You can combine eager loading with relationship filters:

```python
# Load related objects AND filter by them
results = (
    db.select(Book)
    .select_related("author")
    .filter(author__name__startswith="J")
    .fetch_all()
)

for book in results:
    print(f"{book.title} by {book.author.name}")  # No additional query
```

> [!NOTE]
>
> `select_related()` only works with ORM foreign keys (`sqliter.orm.ForeignKey`).
> For explicit foreign keys, use manual joins or separate queries.

> [!TIP]
>
> Always use `select_related()` when you know you'll need related data in a loop.
> Lazy loading is convenient for single objects or conditional access, but eager
> loading prevents N+1 queries in most scenarios.

## Null Foreign Keys

When a foreign key is null, accessing it returns `None` directly:

```python
class Book(BaseDBModel):
    title: str
    author: ForeignKey[Optional[Author]] = ForeignKey(
        Author, on_delete="SET NULL"
    )

# Insert book without author
book = db.insert(Book(title="Anonymous", author=None))
book = db.get(Book, book.pk)

# Returns None for null FK
print(book.author)  # None
```

### Auto-Detecting Nullable FKs (Preferred)

The recommended way to declare a nullable FK is via the type annotation.
SQLiter detects `Optional[T]` and `T | None` (Python 3.10+) and sets
`null=True` automatically:

```python
from typing import Optional

# Preferred — nullability declared in the type annotation:
author: ForeignKey[Optional[Author]] = ForeignKey(Author, on_delete="SET NULL")
author: ForeignKey[Author | None] = ForeignKey(Author, on_delete="SET NULL")  # 3.10+

# Legacy — explicit null=True (prefer annotation-driven nullability):
author: ForeignKey[Author] = ForeignKey(Author, on_delete="SET NULL", null=True)
```

> [!NOTE]
>
> If you pass `null=True` explicitly, it always takes effect regardless of the
> annotation.
>
> For reliable type-hint resolution, define ORM models at **module scope**.
> Models defined inside functions may not resolve annotations when using
> type aliases (e.g., `AuthorRef = Optional[Author]`), so prefer `null=True`
> in those cases.

## Setting Foreign Key Values

You can set foreign key values using a model instance, an integer ID, or `None`:

```python
# Using model instance
book.author = author

# Using integer ID
book.author = 42

# Setting to null (if allowed)
book.author = None

# Any object with a `pk` attribute also works (duck-typed)
book.author = some_obj_with_pk

# Example: custom object with pk attribute
class AuthorReference:
    def __init__(self, pk: int):
        self.pk = pk

book.author = AuthorReference(pk=42)  # Works!
```

## Reverse Relationships

ORM foreign keys automatically create reverse relationships on the related
model. This lets you query all related objects from the other side:

```python
# Get all books by an author
author = db.get(Author, author.pk)
books = author.books.fetch_all()

for book in books:
    print(book.title)
```

### Available Methods

Reverse relationships provide these methods:

```python
# Fetch all related objects
books = author.books.fetch_all()

# Fetch single related object
book = author.books.fetch_one()

# Count related objects
count = author.books.count()

# Check if any exist
has_books = author.books.exists()
```

### Filtering Reverse Relationships

You can filter reverse relationships before fetching:

```python
# Filter by field values
python_books = author.books.filter(title__like="Python%").fetch_all()

# Multiple filters
recent_python = author.books.filter(
    title__like="Python%",
    year__ge=2020
).fetch_all()

# With limit and offset
first_five = author.books.limit(5).fetch_all()
next_five = author.books.offset(5).limit(5).fetch_all()
```

### Custom Related Name

By default, the reverse relationship is named by pluralizing the model name
(e.g., `Book` becomes `books`). If the `inflect` library is installed, it
provides grammatically correct pluralization (e.g., `Person` becomes `people`,
`Category` becomes `categories`). Otherwise, a simple "s" suffix is added.

You can customize this with the `related_name` parameter:

```python
class Book(BaseDBModel):
    title: str
    author: ForeignKey[Author] = ForeignKey(
        Author,
        on_delete="CASCADE",
        related_name="publications"
    )

# Now use the custom name
author.publications.fetch_all()
```

## Cascade Delete Behavior

With `on_delete="CASCADE"`, deleting a parent record automatically deletes all
related child records:

```python
class Book(BaseDBModel):
    title: str
    author: ForeignKey[Author] = ForeignKey(Author, on_delete="CASCADE")

# Insert author with books
author = db.insert(Author(name="Jane", email="jane@example.com"))
db.insert(Book(title="Book 1", author=author))
db.insert(Book(title="Book 2", author=author))

# Delete author - books are automatically deleted
db.delete(Author, author.pk)

# No books remain
assert db.select(Book).count() == 0
```

## Foreign Key Actions

ORM foreign keys support the same actions as explicit foreign keys:

| Action | Behavior |
|--------|----------|
| `CASCADE` | Delete/update related records |
| `SET NULL` | Set foreign key to NULL (requires nullable FK) |
| `RESTRICT` | Prevent deletion/update if referenced (default) |
| `NO ACTION` | Same as RESTRICT in SQLite |

```python
# CASCADE - delete books when author is deleted
author: ForeignKey[Author] = ForeignKey(Author, on_delete="CASCADE")

# SET NULL - set author to NULL when deleted
author: ForeignKey[Optional[Author]] = ForeignKey(
    Author, on_delete="SET NULL"
)

# RESTRICT - prevent deletion if books exist (default)
author: ForeignKey[Author] = ForeignKey(Author, on_delete="RESTRICT")
```

## Common Issues and Gotchas

### Database Context Not Set

Lazy loading requires `db_context` to be set on the model instance. SQLiter
automatically sets this for objects returned from database operations, but
manually created instances need it set explicitly:

```python
# ❌ Won't work - no db_context
book = Book(title="Manual Book", author_id=1)
print(book.author.name)  # AttributeError: 'NoneType' has no attribute 'name'

# ✅ Works - db_context set manually
book = Book(title="Manual Book", author_id=1)
book.db_context = db
print(book.author.name)  # Now works!

# ✅ Automatic - db operations set db_context
book = db.get(Book, 1)
print(book.author.name)  # Works automatically
```

**When `db_context` is set automatically:**

+ `db.insert()` - Returns instance with `db_context` set
+ `db.get()` - Returns instance with `db_context` set
+ `db.select().fetch_all()` - All instances have `db_context` set
+ `db.select().fetch_one()` - Instance has `db_context` set

**When you need to set it manually:**

+ Creating instances with `Model(...)` constructor
+ Deserializing objects from JSON or other sources
+ Using objects in contexts where they weren't retrieved from the database

### LazyLoader Not Hashable

Foreign key fields return `LazyLoader` proxy objects, which are **not hashable**.
This means you cannot use them in sets or as dictionary keys:

```python
book = db.get(Book, 1)

# ❌ Won't work - LazyLoader is unhashable
authors_set = {book.author}  # TypeError: unhashable type: 'LazyLoader'

# ❌ Won't work - Can't use as dict key
author_map = {book.author: book}  # TypeError: unhashable type: 'LazyLoader'

# ✅ Works - Access the underlying object's pk
authors_set = {book.author.pk}

# ✅ Works - Store the ID instead
author_map = {book.author_id: book}

# ✅ Works - Build dict from author objects after loading
authors = [book.author for book in books]  # Triggers loading
author_map = {author.pk: author for author in authors}
```

**Why unhashable?** `LazyLoader` uses mutable equality (based on the cached
object), which violates Python's hash/equality contract. Setting `__hash__ = None`
prevents subtle bugs where two "equal" objects have different hashes.

### Stale Cache After Manual Updates

If you modify the foreign key ID field directly and then access the relationship,
the cache is automatically cleared. However, external database changes won't be
reflected:

```python
book = db.get(Book, 1)
author_name = book.author.name  # Caches author object

# Another process/connection updates the author record
# book.author still returns cached (stale) data

# ✅ To get fresh data, re-fetch the book
book = db.get(Book, 1)
author_name = book.author.name  # Fetches latest author data
```

### Foreign Keys in Filters

When filtering by foreign key relationships, you have several options:

```python
# ✅ Works - filter by _id field
books = db.select(Book).filter(author_id=author.pk).fetch_all()

# ✅ Also works - use the ID directly
books = db.select(Book).filter(author_id=42).fetch_all()

# ✅ NEW - Filter by related model fields (requires ORM FK)
books = db.select(Book).filter(author__name="Jane Austen").fetch_all()
```

The relationship filter traversal (e.g., `author__name`) only works with
`sqliter.orm.ForeignKey` and automatically joins the related tables.

## Complete Example

Here's a complete example demonstrating ORM foreign keys with lazy loading and
reverse relationships:

```python
from sqliter import SqliterDB
from sqliter.orm import BaseDBModel, ForeignKey

class Author(BaseDBModel):
    name: str
    email: str

class Book(BaseDBModel):
    title: str
    year: int
    author: ForeignKey[Author] = ForeignKey(Author, on_delete="CASCADE")

# Create database and tables
db = SqliterDB(":memory:")
db.create_table(Author)
db.create_table(Book)

# Insert an author
author = db.insert(Author(
    name="Jane Austen",
    email="jane@example.com"
))

# Insert books - can use model instance directly
book1 = db.insert(Book(
    title="Pride and Prejudice",
    year=1813,
    author=author
))
book2 = db.insert(Book(
    title="Sense and Sensibility",
    year=1811,
    author=author
))

# Lazy loading - access author through book
book = db.get(Book, book1.pk)
print(f"'{book.title}' by {book.author.name}")
# Output: 'Pride and Prejudice' by Jane Austen

# Reverse relationship - access books through author
author = db.get(Author, author.pk)
print(f"{author.name} wrote {author.books.count()} books:")
for book in author.books.fetch_all():
    print(f"  - {book.title} ({book.year})")
# Output:
# Jane Austen wrote 2 books:
#   - Pride and Prejudice (1813)
#   - Sense and Sensibility (1811)

# Filter reverse relationship
early_books = author.books.filter(year__lt=1812).fetch_all()
print(f"Books before 1812: {len(early_books)}")
# Output: Books before 1812: 1

# Cascade delete
db.delete(Author, author.pk)
assert db.select(Book).count() == 0  # All books deleted
```
