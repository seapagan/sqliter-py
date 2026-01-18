# Foreign Keys

Foreign keys define relationships between models, enabling referential integrity
in your database. When you define a foreign key, SQLiter ensures that the
referenced record exists and automatically handles actions when the referenced
record is deleted or updated.

## Two Approaches

SQLiter offers two ways to work with foreign keys:

| Feature | Explicit FK | ORM FK |
|---------|-------------|--------|
| Import | `sqliter.model` | `sqliter.orm` |
| Syntax | `author_id: int = ForeignKey(Author)` | `author: ForeignKey[Author] = ForeignKey(Author)` |
| Access related object | Manual: `db.get(Author, book.author_id)` | Automatic: `book.author.name` |
| Reverse relationships | Manual queries | `author.books.fetch_all()` |
| Lazy loading | No | Yes |
| Caching | N/A | Yes (per instance) |
| Overhead | Minimal | Slightly more |

## Which Should I Use?

### Use Explicit Foreign Keys when

- You want minimal abstraction over the database
- You're managing IDs manually anyway
- You don't need lazy loading or reverse relationships
- You want the simplest possible setup
- Performance is critical and you want to avoid any overhead

**Example:**

```python
from sqliter.model import BaseDBModel, ForeignKey

class Book(BaseDBModel):
    title: str
    author_id: int = ForeignKey(Author, on_delete="CASCADE")

# Manual access
author = db.get(Author, book.author_id)
```

[Read the Explicit Foreign Keys guide](foreign-keys/explicit.md)

### Use ORM Foreign Keys when

- You want `book.author.name` style access
- You need reverse relationships (`author.books`)
- You prefer Django/SQLAlchemy-style patterns
- You want automatic caching of related objects
- Convenience is more important than minimal overhead

**Example:**

```python
from sqliter.orm import BaseDBModel, ForeignKey

class Book(BaseDBModel):
    title: str
    author: ForeignKey[Author] = ForeignKey(Author, on_delete="CASCADE")

# Automatic lazy loading
print(book.author.name)

# Reverse relationships
for book in author.books.fetch_all():
    print(book.title)
```

[Read the ORM Foreign Keys guide](foreign-keys/orm.md)

## Common Features

Both approaches share these features:

- **Database constraints**: Proper foreign key constraints in SQLite
- **Referential integrity**: Ensures referenced records exist
- **Foreign key actions**: CASCADE, SET NULL, RESTRICT, NO ACTION
- **Nullable foreign keys**: Optional relationships with `null=True`
- **One-to-one relationships**: Use `unique=True`
- **Automatic indexing**: Indexes created on FK columns
- **Same database**: Both work with the same SQLite database

## Mixing Approaches

You can use both approaches in the same project. Models from `sqliter.model`
and `sqliter.orm` can coexist and reference each other. However, ORM features
(lazy loading, reverse relationships) only work with models that inherit from
`sqliter.orm.BaseDBModel`.
