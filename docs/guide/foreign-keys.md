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

## Performance Comparison

Understanding the performance characteristics of each approach helps you make
informed decisions based on your use case.

### Overhead Breakdown

| Aspect | Explicit FK | ORM FK |
|--------|-------------|--------|
| Memory overhead | None | Minimal (LazyLoader proxy per FK field) |
| Query overhead | None | None (parameterized queries) |
| Cache overhead | None | Small (one cached object per instance) |
| Attribute access | Direct field access | Descriptor + proxy lookup |
| Relationship queries | Manual `db.select()` | Built-in methods (same queries) |

### Query Comparison

Both approaches execute the same underlying SQL queries:

```python
# Explicit FK - Manual query
author = db.get(Author, book.author_id)  # SELECT * FROM authors WHERE pk = ?

# ORM FK - Automatic lazy loading
author = book.author  # Same query: SELECT * FROM authors WHERE pk = ?
```

**Key insight**: The queries are identical. The difference is in convenience
and when queries execute.

### Single Object Access

For accessing a single related object, the overhead is negligible:

```python
# Explicit FK: ~2 operations (field access + manual query)
book = db.get(Book, 1)
author = db.get(Author, book.author_id)

# ORM FK: ~3 operations (descriptor + proxy + automatic query)
book = db.get(Book, 1)
author = book.author

# Performance difference: Microseconds (typically < 0.01ms)
```

**Recommendation**: Choose based on preference, not performance.

### Collections and Loops

For collections, ORM FK can cause N+1 query problems if not used carefully:

```python
# ❌ Explicit FK: Still need N+1 queries
books = db.select(Book).fetch_all()
for book in books:
    author = db.get(Author, book.author_id)  # N queries

# ❌ ORM FK: Same N+1 problem
books = db.select(Book).fetch_all()
for book in books:
    print(book.author.name)  # N queries (lazy loading each author)

# ✅ Both approaches: Use reverse relationships to avoid N+1
authors = db.select(Author).fetch_all()
for author in authors:
    books = author.books.fetch_all()  # One query per author
    for book in books:
        print(f"{book.title} by {author.name}")
```

**Recommendation**: Both approaches suffer from N+1 if used carelessly. Design
your queries thoughtfully regardless of which approach you choose.

### Caching Benefits (ORM FK Only)

ORM FK caches loaded objects, which helps in some scenarios:

```python
book = db.get(Book, 1)

# First access: Queries database
author1 = book.author

# Second access: Returns cached object (no query)
author2 = book.author

# Same instance
assert author1 is author2
```

**When caching helps:**

- Multiple accesses to the same FK field on one instance
- Complex business logic that repeatedly checks relationships

**When caching doesn't help:**

- One-time access patterns
- Different instances with the same FK value (each caches separately)

### Memory Considerations

**Explicit FK:**

- Uses only primitive types (integers)
- No extra memory per instance

**ORM FK:**

- Each FK field adds a `LazyLoader` proxy (~200 bytes)
- Each cached object adds the full object (~1KB typical model)
- For 1000 Book instances, expect ~1.2MB overhead (LazyLoader + cached authors)

**Recommendation**: Memory overhead is negligible for typical applications.
Only consider this for applications managing tens of thousands of objects in
memory simultaneously.

### Choosing Based on Performance

| Scenario | Recommendation | Reason |
|----------|---------------|---------|
| **CLI tools** | Either | Performance difference is negligible |
| **Web APIs (read-heavy)** | ORM FK | Convenience worth minimal overhead |
| **Web APIs (write-heavy)** | Either | Both approaches have same write performance |
| **Batch processing (large collections)** | Explicit FK | More control over when queries execute |
| **Interactive applications** | ORM FK | Lazy loading feels more responsive |
| **High-traffic services** | Either | Bottleneck is usually DB I/O, not FK overhead |
| **Memory-constrained** | Explicit FK | Avoid caching overhead |

### Performance Best Practices

**For both approaches:**

1. **Use indexes** - Foreign key columns are automatically indexed
2. **Avoid N+1** - Restructure queries to minimize relationship traversal
3. **Batch operations** - Use transactions for multiple inserts/updates
4. **Profile first** - Measure before optimizing

**For ORM FK specifically:**

1. **Use reverse relationships** - More efficient than iterating forward
2. **Cache locally** - Store frequently accessed data in variables
3. **Know when lazy loading happens** - Be aware of query timing

> [!TIP]
>
> In practice, the performance difference between Explicit and ORM FK is
> rarely the bottleneck. Database I/O, network latency, and query structure
> have much larger impacts. Choose based on code maintainability and
> development speed rather than premature optimization.

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
