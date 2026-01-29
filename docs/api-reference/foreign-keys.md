# Foreign Keys (Legacy Mode)

This page documents the legacy-mode foreign key support. For the
ORM-mode `ForeignKey` descriptor with lazy loading, see
[ORM Mode](orm.md).

**Source:** `sqliter/model/foreign_key.py`

See also: [Guide -- Foreign Keys](../guide/foreign-keys.md),
[Explicit Foreign Keys](../guide/foreign-keys/explicit.md)

---

## `FKAction`

Type alias for the allowed foreign key actions.

```python
FKAction = Literal["CASCADE", "SET NULL", "RESTRICT", "NO ACTION"]
```

| Value | Description |
|-------|-------------|
| `"CASCADE"` | Propagate the operation to referencing records (delete or update them) |
| `"SET NULL"` | Set the foreign key field to `NULL` (requires `null=True`) |
| `"RESTRICT"` | Prevent the operation if references exist (default) |
| `"NO ACTION"` | Similar to `RESTRICT` in SQLite |

---

## `ForeignKey()`

Factory function that creates a Pydantic `Field` with foreign key
metadata stored in `json_schema_extra`.

```python
def ForeignKey(
    to: type[BaseDBModel],
    *,
    on_delete: FKAction = "RESTRICT",
    on_update: FKAction = "RESTRICT",
    null: bool = False,
    unique: bool = False,
    related_name: str | None = None,
    db_column: str | None = None,
    default: Any = ...,
    **kwargs: Any,
) -> Any:
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `to` | `type[BaseDBModel]` | *required* | Target model class referenced by this FK |
| `on_delete` | `FKAction` | `"RESTRICT"` | Action when referenced record is deleted |
| `on_update` | `FKAction` | `"RESTRICT"` | Action when referenced record's PK is updated |
| `null` | `bool` | `False` | Whether the FK field can be `NULL` |
| `unique` | `bool` | `False` | Whether the FK must be unique (one-to-one) |
| `related_name` | `str` &#124; `None` | `None` | Name for reverse relationship (reserved) |
| `db_column` | `str` &#124; `None` | `None` | Custom column name; defaults to `{field_name}_id` |
| `default` | `Any` | `...` | Default value; auto-set to `None` if `null=True` |
| `**kwargs` | `Any` | | Additional arguments passed to Pydantic `Field` |

**Returns:**

A Pydantic `Field` with foreign key metadata.

**Raises:**

- [`InvalidForeignKeyError`](exceptions.md#invalidforeignkeyerror) --
  If `on_delete="SET NULL"` or `on_update="SET NULL"` is used without
  `null=True`.

**Example:**

```python
from sqliter.model import BaseDBModel, ForeignKey


class Author(BaseDBModel):
    name: str


class Book(BaseDBModel):
    title: str
    author_id: int = ForeignKey(Author, on_delete="CASCADE")
```

---

## `ForeignKeyInfo`

Dataclass holding metadata about a foreign key relationship. Created
internally by `ForeignKey()` and stored in the field's
`json_schema_extra["foreign_key"]`.

```python
@dataclass
class ForeignKeyInfo:
    to_model: type[BaseDBModel]
    on_delete: FKAction
    on_update: FKAction
    null: bool
    unique: bool
    related_name: str | None
    db_column: str | None
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `to_model` | `type[BaseDBModel]` | Target model class |
| `on_delete` | `FKAction` | Delete action |
| `on_update` | `FKAction` | Update action |
| `null` | `bool` | Whether the FK is nullable |
| `unique` | `bool` | Whether the FK must be unique |
| `related_name` | `str` &#124; `None` | Reverse relationship name |
| `db_column` | `str` &#124; `None` | Custom column name |

---

## `get_foreign_key_info()`

Extract `ForeignKeyInfo` from a Pydantic `FieldInfo` object, if the
field is a foreign key.

```python
def get_foreign_key_info(
    field_info: FieldInfo,
) -> ForeignKeyInfo | None:
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `field_info` | `FieldInfo` | *required* | The Pydantic field info to examine |

**Returns:**

`ForeignKeyInfo | None` -- The FK metadata if the field is a foreign
key, `None` otherwise.

**Example:**

```python
from sqliter.model.foreign_key import get_foreign_key_info

field_info = Book.model_fields["author_id"]
fk_info = get_foreign_key_info(field_info)
if fk_info:
    print(fk_info.to_model)   # <class 'Author'>
    print(fk_info.on_delete)  # "CASCADE"
```
