# ORM Mode

The ORM module extends the legacy `sqliter.model` with lazy loading,
reverse relationships, and a descriptor-based `ForeignKey` class.

```python
from sqliter.orm import BaseDBModel, ForeignKey, ModelRegistry
```

**Sources:** `sqliter/orm/model.py`, `sqliter/orm/fields.py`,
`sqliter/orm/registry.py`, `sqliter/orm/query.py`

See also: [Guide -- ORM Foreign Keys](../guide/foreign-keys/orm.md)

> [!NOTE]
> The ORM module is an **alternative** to the legacy `sqliter.model`
> import. Both modes use the same `SqliterDB` class for database
> operations. The key difference is how foreign key relationships are
> defined and accessed.

---

## Legacy vs ORM Mode

| Feature         | Legacy (`sqliter.model`)                | ORM (`sqliter.orm`)                   |
| --------------- | --------------------------------------- | ------------------------------------- |
| FK definition   | `ForeignKey()` factory function         | `ForeignKey` descriptor class         |
| FK access       | Manual ID lookup                        | Lazy loading via `book.author.name`   |
| Reverse queries | Not available                           | `author.books.fetch_all()`            |
| Eager loading   | Not available                           | `select_related("author")`            |
| Import          | `from sqliter.model import BaseDBModel` | `from sqliter.orm import BaseDBModel` |

---

## `orm.BaseDBModel`

Extends the legacy [`BaseDBModel`](base-model.md) with ORM features.

```python
from sqliter.orm import BaseDBModel
```

**Additional Class Variables:**

| Attribute        | Type                              | Description                                   |
| ---------------- | --------------------------------- | --------------------------------------------- |
| `fk_descriptors` | `ClassVar[dict[str, ForeignKey]]` | FK descriptors for this class (not inherited) |

**Additional Instance Fields:**

| Field        | Type                | Default | Description                                                        |
| ------------ | ------------------- | ------- | ------------------------------------------------------------------ |
| `db_context` | `Any` &#124; `None` | `None`  | Database connection for lazy loading (excluded from serialization) |

### Overridden Behavior

**`__init__(**kwargs)`**

Converts FK field values to `_id` fields before Pydantic validation.
Accepts model instances, integer IDs, or `None`.

```python
# All equivalent:
book = Book(author=author_instance)  # Model instance
book = Book(author=42)               # Integer ID
book = Book(author_id=42)            # Direct _id field
```

**`model_dump(**kwargs)`**

Excludes FK descriptor fields (like `author`) from serialization.
Only the `_id` fields (like `author_id`) are included.

**`__getattribute__(name)`**

Intercepts FK field access to provide lazy loading. Returns a
[`LazyLoader`](#lazyloadert) that queries the database on first
attribute access. Returns `None` for null FK values.

**`__setattr__(name, value)`**

Intercepts FK field assignment. Accepts model instances, integer IDs,
or `None`. Clears the FK cache when an `_id` field changes.

---

## `ForeignKey[T]`

Generic descriptor class for FK fields providing lazy loading and type
safety.

```python
from sqliter.orm import ForeignKey
```

```python
class ForeignKey(Generic[T]):
    def __init__(
        self,
        to_model: type[T],
        *,
        on_delete: FKAction = "RESTRICT",
        on_update: FKAction = "RESTRICT",
        null: bool = False,
        unique: bool = False,
        related_name: str | None = None,
        db_column: str | None = None,
    ) -> None:
```

**Parameters:**

| Parameter      | Type                | Default      | Description                                              |
| -------------- | ------------------- | ------------ | -------------------------------------------------------- |
| `to_model`     | `type[T]`           | *required*   | The related model class                                  |
| `on_delete`    | `FKAction`          | `"RESTRICT"` | Action when related record is deleted                    |
| `on_update`    | `FKAction`          | `"RESTRICT"` | Action when related record's PK is updated               |
| `null`         | `bool`              | `False`      | Whether FK can be null                                   |
| `unique`       | `bool`              | `False`      | Whether FK must be unique (one-to-one)                   |
| `related_name` | `str` &#124; `None` | `None`       | Name for reverse relationship (auto-generated if `None`) |
| `db_column`    | `str` &#124; `None` | `None`       | Custom column name for `_id` field                       |

**Example:**

```python
from sqliter.orm import BaseDBModel, ForeignKey


class Author(BaseDBModel):
    name: str


class Book(BaseDBModel):
    title: str
    author: ForeignKey[Author] = ForeignKey(
        Author, on_delete="CASCADE"
    )
```

### Auto-nullable Detection

If the type annotation is `ForeignKey[Optional[Model]]` or
`ForeignKey[Model | None]`, the FK is automatically set to
`null=True`:

```python
class Book(BaseDBModel):
    # null=True is inferred from Optional
    editor: ForeignKey[Optional[Author]] = ForeignKey(Author)
```

### Auto-generated `related_name`

If `related_name` is not provided, it is auto-generated by
pluralizing the owner class name (e.g., `Book` becomes `"books"`).
Uses the `inflect` library if installed, otherwise adds `"s"`.

### Descriptor Protocol

**`__get__(instance, owner)`**

- On a **class**: returns the `ForeignKey` descriptor itself.
- On an **instance**: returns a [`LazyLoader[T]`](#lazyloadert)
  that loads the related object on first attribute access.

**`__set__(instance, value)`**

Sets the FK value. Accepts:

- A model instance (extracts `pk`)
- An `int` (used as the FK ID directly)
- `None` (for nullable FKs)

Raises `TypeError` for other types.

### `ForeignKeyDescriptor`

> [!CAUTION]
> `ForeignKeyDescriptor` is a backwards-compatibility alias for
> `ForeignKey`. Use `ForeignKey` directly.

---

## `LazyLoader[T]`

Transparent proxy that lazy-loads a related object when its attributes
are accessed. Returned by FK field access on ORM model instances.

```python
class LazyLoader(Generic[T]):
    def __init__(
        self,
        instance: object,
        to_model: type[T],
        fk_id: int | None,
        db_context: SqliterDB | None,
    ) -> None:
```

### Properties

| Property     | Type     | Description                                  |
| ------------ | -------- | -------------------------------------------- |
| `db_context` | `object` | The database context (for validity checking) |

### Methods

**`__getattr__(name)`**

Loads the related object from the database on first access, then
delegates attribute access to it. Raises `AttributeError` if the
FK is null or the object is not found.

**`__eq__(other)`**

Compares based on the loaded object. Loads the object if not already
cached. Returns `True` if `other` equals the loaded object, or if both
are `None`.

**`__repr__()`**

Returns `<LazyLoader unloaded for ModelName id=N>` before loading, or
`<LazyLoader loaded: <repr>>` after loading.

> [!NOTE]
> `LazyLoader` is unhashable (`__hash__ = None`) because its equality
> depends on mutable cached state.

---

## `ModelRegistry`

Class-level registry for ORM models, FK relationships, and pending
reverse relationships. Uses automatic setup via the descriptor
`__set_name__` hook -- no manual registration required.

```python
from sqliter.orm import ModelRegistry
```

### `register_model()`

Register a model class in the global registry.

```python
@classmethod
def register_model(
    cls,
    model_class: type[Any],
) -> None:
```

**Parameters:**

| Parameter     | Type        | Description                 |
| ------------- | ----------- | --------------------------- |
| `model_class` | `type[Any]` | The model class to register |

Also processes any pending reverse relationships for this model.

### `register_foreign_key()`

Register a FK relationship.

```python
@classmethod
def register_foreign_key(
    cls,
    from_model: type[Any],
    to_model: type[Any],
    fk_field: str,
    on_delete: str,
    related_name: str | None = None,
) -> None:
```

**Parameters:**

| Parameter      | Type                | Description                 |
| -------------- | ------------------- | --------------------------- |
| `from_model`   | `type[Any]`         | The model with the FK field |
| `to_model`     | `type[Any]`         | The referenced model        |
| `fk_field`     | `str`               | Name of the FK field        |
| `on_delete`    | `str`               | Delete action               |
| `related_name` | `str` &#124; `None` | Reverse relationship name   |

### `get_model()`

Get a model class by table name.

```python
@classmethod
def get_model(
    cls,
    table_name: str,
) -> type[Any] | None:
```

**Parameters:**

| Parameter    | Type  | Description           |
| ------------ | ----- | --------------------- |
| `table_name` | `str` | Table name to look up |

**Returns:**

`type[Any] | None` -- The model class, or `None` if not found.

### `get_foreign_keys()`

Get FK relationships for a model by table name.

```python
@classmethod
def get_foreign_keys(
    cls,
    table_name: str,
) -> list[dict[str, Any]]:
```

**Parameters:**

| Parameter    | Type  | Description           |
| ------------ | ----- | --------------------- |
| `table_name` | `str` | Table name to look up |

**Returns:**

`list[dict[str, Any]]` -- List of FK relationship dictionaries with
keys: `to_model`, `fk_field`, `on_delete`, `related_name`.

### `add_reverse_relationship()`

Add a reverse relationship descriptor to the target model. Called
automatically by `ForeignKey.__set_name__()` during class creation. If
the target model does not exist yet, stores the relationship as pending.

```python
@classmethod
def add_reverse_relationship(
    cls,
    from_model: type[Any],
    to_model: type[Any],
    fk_field: str,
    related_name: str,
) -> None:
```

**Parameters:**

| Parameter      | Type        | Description                                 |
| -------------- | ----------- | ------------------------------------------- |
| `from_model`   | `type[Any]` | Model with the FK (e.g., `Book`)            |
| `to_model`     | `type[Any]` | Referenced model (e.g., `Author`)           |
| `fk_field`     | `str`       | FK field name (e.g., `"author"`)            |
| `related_name` | `str`       | Reverse relationship name (e.g., `"books"`) |

---

## `ReverseQuery`

Query builder for reverse relationships. Returned when accessing a
reverse relationship on a model instance (e.g., `author.books`).
Delegates to [`QueryBuilder`](query-builder.md) for SQL execution.

```python
class ReverseQuery:
    def __init__(
        self,
        instance: HasPKAndContext,
        to_model: type[BaseDBModel],
        fk_field: str,
        db_context: SqliterDB | None,
    ) -> None:
```

### `filter()`

Add filter conditions to the reverse query.

```python
def filter(
    self,
    **kwargs: Any,
) -> ReverseQuery:
```

**Returns:** `ReverseQuery` for method chaining.

### `limit()`

Set a limit on query results.

```python
def limit(self, count: int) -> ReverseQuery:
```

**Returns:** `ReverseQuery` for method chaining.

### `offset()`

Set an offset on query results.

```python
def offset(self, count: int) -> ReverseQuery:
```

**Returns:** `ReverseQuery` for method chaining.

### `fetch_all()`

Execute the query and return all matching related objects.

```python
def fetch_all(self) -> list[BaseDBModel]:
```

**Returns:** `list[BaseDBModel]` -- Related model instances.

### `fetch_one()`

Execute the query and return a single result.

```python
def fetch_one(self) -> BaseDBModel | None:
```

**Returns:** `BaseDBModel | None` -- A single related instance or
`None`.

### `count()`

Count the number of related objects.

```python
def count(self) -> int:
```

**Returns:** `int` -- Number of matching related objects.

### `exists()`

Check if any related objects exist.

```python
def exists(self) -> bool:
```

**Returns:** `bool` -- `True` if at least one related object exists.

**Example:**

```python
# Fetch all books by an author
books = author.books.fetch_all()

# Filter and count
count = author.books.filter(title__contains="Python").count()

# Check existence
has_books = author.books.exists()
```

---

## `ReverseRelationship`

Descriptor that returns a [`ReverseQuery`](#reversequery) when accessed
on a model instance. Added automatically to models by
`ForeignKey.__set_name__()` during class creation.

```python
class ReverseRelationship:
    def __init__(
        self,
        from_model: type[BaseDBModel],
        fk_field: str,
        related_name: str,
    ) -> None:
```

**Descriptor Protocol:**

- On a **class**: returns the `ReverseRelationship` descriptor itself.
- On an **instance**: returns a `ReverseQuery` bound to that instance.
- **`__set__`**: Raises `AttributeError`. Reverse relationships are
  read-only.

---

## Protocols

### `HasPK`

Runtime-checkable protocol for objects that have a `pk` attribute.
Used for duck-typed FK assignment.

```python
@runtime_checkable
class HasPK(Protocol):
    pk: int | None
```

### `HasPKAndContext`

Runtime-checkable protocol for model instances with `pk` and
`db_context`. Used by `ReverseQuery`.

```python
@runtime_checkable
class HasPKAndContext(Protocol):
    pk: int | None
    db_context: SqliterDB | None
```
