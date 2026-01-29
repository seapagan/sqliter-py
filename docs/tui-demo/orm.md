# ORM Features Demos

These demos show advanced ORM features including foreign keys and relationships.

## Foreign Key Basics

Link records from different tables using foreign keys.

```python
# --8<-- [start:foreign-key]
from sqliter import SqliterDB
from sqliter.orm import BaseDBModel, ForeignKey

class Author(BaseDBModel):
    name: str

class Book(BaseDBModel):
    title: str
    author: ForeignKey[Author] = ForeignKey(Author)

db = SqliterDB(memory=True)
db.create_table(Author)
db.create_table(Book)

author = db.insert(Author(name="J.K. Rowling"))
book1 = db.insert(Book(title="Harry Potter 1", author=author))
book2 = db.insert(Book(title="Harry Potter 2", author=author))

print(f"Author: {author.name}")
print(f"Author ID: {author.pk}")

db.close()
# --8<-- [end:foreign-key]
```

### What Happens

- `author` field stores the primary key of the Author
- Database creates a foreign key constraint
- Referential integrity is enforced

## Nullable Foreign Keys

Declare nullable FKs using `Optional[T]` or `T | None` in the type annotation.
SQLiter auto-detects nullability from the annotation.

```python
# --8<-- [start:nullable-foreign-key]
from typing import Optional

from sqliter import SqliterDB
from sqliter.orm import BaseDBModel, ForeignKey

class Author(BaseDBModel):
    name: str

class Book(BaseDBModel):
    title: str
    # Optional[Author] auto-sets null=True — no need to pass it explicitly
    author: ForeignKey[Optional[Author]] = ForeignKey(
        Author, on_delete="SET NULL"
    )

db = SqliterDB(memory=True)
db.create_table(Author)
db.create_table(Book)

author = db.insert(Author(name="Jane Austen"))
book_with = db.insert(Book(title="Pride and Prejudice", author=author))
book_without = db.insert(Book(title="Anonymous Work", author=None))

book1 = db.get(Book, book_with.pk)
book2 = db.get(Book, book_without.pk)

print(f"'{book1.title}' author: {book1.author.name}")
print(f"'{book2.title}' author: {book2.author}")

db.close()
# --8<-- [end:nullable-foreign-key]
```

### What Happens

- `ForeignKey[Optional[Author]]` tells SQLiter the FK column is nullable
- Books can be inserted with `author=None`
- Accessing a null FK returns `None` instead of a model instance
- The explicit `null=True` parameter still works but the annotation approach
  is preferred
- Prefer defining ORM models at **module scope** so type annotations resolve
  reliably. If you use type aliases for nullable FKs in locally defined models,
  set `null=True` explicitly.

## Inserting with Foreign Keys

Create records linked to other records.

```python
# --8<-- [start:insert-foreign-key]
from sqliter import SqliterDB
from sqliter.orm import BaseDBModel, ForeignKey

class Author(BaseDBModel):
    name: str

class Book(BaseDBModel):
    title: str
    author: ForeignKey[Author] = ForeignKey(Author)

db = SqliterDB(memory=True)
db.create_table(Author)
db.create_table(Book)

author = db.insert(Author(name="Jane Austen"))
book = db.insert(Book(title="Pride and Prejudice", author=author))

print("Created book:")
print(f"  title: {book.title}")
print(f"  author: {book.author.name}")
print("\nForeign key stores the primary key internally, but access returns the object")

db.close()
# --8<-- [end:insert-foreign-key]
```

### Storage vs Access

- **Storage**: The `author` field stores only the primary key (integer)
- **Access**: When you access `book.author`, lazy loading fetches the full Author object
- This dual behavior lets you store efficiently but access conveniently

## Lazy Loading

Access related objects on-demand.

```python
# --8<-- [start:lazy-loading]
from sqliter import SqliterDB
from sqliter.orm import BaseDBModel, ForeignKey

class Author(BaseDBModel):
    name: str

class Book(BaseDBModel):
    title: str
    author: ForeignKey[Author] = ForeignKey(Author)

db = SqliterDB(memory=True)
db.create_table(Author)
db.create_table(Book)

author = db.insert(Author(name="J.K. Rowling"))
book1 = db.insert(Book(title="Harry Potter 1", author=author))
book2 = db.insert(Book(title="Harry Potter 2", author=author))

print(f"Author: {author.name}")
print(f"Author ID: {author.pk}")

# Access related author through foreign key - triggers lazy load
print("\nAccessing book.author triggers lazy load:")
print(f"  '{book1.title}' was written by {book1.author.name}")

print(f"\n'{book2.title}' was written by {book2.author.name}")
print("Related objects loaded on-demand from database")

db.close()
# --8<-- [end:lazy-loading]
```

### How Lazy Loading Works

1. Book object is fetched with just `author.pk` stored
2. When you access `book.author.name`, SQLiter queries the Author table
3. Full Author object is loaded and cached

### Performance Consideration

- **Pro**: Only loads related data when needed
- **Con**: N+1 query problem if iterating many records

```python
# Potential N+1 problem
books = db.select(Book).fetch_all()
for book in books:  # N queries here (one per book)
    print(book.author.name)
```

## Eager Loading with select_related()

Solve the N+1 problem by fetching related objects in a single JOIN query.

```python
# --8<-- [start:select-related]
from sqliter import SqliterDB
from sqliter.orm import BaseDBModel, ForeignKey

class Author(BaseDBModel):
    name: str

class Book(BaseDBModel):
    title: str
    author: ForeignKey[Author] = ForeignKey(Author)

db = SqliterDB(memory=True)
db.create_table(Author)
db.create_table(Book)

# Insert test data
author1 = db.insert(Author(name="Jane Austen"))
author2 = db.insert(Author(name="Charles Dickens"))

db.insert(Book(title="Pride and Prejudice", author=author1))
db.insert(Book(title="Emma", author=author1))
db.insert(Book(title="Oliver Twist", author=author2))

# Eager load - single JOIN query
print("Fetching books with eager loading:")
books = db.select(Book).select_related("author").fetch_all()

for book in books:
    print(f"  '{book.title}' by {book.author.name}")

print("\nAll authors loaded in single query (no N+1 problem)")

db.close()
# --8<-- [end:select-related]
```

### What Happens

1. `select_related("author")` tells SQLiter to include Author data in the initial query
2. A JOIN fetches both Book and Author data in a single database call
3. All related objects are preloaded and cached, avoiding the N+1 problem

### When to Use Eager Loading

- **Use** when you know you'll access related objects
- **Use** when iterating over multiple records with relationships
- **Don't use** if you only need the parent records

### Performance Comparison

```python
# Without select_related - N+1 queries (1 for books + N for authors)
books = db.select(Book).fetch_all()  # 1 query
for book in books:
    print(book.author.name)  # N queries (one per book)

# With select_related - 1 query total
books = db.select(Book).select_related("author").fetch_all()  # 1 query with JOIN
for book in books:
    print(book.author.name)  # No additional queries
```

## Nested Relationship Loading

Load multiple levels of relationships using double underscore syntax.

```python
# --8<-- [start:nested-select-related]
from sqliter import SqliterDB
from sqliter.orm import BaseDBModel, ForeignKey

class Author(BaseDBModel):
    name: str

class Book(BaseDBModel):
    title: str
    author: ForeignKey[Author] = ForeignKey(Author)

class Comment(BaseDBModel):
    text: str
    book: ForeignKey[Book] = ForeignKey(Book)

db = SqliterDB(memory=True)
db.create_table(Author)
db.create_table(Book)
db.create_table(Comment)

# Insert nested test data
author = db.insert(Author(name="Jane Austen"))
book = db.insert(Book(title="Pride and Prejudice", author=author))
db.insert(Comment(text="Amazing book!", book=book))

# Load nested relationship - single query joins Comment -> Book -> Author
print("Loading nested relationships:")
comment = db.select(Comment).select_related("book__author").fetch_one()

if comment is not None:
    print(f"Comment: {comment.text}")
    print(f"Book: {comment.book.title}")
    # Access author through book's foreign key relationship
    # Both book and author were loaded in a single JOIN query
    print(f"Author: {comment.book.author.name}")

print("\nNested relationships loaded in single query")

db.close()
# --8<-- [end:nested-select-related]
```

### How Nested Loading Works

1. Use double underscores (`__`) to traverse relationship paths
2. `select_related("book__author")` loads: Comment → Book → Author
3. Creates a chain of JOINs in a single query
4. All related objects are accessible without additional database hits

### Relationship Paths

```python
# Single level
select_related("author")  # Loads immediate parent

# Two levels
select_related("book__author")  # Loads grandparent

# Multiple paths (comma-separated)
select_related("author", "publisher")  # Loads multiple relationships

# Deep nesting (3+ levels)
select_related("comment__book__author__country")
```

## Relationship Filter Traversal

Filter records by fields on related models using double underscore syntax.

```python
# --8<-- [start:filter-traversal]
from sqliter import SqliterDB
from sqliter.orm import BaseDBModel, ForeignKey

class Author(BaseDBModel):
    name: str

class Book(BaseDBModel):
    title: str
    author: ForeignKey[Author] = ForeignKey(Author)

db = SqliterDB(memory=True)
db.create_table(Author)
db.create_table(Book)

# Insert test data
author1 = db.insert(Author(name="Jane Austen"))
author2 = db.insert(Author(name="Charles Dickens"))

db.insert(Book(title="Pride and Prejudice", author=author1))
db.insert(Book(title="Emma", author=author1))
db.insert(Book(title="Oliver Twist", author=author2))
db.insert(Book(title="Great Expectations", author=author2))

# Filter by related field
print("Filtering by author name:")
books = db.select(Book).filter(author__name="Jane Austen").fetch_all()

for book in books:
    print(f"  {book.title}")

print(f"\nFound {len(books)} book(s) by Jane Austen")
print("(Automatic JOIN added behind the scenes)")

db.close()
# --8<-- [end:filter-traversal]
```

### How Filter Traversal Works

1. Use `__` to access fields on related models: `author__name`
2. SQLiter automatically creates JOINs to traverse relationships
3. Filter is applied in SQL, not in Python
4. Works with most filter operators (note: `__isnull`/`__notnull`
   are not applied via relationship traversal)

### Filter Operators on Relationships

```python
# Exact match
.filter(author__name="Jane Austen")

# Comparison operators
.filter(author__age__gte=30)

# String operators
.filter(author__name__startswith="Jane")
.filter(author__name__contains="en")

# Multiple conditions
.filter(author__name="Jane Austen", year__gt=1800)
```

## Combining select_related with Filters

Use eager loading and relationship filters together for optimal performance.

```python
# --8<-- [start:select-related-filter]
from sqliter import SqliterDB
from sqliter.orm import BaseDBModel, ForeignKey

class Author(BaseDBModel):
    name: str

class Book(BaseDBModel):
    title: str
    year: int
    author: ForeignKey[Author] = ForeignKey(Author)

db = SqliterDB(memory=True)
db.create_table(Author)
db.create_table(Book)

# Insert test data
author1 = db.insert(Author(name="Jane Austen"))
author2 = db.insert(Author(name="Charles Dickens"))

db.insert(Book(title="Pride and Prejudice", year=1813, author=author1))
db.insert(Book(title="Emma", year=1815, author=author1))
db.insert(Book(title="Oliver Twist", year=1838, author=author2))

# Combine filter + eager load
print("Filter and eager load in single query:")
books = (
    db.select(Book)
    .select_related("author")
    .filter(author__name__startswith="Jane")
    .fetch_all()
)

for book in books:
    print(f"  {book.title} ({book.year}) by {book.author.name}")

print(f"\n{len(books)} result(s) with authors preloaded")

db.close()
# --8<-- [end:select-related-filter]
```

### Why Combine Them?

- **Filter**: Reduces result set at the database level
- **select_related**: Preloads relationships for filtered results
- **Together**: Optimal performance - minimal data transfer, no N+1 queries

### Query Builder Chaining

```python
# Build complex queries step by step
query = (
    db.select(Book)
    .select_related("author")  # Eager load
    .filter(author__name="Jane Austen")  # Filter by related field
    .filter(year__gte=1800)  # Additional filter
    .order("year")  # Sort results
)

results = query.fetch_all()
```

### Best Practices

```python
# Both examples produce identical SQL - QueryBuilder composes
# the query regardless of method chaining order
books = (
    db.select(Book)
    .filter(author__name="Jane Austen")
    .select_related("author")
    .fetch_all()
)

# Equivalent to the above - same SQL, same performance
books = (
    db.select(Book)
    .select_related("author")
    .filter(author__name="Jane Austen")
    .fetch_all()
)
```

### Performance Tips

1. **Apply filters to limit rows returned** - reduces data transfer
2. **Select only needed relationships** - avoid unused data
3. **Combine with ordering** - sort at database level
4. **Use pagination** - limit results with `.limit()` and `.offset()`

```python
# Optimal query pattern
results = (
    db.select(Model)
    .filter(relationship__field="value")
    .select_related("relationship")
    .order("field")  # Sort in database
    .limit(10)
    .fetch_all()
)
```

## Reverse Relationships

Access all books by an author using queries.

```python
# --8<-- [start:reverse-relationship]
from sqliter import SqliterDB
from sqliter.orm import BaseDBModel, ForeignKey

class Author(BaseDBModel):
    name: str

class Book(BaseDBModel):
    title: str
    author: ForeignKey[Author] = ForeignKey(Author, related_name="books")

db = SqliterDB(memory=True)
db.create_table(Author)
db.create_table(Book)

author = db.insert(Author(name="Jane Austen"))
db.insert(Book(title="Pride and Prejudice", author=author))
db.insert(Book(title="Emma", author=author))
db.insert(Book(title="Sense and Sensibility", author=author))

print(f"Author: {author.name}")

# Access reverse relationship - get all books by this author
# Note: 'books' attribute added dynamically by ForeignKey descriptor
print("\nAccessing author.books (reverse relationship):")
reverse_attr = "books"  # Dynamic attribute added by FK descriptor
books_query = getattr(author, reverse_attr)
books = books_query.fetch_all()
for book in books:
    print(f"  - {book.title}")

print(f"\nTotal books: {len(books)}")
print("Reverse relationships auto-generated from FKs")

db.close()
# --8<-- [end:reverse-relationship]
```

### Setting Up Reverse Relationships

Use the `related_name` parameter when defining the ForeignKey:

```python
class Book(BaseDBModel):
    author: ForeignKey[Author] = ForeignKey(Author, related_name="books")
```

The reverse relationship is dynamically added and accessed as a query builder.

## Navigating with Foreign Keys

Navigate from child records to parent records using foreign keys.

```python
# --8<-- [start:delete-foreign-key]
from sqliter import SqliterDB
from sqliter.orm import BaseDBModel, ForeignKey

class Team(BaseDBModel):
    name: str

class Player(BaseDBModel):
    name: str
    team: ForeignKey[Team] = ForeignKey(Team)

db = SqliterDB(memory=True)
db.create_table(Team)
db.create_table(Player)

team = db.insert(Team(name="Lakers"))
player1 = db.insert(Player(name="LeBron", team=team))
player2 = db.insert(Player(name="Davis", team=team))

print(f"Team: {team.name}")

# Navigate from player to team via FK
print(f"\n{player1.name} plays for: {player1.team.name}")
print(f"{player2.name} plays for: {player2.team.name}")
print("Foreign keys enable relationship navigation")

db.close()
# --8<-- [end:delete-foreign-key]
```

### What This Shows

- Child objects (Player) can access parent objects (Team) via FK
- Lazy loading fetches the Team when you access `player.team`
- No need to manually query the parent table

### Note on Constraints

By default, SQLite doesn't enforce foreign key constraints for backwards compatibility. However, SQLiter automatically enables foreign key enforcement on every database connection, so you don't need to manually set `PRAGMA foreign_keys = ON`.

## ORM Best Practices

### DO

- Use foreign keys to link related data
- Use `select_related()` when accessing related objects in loops
- Filter by relationship fields using double underscore syntax
- Combine eager loading with filters for optimal performance
- Consider query count when iterating over related objects

### DON'T

- Forget that ForeignKey stores the pk, not the object
- Create circular foreign key relationships
- Delete parent records without handling children
- Use lazy loading in loops (causes N+1 queries)
- Eager load relationships you won't access

### Performance Checklist

- [ ] Will I access related objects? Use `select_related()`
- [ ] Am I filtering by related fields? Use `__` syntax
- [ ] Am I iterating over results? Preload with `select_related()`
- [ ] Can I filter before eager loading? Order operations for efficiency

## Related Documentation

- [Models](models.md) - Define your data models
- [CRUD Operations](crud.md) - Create and manipulate records
- [Query Results](results.md) - Fetch related records
- [Filters](filters.md) - Advanced filtering techniques
- [Foreign Keys Guide](../guide/foreign-keys/orm.md) - Complete ORM reference
