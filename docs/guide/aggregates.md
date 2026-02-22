# Aggregates and Grouping

SQLiter supports SQL-style projection queries with grouping and aggregates.
These queries return dictionaries rather than model instances.

```python
from sqliter.query import func

rows = (
    db.select(Sale)
    .group_by("category")
    .annotate(total=func.sum("amount"), entries=func.count())
    .order("total", reverse=True)
    .fetch_dicts()
)
```

## Key Methods

- `group_by(*fields)`: Group rows by one or more model fields.
- `annotate(**aggregates)`: Add aggregate projections using `func`.
- `having(**conditions)`: Filter grouped/aggregate results.
- `with_count(path, alias="count", distinct=False)`: Count related rows.
- `fetch_dicts()`: Execute projection queries and return
  `list[dict[str, Any]]`.

## Aggregate Helpers

Use `func` from `sqliter.query`:

- `func.count(field=None, distinct=False)`
- `func.sum(field, distinct=False)`
- `func.avg(field, distinct=False)`
- `func.min(field, distinct=False)`
- `func.max(field, distinct=False)`

Example:

```python
rows = (
    db.select(Sale)
    .group_by("category")
    .annotate(
        total=func.sum("amount"),
        average=func.avg("amount"),
        lowest=func.min("amount"),
        highest=func.max("amount"),
        entries=func.count(),
    )
    .fetch_dicts()
)
```

## Aggregate-Only Queries

You can run aggregate queries without `group_by()`:

```python
summary = (
    db.select(Sale)
    .annotate(total_rows=func.count(), total_amount=func.sum("amount"))
    .fetch_dicts()
)
# -> [{"total_rows": 5, "total_amount": 90.0}]
```

## Grouping Without Aggregates

`group_by()` also works on its own for unique grouped rows:

```python
categories = db.select(Sale).group_by("category").fetch_dicts()
# -> [{"category": "books"}, {"category": "games"}, {"category": "music"}]
```

## HAVING Filters

`having()` accepts the same operator suffixes as `filter()` (such as
`__gt`, `__in`, `__contains`, etc.), but fields must be either:

- A grouped field from `group_by()`
- An aggregate alias from `annotate()` / `with_count()`

```python
rows = (
    db.select(Sale)
    .group_by("category")
    .annotate(total=func.sum("amount"))
    .having(total__gt=20)
    .fetch_dicts()
)
```

## Counting Related Rows with `with_count()`

`with_count()` is useful in ORM mode for reporting relationship counts.
It uses `LEFT JOIN`, so rows with zero related records are included.

```python
# Reverse FK count (includes authors with zero books)
rows = (
    db.select(Author)
    .with_count("books", alias="book_count")
    .order("name")
    .fetch_dicts()
)
```

```python
# Many-to-many count (forward or reverse)
rows = (
    db.select(Article)
    .with_count("tags", alias="tag_count")
    .fetch_dicts()
)
```

```python
# Multi-segment path: forward FK + reverse FK terminal
rows = (
    db.select(Book)
    .with_count("author__books", alias="author_book_count")
    .fetch_dicts()
)
```

## Important Notes

- Projection queries must use `fetch_dicts()`.
- `fetch_all()`, `fetch_one()`, `fetch_first()`, `fetch_last()`, and
  `count()` are not available in projection mode.
- Aggregate aliases must be non-empty, unique, and must not conflict
  with model field names.
- `with_count()` supports nested relationship paths (for example,
  `"author__books"` or `"articles__tags"`), but the terminal segment
  must be a to-many relationship (reverse FK or many-to-many).
- Use `distinct=True` when you need unique terminal-row counts across
  fan-out joins.
