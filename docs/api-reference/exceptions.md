# Exceptions

All exceptions in SQLiter inherit from `SqliterError`. Import them from
`sqliter.exceptions`:

```python
from sqliter.exceptions import (
    SqliterError,
    DatabaseConnectionError,
    RecordInsertionError,
    # ...
)
```

**Source:** `sqliter/exceptions.py`

See also: [Guide -- Exceptions](../guide/exceptions.md)

## Hierarchy

```text
Exception
└── SqliterError
    ├── DatabaseConnectionError
    ├── TableCreationError
    ├── TableDeletionError
    ├── RecordInsertionError
    ├── RecordUpdateError
    ├── RecordNotFoundError
    ├── RecordFetchError
    ├── RecordDeletionError
    ├── InvalidFilterError
    ├── InvalidOffsetError
    ├── InvalidOrderError
    ├── InvalidRelationshipError
    ├── InvalidIndexError
    ├── ForeignKeyError
    │   ├── ForeignKeyConstraintError
    │   └── InvalidForeignKeyError
    └── SqlExecutionError
```

---

## Base Exception

### `SqliterError`

Base exception class for all SQLiter-specific errors.

```python
class SqliterError(Exception):
    message_template: str = "An error occurred in the SQLiter package."
```

**Attributes:**

| Attribute            | Type        | Description                                             |
| -------------------- | ----------- | ------------------------------------------------------- |
| `message_template`   | `str`       | Template string formatted with `*args`                  |
| `original_exception` | `Exception` | The caught exception that triggered this error (if any) |

**Behavior:**

- Formats `message_template` with positional `*args`.
- Captures the active exception via `sys.exc_info()` and appends its
  type, location, and message.
- Chains the original exception using `__cause__`.

---

## Connection Exceptions

### `DatabaseConnectionError`

Raised when a database connection cannot be established.

```python
message_template = "Failed to connect to the database: '{}'"
```

**Raised by:**

- [`SqliterDB.connect()`](sqliterdb.md#connect)

---

## Table Exceptions

### `TableCreationError`

Raised when a table cannot be created in the database.

```python
message_template = "Failed to create the table: '{}'"
```

**Raised by:**

- [`SqliterDB.create_table()`](sqliterdb.md#create_table)

### `TableDeletionError`

Raised when a table cannot be deleted from the database.

```python
message_template = "Failed to delete the table: '{}'"
```

**Raised by:**

- [`SqliterDB.drop_table()`](sqliterdb.md#drop_table)

---

## Record Exceptions

### `RecordInsertionError`

Raised when a record cannot be inserted into the database.

```python
message_template = "Failed to insert record into table: '{}'"
```

**Raised by:**

- [`SqliterDB.insert()`](sqliterdb.md#insert)

### `RecordUpdateError`

Raised when a record cannot be updated in the database.

```python
message_template = "Failed to update record in table: '{}'"
```

**Raised by:**

- [`SqliterDB.update()`](sqliterdb.md#update)

### `RecordNotFoundError`

Raised when a requested record is not found in the database.

```python
message_template = "Failed to find that record in the table (key '{}') "
```

**Raised by:**

- [`SqliterDB.update()`](sqliterdb.md#update) (when no rows match)
- [`SqliterDB.delete()`](sqliterdb.md#delete) (when no rows match)

### `RecordFetchError`

Raised on an error fetching records from the database.

```python
message_template = "Failed to fetch record from table: '{}'"
```

**Raised by:**

- [`SqliterDB.get()`](sqliterdb.md#get)
- [`QueryBuilder._execute_query()`](query-builder.md) (internal)

### `RecordDeletionError`

Raised when a record cannot be deleted from the database.

```python
message_template = "Failed to delete record from table: '{}'"
```

**Raised by:**

- [`SqliterDB.delete()`](sqliterdb.md#delete)
- [`QueryBuilder.delete()`](query-builder.md#delete)

---

## Query Exceptions

### `InvalidFilterError`

Raised when an invalid filter is applied to a query.

```python
message_template = "Failed to apply filter: invalid field '{}'"
```

**Raised by:**

- [`QueryBuilder.filter()`](query-builder.md#filter)

### `InvalidOffsetError`

Raised when an invalid offset value is provided.

```python
message_template = (
    "Invalid offset value: '{}'. Offset must be a positive integer."
)
```

**Raised by:**

- [`QueryBuilder.offset()`](query-builder.md#offset)

### `InvalidOrderError`

Raised when an invalid order specification is provided.

```python
message_template = "Invalid order value - {}"
```

**Raised by:**

- [`QueryBuilder.order()`](query-builder.md#order)

### `InvalidRelationshipError`

Raised when an invalid relationship path is specified in
`select_related()` or relationship filter traversal.

```python
message_template = (
    "Invalid relationship path '{}': field '{}' is not a valid "
    "foreign key relationship on model {}"
)
```

**Raised by:**

- [`QueryBuilder.select_related()`](query-builder.md#select_related)
- [`QueryBuilder.filter()`](query-builder.md#filter) (relationship
  traversal)

---

## Index Exceptions

### `InvalidIndexError`

Raised when one or more fields specified for an index do not exist
in the model's fields. Has a custom `__init__` that accepts structured
arguments.

```python
class InvalidIndexError(SqliterError):
    message_template = "Invalid fields for indexing in model '{}': {}"

    def __init__(
        self,
        invalid_fields: list[str],
        model_class: str,
    ) -> None:
```

**Parameters:**

| Parameter        | Type        | Description                           |
| ---------------- | ----------- | ------------------------------------- |
| `invalid_fields` | `list[str]` | Fields that do not exist in the model |
| `model_class`    | `str`       | Name of the model class               |

**Attributes:**

| Attribute        | Type        | Description                                         |
| ---------------- | ----------- | --------------------------------------------------- |
| `invalid_fields` | `list[str]` | The invalid field names (from `__init__` parameter) |
| `model_class`    | `str`       | The model class name (from `__init__` parameter)    |

**Raised by:**

- [`SqliterDB.create_table()`](sqliterdb.md#create_table) (during
  index creation)

---

## Foreign Key Exceptions

### `ForeignKeyError`

Base exception for foreign key related errors.

```python
message_template = "Foreign key error: {}"
```

### `ForeignKeyConstraintError`

Raised when a foreign key constraint is violated (e.g., inserting a
record with a FK value that does not exist in the referenced table, or
deleting a record that is still referenced).

```python
message_template = (
    "Foreign key constraint violation: Cannot {} record - "
    "referenced record {}"
)
```

**Raised by:**

- [`SqliterDB.insert()`](sqliterdb.md#insert) (FK value not in
  referenced table)
- [`SqliterDB.delete()`](sqliterdb.md#delete) (record still referenced
  with RESTRICT)

### `InvalidForeignKeyError`

Raised when an invalid foreign key configuration is detected (e.g.,
using `SET NULL` without `null=True`).

```python
message_template = "Invalid foreign key configuration: {}"
```

**Raised by:**

- [`ForeignKey()`](foreign-keys.md#foreignkey) factory function

---

## SQL Exceptions

### `SqlExecutionError`

Raised when a raw SQL execution fails.

```python
message_template = "Failed to execute SQL: '{}'"
```

**Raised by:**

- Internal `SqliterDB._execute_sql()` method (used by
  `create_table()`, `drop_table()`, and index creation)
