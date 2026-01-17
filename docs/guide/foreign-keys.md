# Foreign Keys

Foreign keys allow you to define relationships between models, enabling
referential integrity in your database. When you define a foreign key, SQLiter
ensures that the referenced record exists and automatically handles actions when
the referenced record is deleted or updated.

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
    author_id: int = ForeignKey(Author, on_delete="CASCADE")

db = SqliterDB(":memory:")
db.create_table(Author)
db.create_table(Book)
```

> [!IMPORTANT]
>
> The referenced table (`Author`) must be created **before** the table that
> references it (`Book`).

### Foreign Key Naming Convention

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

## Foreign Key Actions

Foreign keys support actions that define what happens when the referenced record
is deleted (`on_delete`) or updated (`on_update`). The following actions are
available:

### CASCADE

When the referenced record is deleted, all records that reference it are also
deleted. When the referenced record's primary key is updated, the foreign key
values are updated to match:

```python
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
    author_id: Annotated[
        int,
        ForeignKey(Author, on_delete="SET NULL", null=True)
    ] = None
```

> [!IMPORTANT]
>
> You must set `null=True` when using `SET NULL`. SQLiter will raise a
> `ValueError` if you try to use `SET NULL` without `null=True`.

### RESTRICT

Prevents deletion or update of the referenced record if other records reference
it. This is the default behavior in SQLite when foreign keys are enabled:

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
from typing import Annotated

class Book(BaseDBModel):
    title: str
    author_id: Annotated[
        int,
        ForeignKey(Author, on_delete="SET NULL", null=True)
    ] = None

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
    author_id: int = ForeignKey(Author, on_delete="CASCADE")

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

## Future Enhancements

Phase 1 of foreign key support (current implementation) focuses on constraint
enforcement and explicit `_id` field access. Phase 2 will add ORM-style
conveniences such as:

- Lazy loading: `book.author.name` instead of `book.author_id`
- Reverse relationships: `author.books.fetch_all()`
- String references for forward references

See the [TODO](../todo/index.md) for more details on planned enhancements.
