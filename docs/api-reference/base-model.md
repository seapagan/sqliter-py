# BaseDBModel

The base class for all SQLiter database models. Extends Pydantic's
`BaseModel` with database-specific functionality including automatic
primary keys, timestamps, table name inference, and field
serialization.

```python
from sqliter.model import BaseDBModel
```

**Source:** `sqliter/model/model.py`, `sqliter/model/unique.py`

See also: [Guide -- Models](../guide/models.md),
[Guide -- Fields](../guide/fields.md)

> [!NOTE]
> This page documents the **legacy mode** `BaseDBModel` from
> `sqliter.model`. For the ORM-mode version with lazy loading and
> reverse relationships, see [ORM Mode](orm.md).

---

## Built-in Fields

Every model automatically includes these fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `pk` | `int` | `0` | Auto-incrementing primary key (set on insert) |
| `created_at` | `int` | `0` | Unix timestamp when the record was created |
| `updated_at` | `int` | `0` | Unix timestamp when the record was last updated |

`pk` is managed by SQLite's `AUTOINCREMENT`. The `created_at` and
`updated_at` timestamps are set automatically by
[`SqliterDB.insert()`](sqliterdb.md#insert) and
[`SqliterDB.update()`](sqliterdb.md#update).

---

## Model Configuration

`BaseDBModel` uses the following Pydantic `ConfigDict`:

```python
model_config = ConfigDict(
    extra="ignore",
    populate_by_name=True,
    validate_assignment=True,
    from_attributes=True,
)
```

| Option | Value | Effect |
|--------|-------|--------|
| `extra` | `"ignore"` | Extra fields in input data are silently ignored |
| `populate_by_name` | `True` | Fields can be populated by name or alias |
| `validate_assignment` | `True` | Field values are validated on assignment |
| `from_attributes` | `True` | Models can be created from objects with attributes |

---

## Inner Class `Meta`

Configure database-specific attributes via the `Meta` inner class.

```python
class MyModel(BaseDBModel):
    name: str

    class Meta:
        table_name = "custom_table"
        indexes = ["name"]
        unique_indexes = [("name", "email")]
```

**Attributes:**

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `table_name` | `str` &#124; `None` | `None` | Custom table name; auto-generated from class name if not set |
| `indexes` | `list[str` &#124; `tuple[str]]` | `[]` | Fields for regular indexes |
| `unique_indexes` | `list[str` &#124; `tuple[str]]` | `[]` | Fields for unique indexes |

---

## Class Methods

### `get_table_name()`

Get the database table name for the model.

```python
@classmethod
def get_table_name(cls) -> str:
```

**Returns:**

`str` -- The table name. If `Meta.table_name` is set, returns that
value. Otherwise, the class name is converted to `snake_case`, the
suffix `Model` is removed (if present), and the result is pluralized.

If the [`inflect`](https://pypi.org/project/inflect/) library is
installed, grammatically correct pluralization is used (e.g.,
`"person"` becomes `"people"`). Otherwise, a simple `"s"` suffix is
added.

**Raises:**

- `ValueError` -- If the table name contains invalid characters.

**Example:**

```python
class UserProfile(BaseDBModel):
    name: str

UserProfile.get_table_name()  # "user_profiles"
```

---

### `get_primary_key()`

Returns the name of the primary key field (always `"pk"`).

```python
@classmethod
def get_primary_key(cls) -> str:
```

**Returns:**

`str` -- Always `"pk"`.

---

### `should_create_pk()`

Returns whether the primary key should be created (always `True`).

```python
@classmethod
def should_create_pk(cls) -> bool:
```

**Returns:**

`bool` -- Always `True`.

---

### `serialize_field()`

Serialize a field value for SQLite storage.

```python
@classmethod
def serialize_field(
    cls,
    value: SerializableField,
) -> SerializableField:
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `value` | `SerializableField` | *required* | The field value to serialize |

**Returns:**

`SerializableField` -- The serialized value:

- `datetime` / `date` objects are converted to Unix timestamps (via
  [`to_unix_timestamp()`](helpers.md#to_unix_timestamp)).
- `list`, `dict`, `set`, `tuple` values are serialized with `pickle`.
- All other values are returned as-is.

---

### `deserialize_field()`

Deserialize a field value from SQLite storage back to a Python object.

```python
@classmethod
def deserialize_field(
    cls,
    field_name: str,
    value: SerializableField,
    *,
    return_local_time: bool,
) -> object:
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `field_name` | `str` | *required* | Name of the field being deserialized |
| `value` | `SerializableField` | *required* | The value from the database |
| `return_local_time` | `bool` | *required* | Whether to localize datetime values |

**Returns:**

`object` -- The deserialized value:

- Integer values in `datetime`/`date` fields are converted back using
  [`from_unix_timestamp()`](helpers.md#from_unix_timestamp).
- `bytes` values in `list`/`dict`/`set`/`tuple` fields are
  deserialized with `pickle`.
- `None` values return `None`.
- All other values are returned as-is.

---

### `model_validate_partial()`

Create a model instance from partial data (not all fields required).
Used internally when fetching partial field selections.

```python
@classmethod
def model_validate_partial(
    cls,
    obj: dict[str, Any],
) -> Self:
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `obj` | `dict[str, Any]` | *required* | Dictionary of field names and values |

**Returns:**

`Self` -- A model instance constructed with the provided data.

---

## Protocol

### `SerializableField`

Protocol for fields that can be serialized or deserialized. Used as a
type hint for `serialize_field()` and `deserialize_field()`.

```python
class SerializableField(Protocol):
    """Protocol for fields that can be serialized or deserialized."""
```

---

## `unique()`

Create a Pydantic `Field` with a unique constraint marker in
`json_schema_extra`.

```python
from sqliter.model import unique
```

```python
def unique(
    default: Any = ...,
    **kwargs: Any,
) -> Any:
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `default` | `Any` | `...` | Default value for the field |
| `**kwargs` | `Any` | | Additional arguments passed to Pydantic `Field` |

**Returns:**

A Pydantic `Field` with `json_schema_extra={"unique": True}`.

**Example:**

```python
from typing import Annotated

from sqliter.model import BaseDBModel, unique


class User(BaseDBModel):
    email: Annotated[str, unique()]
    username: Annotated[str, unique(default="anonymous")]
```

> [!TIP]
> Using `Annotated` is optional but recommended. Without it, type
> checkers like MyPy will report an incompatible assignment because
> `unique()` returns a Pydantic `Field`, not a `str`. The plain
> syntax `email: str = unique()` still works at runtime.

---

## `Unique()` (Deprecated)

> [!CAUTION]
> `Unique()` is deprecated and will be removed in a future version. Use
> [`unique()`](#unique) instead.

```python
from sqliter.model import Unique  # Deprecated
```

Wrapper around `unique()` that emits a `DeprecationWarning`.
