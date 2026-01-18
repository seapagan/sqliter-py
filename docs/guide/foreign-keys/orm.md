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

## Null Foreign Keys

When a foreign key is null, accessing it returns `None` directly:

```python
class Book(BaseDBModel):
    title: str
    author: ForeignKey[Author] = ForeignKey(
        Author, on_delete="SET NULL", null=True
    )

# Insert book without author
book = db.insert(Book(title="Anonymous", author=None))
book = db.get(Book, book.pk)

# Returns None for null FK
print(book.author)  # None
```

## Setting Foreign Key Values

You can set foreign key values using a model instance, an integer ID, or `None`:

```python
# Using model instance
book.author = author

# Using integer ID
book.author = 42

# Setting to null (if allowed)
book.author = None
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

By default, the reverse relationship is named after the model with an "s"
suffix (e.g., `Book` becomes `books`). You can customize this:

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
| `SET NULL` | Set foreign key to NULL (requires `null=True`) |
| `RESTRICT` | Prevent deletion/update if referenced (default) |
| `NO ACTION` | Same as RESTRICT in SQLite |

```python
# CASCADE - delete books when author is deleted
author: ForeignKey[Author] = ForeignKey(Author, on_delete="CASCADE")

# SET NULL - set author to NULL when deleted
author: ForeignKey[Author] = ForeignKey(
    Author, on_delete="SET NULL", null=True
)

# RESTRICT - prevent deletion if books exist (default)
author: ForeignKey[Author] = ForeignKey(Author, on_delete="RESTRICT")
```

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
