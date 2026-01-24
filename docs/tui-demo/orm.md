# ORM Features Demos

These demos show advanced ORM features including foreign keys and relationships.

## Foreign Key Basics

Link records from different tables using foreign keys.

```python
# --8<-- [start:foreign-key]
from sqliter.model import BaseDBModel, ForeignKey

class Author(BaseDBModel):
    """An author of books."""
    name: str

class Book(BaseDBModel):
    """A book linked to an author."""
    title: str
    author: ForeignKey[Author]
```

### What Happens

- `author` field stores the primary key of the Author
- Database creates a foreign key constraint
- Referential integrity is enforced

## Inserting with Foreign Keys

Create records linked to other records.

```python
# --8<-- [start:insert-foreign-key]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel, ForeignKey

class Author(BaseDBModel):
    name: str

class Book(BaseDBModel):
    title: str
    author: ForeignKey[Author]

db = SqliterDB(memory=True)
db.create_table(Author)
db.create_table(Book)

# Insert an author
author = db.insert(Author(name="Jane Austen"))

# Insert books linked to the author
book1 = db.insert(Book(title="Pride and Prejudice", author=author.pk))
book2 = db.insert(Book(title="Emma", author=author.pk))
```

### Storage

The `author` field stores the primary key (integer), not the full Author object.

## Lazy Loading

Access related objects on-demand.

```python
# --8<-- [start:lazy-loading]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel, ForeignKey

class Author(BaseDBModel):
    name: str

class Book(BaseDBModel):
    title: str
    author: ForeignKey[Author]

db = SqliterDB(memory=True)
db.create_table(Author)
db.create_table(Book)

# Setup data
author = db.insert(Author(name="J.K. Rowling"))
db.insert(Book(title="Harry Potter", author=author.pk))

# Access author later (lazy-loaded)
books = db.select(Book).fetch_all()
for book in books:
    # author is loaded automatically when accessed
    print(f"{book.title} by {book.author.name}")
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

## Reverse Relationships

Access all books by an author.

```python
# --8<-- [start:reverse-relationship]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel, ForeignKey, ReverseRelationship

class Author(BaseDBModel):
    name: str
    books: ReverseRelationship

class Book(BaseDBModel):
    title: str
    author: ForeignKey[Author]

db = SqliterDB(memory=True)
db.create_table(Author)
db.create_table(Book)

# Create author and books
author = db.insert(Author(name="Isaac Asimov"))
db.insert(Book(title="Foundation", author=author.pk))
db.insert(Book(title="I, Robot", author=author.pk))

# Access author's books
fetched_author = db.get_by_pk(Author, author.pk)
for book in fetched_author.books:
    print(f"  - {book.title}")
```

### Setting Up Reverse Relationships

Use the `related_name` parameter when defining the ForeignKey:

```python
class Book(BaseDBModel):
    author: ForeignKey[Author, related_name="books"]
```

Or define it as a class attribute:

```python
class Author(BaseDBModel):
    books: ReverseRelationship
```

## Deleting with Foreign Keys

Handle deleting records that are referenced by other records.

```python
# --8<-- [start:delete-foreign-key]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel, ForeignKey

class Author(BaseDBModel):
    name: str

class Book(BaseDBModel):
    title: str
    author: ForeignKey[Author]

db = SqliterDB(memory=True)
db.create_table(Author)
db.create_table(Book)

author = db.insert(Author(name="Author"))
db.insert(Book(title="Book", author=author.pk))

# Delete the author
db.delete(author)

# Book still exists but references a deleted author
orphaned_books = db.select(Book).fetch_all()
```

!!! warning
    By default, SQLite doesn't enforce foreign key constraints for backwards compatibility. Enable with `PRAGMA foreign_keys = ON` if needed.

## ORM Best Practices

### DO

- Use foreign keys to link related data
- Access related objects when needed (lazy loading)
- Consider query count when iterating over related objects

### DON'T

- Forget that ForeignKey stores the pk, not the object
- Create circular foreign key relationships
- Delete parent records without handling children

## Related Documentation

- [Models](models.md) - Define your data models
- [CRUD Operations](crud.md) - Create and manipulate records
- [Query Results](results.md) - Fetch related records
