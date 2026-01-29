# SqliterDB

The main entry point for all database operations. Manages SQLite
connections, table creation, CRUD operations, caching, and
transactions.

```python
from sqliter import SqliterDB
```

**Source:** `sqliter/sqliter.py`

See also: [Guide -- Connecting](../guide/connecting.md),
[Guide -- Properties](../guide/properties.md),
[Guide -- Tables](../guide/tables.md),
[Guide -- Data Operations](../guide/data-operations.md),
[Guide -- Caching](../guide/caching.md),
[Guide -- Transactions](../guide/transactions.md)

---

## Class Attribute

### `MEMORY_DB`

Constant for in-memory database filename.

```python
MEMORY_DB = ":memory:"
```

---

## Constructor

```python
def __init__(
    self,
    db_filename: str | None = None,
    *,
    memory: bool = False,
    auto_commit: bool = True,
    debug: bool = False,
    logger: logging.Logger | None = None,
    reset: bool = False,
    return_local_time: bool = True,
    cache_enabled: bool = False,
    cache_max_size: int = 1000,
    cache_ttl: int | None = None,
    cache_max_memory_mb: int | None = None,
) -> None:
```

**Parameters:**

| Parameter             | Type                   | Default | Description                              |
| --------------------- | ---------------------- | ------- | ---------------------------------------- |
| `db_filename`         | `str` &#124; `None`    | `None`  | Path to the SQLite database file         |
| `memory`              | `bool`                 | `False` | If `True`, create an in-memory database  |
| `auto_commit`         | `bool`                 | `True`  | Auto-commit after each operation         |
| `debug`               | `bool`                 | `False` | Enable SQL debug logging                 |
| `logger`              | `Logger` &#124; `None` | `None`  | Custom logger for debug output           |
| `reset`               | `bool`                 | `False` | Drop all tables on initialization        |
| `return_local_time`   | `bool`                 | `True`  | Return local time for datetime fields    |
| `cache_enabled`       | `bool`                 | `False` | Enable query result caching              |
| `cache_max_size`      | `int`                  | `1000`  | Max cached queries per table (LRU)       |
| `cache_ttl`           | `int` &#124; `None`    | `None`  | Time-to-live for cache entries (seconds) |
| `cache_max_memory_mb` | `int` &#124; `None`    | `None`  | Max memory for cache (MB)                |

**Raises:**

- `ValueError` -- If no filename is provided for a non-memory
  database, if `cache_max_size <= 0`, if `cache_ttl < 0`, or if
  `cache_max_memory_mb <= 0`.

**Example:**

```python
# File-based database
db = SqliterDB("myapp.db")

# In-memory database
db = SqliterDB(memory=True)

# With caching enabled
db = SqliterDB(
    "myapp.db",
    cache_enabled=True,
    cache_ttl=300,
    cache_max_memory_mb=50,
)
```

---

## Properties

### `filename`

Returns the database filename, or `None` if using an in-memory
database.

| Type                | Description                       |
| ------------------- | --------------------------------- |
| `str` &#124; `None` | File path or `None` for in-memory |

### `is_memory`

Returns `True` if the database is in-memory.

| Type   | Description                     |
| ------ | ------------------------------- |
| `bool` | `True` for `:memory:` databases |

### `is_autocommit`

Returns `True` if auto-commit is enabled.

| Type   | Description                 |
| ------ | --------------------------- |
| `bool` | Current auto-commit setting |

### `is_connected`

Returns `True` if a database connection is currently open.

| Type   | Description       |
| ------ | ----------------- |
| `bool` | Connection status |

### `table_names`

Returns a list of all table names in the database. Temporarily
connects if not already connected and restores the connection state
afterward.

| Type        | Description                                             |
| ----------- | ------------------------------------------------------- |
| `list[str]` | All user table names (excludes `sqlite_` system tables) |

**Example:**

```python
db = SqliterDB("myapp.db")
print(db.table_names)  # ["users", "posts", ...]
```

---

## Connection Methods

### `connect()`

Establish a connection to the SQLite database. Enables foreign key
constraint enforcement via `PRAGMA foreign_keys = ON`.

```python
def connect(self) -> sqlite3.Connection:
```

**Returns:**

`sqlite3.Connection` -- The SQLite connection object.

**Raises:**

- [`DatabaseConnectionError`](exceptions.md#databaseconnectionerror)
  -- If unable to connect.

### `close()`

Close the database connection. Commits pending changes if
`auto_commit` is `True`. Clears the query cache and resets cache
statistics.

```python
def close(self) -> None:
```

### `commit()`

Explicitly commit the current transaction.

```python
def commit(self) -> None:
```

---

## Table Methods

### `create_table()`

Create a database table based on a model class. Handles column
definitions, primary keys, foreign key constraints, and indexes.

```python
def create_table(
    self,
    model_class: type[BaseDBModel],
    *,
    exists_ok: bool = True,
    force: bool = False,
) -> None:
```

**Parameters:**

| Parameter     | Type                | Default    | Description                             |
| ------------- | ------------------- | ---------- | --------------------------------------- |
| `model_class` | `type[BaseDBModel]` | *required* | The model class defining the table      |
| `exists_ok`   | `bool`              | `True`     | If `True`, do not raise if table exists |
| `force`       | `bool`              | `False`    | If `True`, drop and recreate the table  |

**Raises:**

- [`TableCreationError`](exceptions.md#tablecreationerror) -- If there
  is an error creating the table.
- [`InvalidIndexError`](exceptions.md#invalidindexerror) -- If index
  fields do not exist in the model.

**Example:**

```python
db.create_table(User)
db.create_table(User, force=True)  # Drop and recreate
```

### `drop_table()`

Drop the table associated with a model class.

```python
def drop_table(
    self,
    model_class: type[BaseDBModel],
) -> None:
```

**Parameters:**

| Parameter     | Type                | Default    | Description                         |
| ------------- | ------------------- | ---------- | ----------------------------------- |
| `model_class` | `type[BaseDBModel]` | *required* | The model class whose table to drop |

**Raises:**

- [`TableDeletionError`](exceptions.md#tabledeletionerror) -- If there
  is an error dropping the table.

---

## CRUD Methods

### `insert()`

Insert a new record into the database. Sets `created_at` and
`updated_at` timestamps automatically.

```python
def insert(
    self,
    model_instance: T,
    *,
    timestamp_override: bool = False,
) -> T:
```

**Parameters:**

| Parameter            | Type   | Default    | Description                                           |
| -------------------- | ------ | ---------- | ----------------------------------------------------- |
| `model_instance`     | `T`    | *required* | The model instance to insert                          |
| `timestamp_override` | `bool` | `False`    | If `True`, respect provided non-zero timestamp values |

**Returns:**

`T` -- A new model instance with `pk` set to the inserted row's ID.

**Raises:**

- [`RecordInsertionError`](exceptions.md#recordinsertionerror) -- If
  there is an error during insertion.
- [`ForeignKeyConstraintError`](exceptions.md#foreignkeyconstrainterror)
  -- If a FK value does not exist in the referenced table.

**Example:**

```python
user = User(name="Alice", email="alice@example.com")
saved = db.insert(user)
print(saved.pk)  # e.g. 1
```

### `get()`

Retrieve a single record by its primary key.

```python
def get(
    self,
    model_class: type[T],
    primary_key_value: int,
) -> T | None:
```

**Parameters:**

| Parameter           | Type      | Default    | Description           |
| ------------------- | --------- | ---------- | --------------------- |
| `model_class`       | `type[T]` | *required* | The model class       |
| `primary_key_value` | `int`     | *required* | The primary key value |

**Returns:**

`T | None` -- The model instance if found, `None` otherwise.

**Raises:**

- [`RecordFetchError`](exceptions.md#recordfetcherror) -- If there is
  an error fetching the record.

**Example:**

```python
user = db.get(User, 1)
if user:
    print(user.name)
```

### `update()`

Update an existing record. The model instance must have a valid `pk`.
Automatically sets `updated_at` to the current time.

```python
def update(
    self,
    model_instance: BaseDBModel,
) -> None:
```

**Parameters:**

| Parameter        | Type          | Default    | Description                  |
| ---------------- | ------------- | ---------- | ---------------------------- |
| `model_instance` | `BaseDBModel` | *required* | The model instance to update |

**Raises:**

- [`RecordUpdateError`](exceptions.md#recordupdateerror) -- If there
  is an error updating the record.
- [`RecordNotFoundError`](exceptions.md#recordnotfounderror) -- If no
  record matches the `pk`.

**Example:**

```python
user = db.get(User, 1)
user.name = "Bob"
db.update(user)
```

### `delete()`

Delete a record by its primary key.

```python
def delete(
    self,
    model_class: type[BaseDBModel],
    primary_key_value: int | str,
) -> None:
```

**Parameters:**

| Parameter           | Type                | Default    | Description                             |
| ------------------- | ------------------- | ---------- | --------------------------------------- |
| `model_class`       | `type[BaseDBModel]` | *required* | The model class                         |
| `primary_key_value` | `int` &#124; `str`  | *required* | The primary key of the record to delete |

**Raises:**

- [`RecordDeletionError`](exceptions.md#recorddeletionerror) -- If
  there is an error deleting the record.
- [`RecordNotFoundError`](exceptions.md#recordnotfounderror) -- If no
  record matches the `pk`.
- [`ForeignKeyConstraintError`](exceptions.md#foreignkeyconstrainterror)
  -- If the record is still referenced (with `RESTRICT`).

**Example:**

```python
db.delete(User, 1)
```

### `select()`

Create a [`QueryBuilder`](query-builder.md) for constructing queries
with filters, ordering, pagination, and more.

```python
def select(
    self,
    model_class: type[T],
    fields: list[str] | None = None,
    exclude: list[str] | None = None,
) -> QueryBuilder[T]:
```

**Parameters:**

| Parameter     | Type                      | Default    | Description              |
| ------------- | ------------------------- | ---------- | ------------------------ |
| `model_class` | `type[T]`                 | *required* | The model class to query |
| `fields`      | `list[str]` &#124; `None` | `None`     | Fields to include        |
| `exclude`     | `list[str]` &#124; `None` | `None`     | Fields to exclude        |

**Returns:**

[`QueryBuilder[T]`](query-builder.md) -- A query builder for method
chaining.

**Example:**

```python
# Simple query
users = db.select(User).fetch_all()

# With filters and ordering
users = (
    db.select(User)
    .filter(active=True)
    .order("name")
    .limit(10)
    .fetch_all()
)

# Exclude fields
users = db.select(User, exclude=["password_hash"]).fetch_all()
```

---

## Cache Methods

### `get_cache_stats()`

Get cache performance statistics.

```python
def get_cache_stats(self) -> dict[str, int | float]:
```

**Returns:**

`dict[str, int | float]` -- Dictionary with keys:

| Key        | Type    | Description                     |
| ---------- | ------- | ------------------------------- |
| `hits`     | `int`   | Number of cache hits            |
| `misses`   | `int`   | Number of cache misses          |
| `total`    | `int`   | Total cache lookups             |
| `hit_rate` | `float` | Hit rate as percentage (0--100) |

**Example:**

```python
stats = db.get_cache_stats()
print(f"Hit rate: {stats['hit_rate']}%")
```

### `clear_cache()`

Clear all cached query results. Cache statistics (hits/misses) are
preserved.

```python
def clear_cache(self) -> None:
```

---

## Context Manager

`SqliterDB` can be used as a context manager for transaction
management. Within a `with` block, auto-commit is suppressed and all
operations are wrapped in a single transaction.

```python
def __enter__(self) -> Self:
def __exit__(
    self,
    exc_type: type[BaseException] | None,
    exc_value: BaseException | None,
    traceback: TracebackType | None,
) -> None:
```

**Behavior:**

- **`__enter__`**: Opens a connection and begins a transaction.
- **`__exit__` (no exception)**: Commits the transaction and closes
  the connection.
- **`__exit__` (exception raised)**: Rolls back the transaction and
  closes the connection.
- Cache is cleared on exit in both cases.

**Example:**

```python
db = SqliterDB("myapp.db")

with db:
    db.create_table(User)
    db.insert(User(name="Alice"))
    db.insert(User(name="Bob"))
    # Both inserts are committed together on exit

# If an exception occurs, both inserts are rolled back
```

See also: [Guide -- Transactions](../guide/transactions.md)
