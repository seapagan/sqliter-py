# QueryBuilder

Fluent API for constructing and executing database queries. Instances
are created by [`SqliterDB.select()`](sqliterdb.md#select) -- you do
not instantiate `QueryBuilder` directly.

```python
results = db.select(User).filter(age__gt=18).order("name").fetch_all()
```

**Source:** `sqliter/query/query.py`

See also: [Guide -- Filtering](../guide/filtering.md),
[Guide -- Ordering](../guide/ordering.md),
[Guide -- Field Control](../guide/fields.md),
[Guide -- Caching](../guide/caching.md)

---

## Type Parameters

```python
T = TypeVar("T", bound=BaseDBModel)

class QueryBuilder(Generic[T]):
    ...
```

`QueryBuilder` is generic over `T`, the model class. All fetch methods
return instances of `T`.

---

## Type Aliases

### `FilterValue`

The allowed types for filter values:

```python
FilterValue = Union[
    str, int, float, bool, None,
    list[Union[str, int, float, bool]],
]
```

---

## Constructor

```python
def __init__(
    self,
    db: SqliterDB,
    model_class: type[T],
    fields: list[str] | None = None,
) -> None:
```

> [!NOTE]
> You should not call this directly. Use
> [`db.select(Model)`](sqliterdb.md#select) instead.

**Parameters:**

| Parameter     | Type                      | Default    | Description                      |
| ------------- | ------------------------- | ---------- | -------------------------------- |
| `db`          | `SqliterDB`               | *required* | Database connection              |
| `model_class` | `type[T]`                 | *required* | The model class to query         |
| `fields`      | `list[str]` &#124; `None` | `None`     | Fields to select (all if `None`) |

---

## Filter Methods

### `filter()`

Apply filter conditions to the query. Supports operator suffixes on
field names and relationship traversal.

```python
def filter(
    self,
    **conditions: FilterValue,
) -> Self:
```

**Parameters:**

| Parameter      | Type          | Description                               |
| -------------- | ------------- | ----------------------------------------- |
| `**conditions` | `FilterValue` | Field-operator pairs as keyword arguments |

**Returns:** `Self` for method chaining.

**Raises:**

- [`InvalidFilterError`](exceptions.md#invalidfiltererror) -- If a
  field does not exist on the model.
- [`InvalidRelationshipError`](exceptions.md#invalidrelationshiperror)
  -- If a relationship traversal path is invalid.
- `TypeError` -- If a list is passed for a scalar operator, or a
  non-string for a string operator.

**Example:**

```python
# Simple equality (default __eq)
db.select(User).filter(name="Alice")

# Comparison operators
db.select(User).filter(age__gt=18, age__lt=65)

# Multiple chained calls (AND logic)
db.select(User).filter(active=True).filter(age__gte=21)

# Relationship traversal (ORM mode)
db.select(Book).filter(author__name="Alice")
```

### Filter Operators

| Operator        | SQL           | Value Type | Description                                        |
| --------------- | ------------- | ---------- | -------------------------------------------------- |
| *(none)*        | `=`           | scalar     | Equality (default)                                 |
| `__eq`          | `=`           | scalar     | Explicit equality                                  |
| `__ne`          | `!=`          | scalar     | Not equal                                          |
| `__gt`          | `>`           | scalar     | Greater than                                       |
| `__lt`          | `<`           | scalar     | Less than                                          |
| `__gte`         | `>=`          | scalar     | Greater than or equal                              |
| `__lte`         | `<=`          | scalar     | Less than or equal                                 |
| `__in`          | `IN`          | `list`     | Value in list                                      |
| `__not_in`      | `NOT IN`      | `list`     | Value not in list                                  |
| `__isnull`      | `IS NULL`     | `bool`     | Field is NULL (pass `True`)                        |
| `__notnull`     | `IS NOT NULL` | `bool`     | Field is not NULL (pass `True`)                    |
| `__like`        | `LIKE`        | `str`      | Raw SQL LIKE pattern (user provides `%` wildcards) |
| `__startswith`  | `GLOB`        | `str`      | Case-sensitive starts with                         |
| `__endswith`    | `GLOB`        | `str`      | Case-sensitive ends with                           |
| `__contains`    | `GLOB`        | `str`      | Case-sensitive contains                            |
| `__istartswith` | `LIKE`        | `str`      | Case-insensitive starts with                       |
| `__iendswith`   | `LIKE`        | `str`      | Case-insensitive ends with                         |
| `__icontains`   | `LIKE`        | `str`      | Case-insensitive contains                          |

---

## Field Selection

### `fields()`

Specify which fields to include in the query results.

```python
def fields(
    self,
    fields: list[str] | None = None,
) -> Self:
```

**Parameters:**

| Parameter | Type                      | Default | Description                               |
| --------- | ------------------------- | ------- | ----------------------------------------- |
| `fields`  | `list[str]` &#124; `None` | `None`  | Fields to select; `pk` is always included |

**Returns:** `Self` for method chaining.

**Example:**

```python
db.select(User).fields(["name", "email"]).fetch_all()
```

### `exclude()`

Specify which fields to exclude from the query results.

```python
def exclude(
    self,
    fields: list[str] | None = None,
) -> Self:
```

**Parameters:**

| Parameter | Type                      | Default | Description       |
| --------- | ------------------------- | ------- | ----------------- |
| `fields`  | `list[str]` &#124; `None` | `None`  | Fields to exclude |

**Returns:** `Self` for method chaining.

**Raises:**

- `ValueError` -- If `pk` is excluded, if invalid fields are
  specified, or if exclusion leaves no fields.

**Example:**

```python
db.select(User).exclude(["password_hash"]).fetch_all()
```

### `only()`

Select a single field (plus `pk`).

```python
def only(
    self,
    field: str,
) -> Self:
```

**Parameters:**

| Parameter | Type  | Default    | Description                |
| --------- | ----- | ---------- | -------------------------- |
| `field`   | `str` | *required* | The single field to select |

**Returns:** `Self` for method chaining.

**Raises:**

- `ValueError` -- If the field does not exist.

**Example:**

```python
db.select(User).only("email").fetch_all()
```

---

## Relationships

### `select_related()`

Specify FK relationships to eager load via SQL JOINs. Reduces the N+1
query problem by fetching related objects in a single query.

```python
def select_related(
    self,
    *paths: str,
) -> Self:
```

**Parameters:**

| Parameter | Type  | Description                                  |
| --------- | ----- | -------------------------------------------- |
| `*paths`  | `str` | One or more relationship paths to eager load |

**Returns:** `Self` for method chaining.

**Raises:**

- [`InvalidRelationshipError`](exceptions.md#invalidrelationshiperror)
  -- If a path contains invalid fields.

**Example:**

```python
# Single level
books = db.select(Book).select_related("author").fetch_all()
# book.author.name  -- no additional query needed

# Nested
comments = db.select(Comment).select_related(
    "post__author"
).fetch_all()

# Multiple paths
books = db.select(Book).select_related(
    "author", "publisher"
).fetch_all()
```

---

## Pagination

### `limit()`

Limit the number of results returned.

```python
def limit(
    self,
    limit_value: int,
) -> Self:
```

**Parameters:**

| Parameter     | Type  | Default    | Description               |
| ------------- | ----- | ---------- | ------------------------- |
| `limit_value` | `int` | *required* | Maximum number of records |

**Returns:** `Self` for method chaining.

### `offset()`

Skip a number of records before returning results.

```python
def offset(
    self,
    offset_value: int,
) -> Self:
```

**Parameters:**

| Parameter      | Type  | Default    | Description               |
| -------------- | ----- | ---------- | ------------------------- |
| `offset_value` | `int` | *required* | Number of records to skip |

**Returns:** `Self` for method chaining.

**Raises:**

- [`InvalidOffsetError`](exceptions.md#invalidoffseterror) -- If the
  offset value is negative.

> [!NOTE]
> If `offset()` is called without a prior `limit()`, the limit is
> automatically set to `-1` (unlimited) to satisfy SQLite's requirement
> that `OFFSET` must be paired with `LIMIT`.

**Example:**

```python
# Pagination: page 2, 10 items per page
db.select(User).limit(10).offset(10).fetch_all()
```

---

## Ordering

### `order()`

Order the query results by a field.

```python
def order(
    self,
    order_by_field: str | None = None,
    direction: str | None = None,
    *,
    reverse: bool = False,
) -> Self:
```

**Parameters:**

| Parameter        | Type                | Default | Description                           |
| ---------------- | ------------------- | ------- | ------------------------------------- |
| `order_by_field` | `str` &#124; `None` | `None`  | Field to order by; defaults to `pk`   |
| `direction`      | `str` &#124; `None` | `None`  | **Deprecated.** Use `reverse` instead |
| `reverse`        | `bool`              | `False` | If `True`, sort descending            |

**Returns:** `Self` for method chaining.

**Raises:**

- [`InvalidOrderError`](exceptions.md#invalidordererror) -- If the
  field does not exist, or if both `direction` and `reverse` are
  specified.

**Warns:**

- `DeprecationWarning` -- If `direction` is used.

> [!CAUTION]
> The `direction` parameter is deprecated. Use `reverse=True` for
> descending order instead.

**Example:**

```python
# Ascending (default)
db.select(User).order("name").fetch_all()

# Descending
db.select(User).order("created_at", reverse=True).fetch_all()
```

---

## Cache Control

### `bypass_cache()`

Force this query to skip the cache and hit the database directly.

```python
def bypass_cache(self) -> Self:
```

**Returns:** `Self` for method chaining.

**Example:**

```python
fresh = db.select(User).bypass_cache().fetch_all()
```

### `cache_ttl()`

Set a custom time-to-live for this query's cached result, overriding
the global `cache_ttl`.

```python
def cache_ttl(
    self,
    ttl: int,
) -> Self:
```

**Parameters:**

| Parameter | Type  | Default    | Description    |
| --------- | ----- | ---------- | -------------- |
| `ttl`     | `int` | *required* | TTL in seconds |

**Returns:** `Self` for method chaining.

**Raises:**

- `ValueError` -- If `ttl` is negative.

**Example:**

```python
# Cache this query for 60 seconds
db.select(User).cache_ttl(60).fetch_all()
```

---

## Execution Methods

### `fetch_all()`

Execute the query and return all matching records.

```python
def fetch_all(self) -> list[T]:
```

**Returns:** `list[T]` -- List of model instances.

**Example:**

```python
users = db.select(User).filter(active=True).fetch_all()
```

### `fetch_one()`

Execute the query and return a single record.

```python
def fetch_one(self) -> T | None:
```

**Returns:** `T | None` -- A model instance, or `None` if no match.

### `fetch_first()`

Fetch the first record (sets `LIMIT 1`).

```python
def fetch_first(self) -> T | None:
```

**Returns:** `T | None` -- The first model instance, or `None`.

### `fetch_last()`

Fetch the last record (orders by `rowid DESC`, sets `LIMIT 1`).

```python
def fetch_last(self) -> T | None:
```

**Returns:** `T | None` -- The last model instance, or `None`.

### `count()`

Count the number of matching records.

```python
def count(self) -> int:
```

**Returns:** `int` -- The count of matching records.

**Example:**

```python
total = db.select(User).filter(active=True).count()
```

### `exists()`

Check if any matching records exist.

```python
def exists(self) -> bool:
```

**Returns:** `bool` -- `True` if at least one record matches.

**Example:**

```python
if db.select(User).filter(email="alice@example.com").exists():
    print("User exists")
```

### `delete()`

Delete all records matching the current query conditions.

```python
def delete(self) -> int:
```

**Returns:** `int` -- The number of records deleted.

**Raises:**

- [`RecordDeletionError`](exceptions.md#recorddeletionerror) -- If
  there is an error deleting the records.

**Example:**

```python
deleted = db.select(User).filter(active=False).delete()
print(f"Deleted {deleted} inactive users")
```

---

## Supporting Types

### `JoinInfo`

Dataclass holding metadata for a JOIN clause. Used internally by
`select_related()` and relationship filter traversal.

```python
@dataclass
class JoinInfo:
    alias: str
    table_name: str
    model_class: type[BaseDBModel]
    fk_field: str
    parent_alias: str
    fk_column: str
    join_type: str
    path: str
    is_nullable: bool
```

**Fields:**

| Field          | Type                | Description                                       |
| -------------- | ------------------- | ------------------------------------------------- |
| `alias`        | `str`               | Table alias (e.g., `"t1"`, `"t2"`)                |
| `table_name`   | `str`               | Actual database table name                        |
| `model_class`  | `type[BaseDBModel]` | Model class for the joined table                  |
| `fk_field`     | `str`               | FK field name on the parent model                 |
| `parent_alias` | `str`               | Alias of the parent table                         |
| `fk_column`    | `str`               | FK column name (e.g., `"author_id"`)              |
| `join_type`    | `str`               | `"LEFT"` (nullable FK) or `"INNER"` (required FK) |
| `path`         | `str`               | Full relationship path (e.g., `"post__author"`)   |
| `is_nullable`  | `bool`              | Whether the FK is nullable                        |
