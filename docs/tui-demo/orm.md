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
book_author = book1.author  # LazyLoader fetches author from DB
print(f"  '{book1.title}' was written by {book_author.name}")

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
books = author.books.fetch_all()  # type: ignore[attr-defined]
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
