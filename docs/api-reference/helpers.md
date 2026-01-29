# Helpers & Constants

Internal utility functions and constant mappings used by the SQLiter
library. These are not part of the public API but are documented here
for completeness.

**Sources:** `sqliter/helpers.py`, `sqliter/constants.py`

---

## Functions

### `infer_sqlite_type()`

Map a Python type to its corresponding SQLite column type. Used during
table creation.

```python
def infer_sqlite_type(
    field_type: type | None,
) -> str:
```

**Parameters:**

| Parameter    | Type                 | Default    | Description            |
| ------------ | -------------------- | ---------- | ---------------------- |
| `field_type` | `type` &#124; `None` | *required* | The Python type to map |

**Returns:**

`str` -- The SQLite column type (e.g., `"INTEGER"`, `"TEXT"`). Defaults
to `"TEXT"` if the type is `None` or not recognized.

**Example:**

```python
from sqliter.helpers import infer_sqlite_type

infer_sqlite_type(int)    # "INTEGER"
infer_sqlite_type(str)    # "TEXT"
infer_sqlite_type(float)  # "REAL"
infer_sqlite_type(None)   # "TEXT"
```

---

### `to_unix_timestamp()`

Convert a `datetime` or `date` object to a Unix timestamp (integer) in
UTC. Naive datetimes are assumed to be in the user's local timezone.

```python
def to_unix_timestamp(
    value: datetime.date | datetime.datetime,
) -> int:
```

**Parameters:**

| Parameter | Type                                       | Default    | Description          |
| --------- | ------------------------------------------ | ---------- | -------------------- |
| `value`   | `datetime.date` &#124; `datetime.datetime` | *required* | The value to convert |

**Returns:**

`int` -- Unix timestamp.

**Raises:**

- `TypeError` -- If `value` is not a `datetime` or `date` object.

**Example:**

```python
import datetime
from sqliter.helpers import to_unix_timestamp

dt = datetime.datetime(2024, 1, 15, 12, 0, 0)
ts = to_unix_timestamp(dt)  # e.g. 1705320000
```

---

### `from_unix_timestamp()`

Convert a Unix timestamp back to a `datetime` or `date` object,
optionally converting to the user's local timezone.

```python
def from_unix_timestamp(
    value: int,
    to_type: type,
    *,
    localize: bool = True,
) -> datetime.date | datetime.datetime:
```

**Parameters:**

| Parameter  | Type   | Default    | Description                                          |
| ---------- | ------ | ---------- | ---------------------------------------------------- |
| `value`    | `int`  | *required* | The Unix timestamp                                   |
| `to_type`  | `type` | *required* | Target type (`datetime.datetime` or `datetime.date`) |
| `localize` | `bool` | `True`     | If `True`, convert to local timezone                 |

**Returns:**

`datetime.date | datetime.datetime` -- The converted value.

**Raises:**

- `TypeError` -- If `to_type` is not `datetime.datetime` or
  `datetime.date`.

**Example:**

```python
import datetime
from sqliter.helpers import from_unix_timestamp

dt = from_unix_timestamp(1705320000, datetime.datetime)
d = from_unix_timestamp(1705320000, datetime.date)
```

---

## Constants

### `OPERATOR_MAPPING`

Maps SQLiter filter operator suffixes to their SQL equivalents. Used by
[`QueryBuilder.filter()`](query-builder.md#filter).

| Operator        | SQL           | Description                    |
| --------------- | ------------- | ------------------------------ |
| `__lt`          | `<`           | Less than                      |
| `__lte`         | `<=`          | Less than or equal             |
| `__gt`          | `>`           | Greater than                   |
| `__gte`         | `>=`          | Greater than or equal          |
| `__eq`          | `=`           | Equal (default when no suffix) |
| `__ne`          | `!=`          | Not equal                      |
| `__in`          | `IN`          | Value in list                  |
| `__not_in`      | `NOT IN`      | Value not in list              |
| `__isnull`      | `IS NULL`     | Field is NULL                  |
| `__notnull`     | `IS NOT NULL` | Field is not NULL              |
| `__like`        | `LIKE`        | Raw SQL LIKE pattern           |
| `__startswith`  | `GLOB`        | Case-sensitive starts with     |
| `__endswith`    | `GLOB`        | Case-sensitive ends with       |
| `__contains`    | `GLOB`        | Case-sensitive contains        |
| `__istartswith` | `LIKE`        | Case-insensitive starts with   |
| `__iendswith`   | `LIKE`        | Case-insensitive ends with     |
| `__icontains`   | `LIKE`        | Case-insensitive contains      |

> [!NOTE]
> The `__startswith`, `__endswith`, and `__contains` operators use SQLite's
> `GLOB` for case-sensitive matching. The `i`-prefixed variants use `LIKE`
> for case-insensitive matching.
> The `__like` operator expects a full SQL `LIKE` pattern (including any `%`
> wildcards).

---

### `SQLITE_TYPE_MAPPING`

Maps Python types to SQLite column types. Used by
[`infer_sqlite_type()`](#infer_sqlite_type).

| Python Type         | SQLite Type | Notes                    |
| ------------------- | ----------- | ------------------------ |
| `int`               | `INTEGER`   |                          |
| `float`             | `REAL`      |                          |
| `str`               | `TEXT`      |                          |
| `bool`              | `INTEGER`   | Stored as 0 or 1         |
| `bytes`             | `BLOB`      |                          |
| `datetime.datetime` | `INTEGER`   | Stored as Unix timestamp |
| `datetime.date`     | `INTEGER`   | Stored as Unix timestamp |
| `list`              | `BLOB`      | Serialized with `pickle` |
| `dict`              | `BLOB`      | Serialized with `pickle` |
| `set`               | `BLOB`      | Serialized with `pickle` |
| `tuple`             | `BLOB`      | Serialized with `pickle` |
