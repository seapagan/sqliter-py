# Explicit Foreign Keys

This page covers the explicit foreign key approach where you define `_id` fields
directly and manage relationships manually. This is the simpler, lower-overhead
approach with full control over foreign key values.

For the ORM-style approach with lazy loading and reverse relationships, see
[ORM Foreign Keys](orm.md).

## Defining Foreign Keys

To define a foreign key, use the `ForeignKey()` function when declaring a model
field. The foreign key field stores the primary key (`pk`) of the referenced
model:

```python
from typing import Annotated
from sqliter import SqliterDB
from sqliter.model import BaseDBModel, ForeignKey

class Author(BaseDBModel):
    name: str
    email: str

class Book(BaseDBModel):
    title: str
    author_id: int = ForeignKey(
        Author,
        on_delete="CASCADE",
        on_update="CASCADE"
    )

db = SqliterDB(":memory:")
db.create_table(Author)
db.create_table(Book)
```

> [!IMPORTANT]
>
> The referenced table (`Author`) must be created **before** the table that
> references it (`Book`).

> [!NOTE]
>
> The default foreign key action is `RESTRICT` for both `on_delete` and
> `on_update`. This means that by default, SQLiter will prevent deletion or
> updates of referenced records if other records reference them. This is the
> safest behavior and matches SQLite's default. You must explicitly specify
> `on_delete="CASCADE"` or `on_update="CASCADE"` if you want cascading
> behavior.

## Foreign Key Naming Convention

By default, the foreign key column in the database will be named
`{field_name}_id`. In the example above, the field `author_id` creates a column
named `author_id` in the `books` table.

You can customize the column name using the `db_column` parameter:

```python
class Book(BaseDBModel):
    title: str
    author_id: int = ForeignKey(
        Author,
        db_column="writer_id",
        on_delete="CASCADE"
    )
```

## Type Checking

The examples in this documentation show the simplest syntax that works at
runtime and with most type checkers:

```python
author_id: int = ForeignKey(
    Author,
    on_delete="CASCADE",
    on_update="CASCADE"
)
author_id: int | None = ForeignKey(
    Author, on_delete="SET NULL", null=True, default=None
)
```

If you use strict type checking with `mypy`, you can wrap the type and
`ForeignKey()` with `Annotated` for explicit type metadata:

```python
from typing import Annotated

author_id: Annotated[
    int,
    ForeignKey(Author, on_delete="CASCADE", on_update="CASCADE")
]
author_id: Annotated[
    int | None,
    ForeignKey(Author, on_delete="SET NULL", null=True)
] = None
```

This is optional for foreign keys but required for the `unique()` constraint
(see [Models](../models.md#unique-fields)).

## Foreign Key Actions

Foreign keys support actions that define what happens when the referenced record
is deleted (`on_delete`) or updated (`on_update`). The following actions are
available:

### CASCADE

When the referenced record is deleted, all records that reference it are also
deleted. When the referenced record's primary key is updated, the foreign key
values are updated to match. You must explicitly specify `on_delete="CASCADE"`
and `on_update="CASCADE"` to use this behavior:

```python
class Book(BaseDBModel):
    title: str
    author_id: int = ForeignKey(
        Author,
        on_delete="CASCADE",
        on_update="CASCADE"
    )

author = db.insert(Author(name="Jane Austen", email="jane@example.com"))
book = db.insert(Book(title="Pride and Prejudice", author_id=author.pk))

# Deleting the author will also delete the book
db.delete(Author, author.pk)

# The book is now deleted too
books = db.select(Book).filter(author_id=author.pk).fetch_all()
assert len(books) == 0
```

### SET NULL

When the referenced record is deleted or updated, the foreign key field is set
to `NULL`. This requires `null=True`:

```python
class Book(BaseDBModel):
    title: str
    author_id: int | None = ForeignKey(
        Author, on_delete="SET NULL", null=True, default=None
    )
```

> [!IMPORTANT]
>
> You must set `null=True` when using `SET NULL`. SQLiter will raise a
> `ValueError` if you try to use `SET NULL` without `null=True`.

### RESTRICT

Prevents deletion or update of the referenced record if other records reference
it. This is the **default** behavior in SQLiter and matches SQLite's default when
foreign keys are enabled:

```python
class Book(BaseDBModel):
    title: str
    author_id: int = ForeignKey(Author, on_delete="RESTRICT")

author = db.insert(Author(name="Jane Austen", email="jane@example.com"))
book = db.insert(Book(title="Pride and Prejudice", author_id=author.pk))

# This will raise a ForeignKeyConstraintError
db.delete(Author, author.pk)
```

### NO ACTION

Similar to `RESTRICT` in SQLite. The deletion or update is prevented if other
records reference the record:

```python
class Book(BaseDBModel):
    title: str
    author_id: int = ForeignKey(Author, on_delete="NO ACTION")
```

## Nullable Foreign Keys

By default, foreign key fields are required (NOT NULL). You can make them
optional by setting `null=True`:

```python
class Book(BaseDBModel):
    title: str
    author_id: int | None = ForeignKey(
        Author, on_delete="SET NULL", null=True, default=None
    )

# Insert a book without an author
book = db.insert(Book(title="Anonymous Book", author_id=None))
```

## One-to-One Relationships

To create a one-to-one relationship, use `unique=True`:

```python
class Book(BaseDBModel):
    title: str
    author_id: int = ForeignKey(Author, unique=True)
```

This ensures that each author can be referenced by only one book.

## Querying with Foreign Keys

You can filter records using the foreign key column:

```python
# Get all books by a specific author
books = db.select(Book).filter(author_id=author.pk).fetch_all()

# Get all books without an author
orphaned_books = db.select(Book).filter(author_id=None).fetch_all()
```

## Automatic Indexing

SQLiter automatically creates an index on foreign key columns to improve query
performance. This is done when you create the table:

```python
db.create_table(Book)  # Automatically creates index on author_id
```

## Foreign Key Errors

SQLiter provides specific exceptions for foreign key constraint violations:

- `ForeignKeyConstraintError`: Raised when a foreign key constraint is violated,
  such as trying to delete a record that is referenced by other records with
  `RESTRICT` or `NO ACTION` action.
- `InvalidForeignKeyError`: Raised when an invalid foreign key configuration is
  detected, such as using `SET NULL` without `null=True`.

## Complete Example

Here's a complete example showing foreign key usage with CASCADE deletion:

```python
from sqliter import SqliterDB
from sqliter.model import BaseDBModel, ForeignKey

class Author(BaseDBModel):
    name: str
    email: str

class Book(BaseDBModel):
    title: str
    author_id: int = ForeignKey(
        Author,
        on_delete="CASCADE",
        on_update="CASCADE"
    )

# Create database and tables
db = SqliterDB(":memory:")
db.create_table(Author)
db.create_table(Book)

# Insert an author
author = db.insert(Author(
    name="Jane Austen",
    email="jane@example.com"
))

# Insert books by this author
book1 = db.insert(Book(
    title="Pride and Prejudice",
    author_id=author.pk
))
book2 = db.insert(Book(
    title="Sense and Sensibility",
    author_id=author.pk
))

# Query books by author
jane_books = db.select(Book).filter(author_id=author.pk).fetch_all()
print(f"Jane has {len(jane_books)} books")

# Delete the author (CASCADE will delete the books)
db.delete(Author, author.pk)

# Verify books are deleted
remaining_books = db.select(Book).fetch_all()
assert len(remaining_books) == 0
```
