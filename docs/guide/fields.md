# Field Control

## Selecting Specific Fields

By default, all commands query and return all fields in the table. If you want
to select only specific fields, you can pass them using the `fields()`
method:

```python
results = db.select(User).fields(["name", "age"]).fetch_all()
```

This will return only the `name` and `age` fields for each record.

> **Note:** When using `fields()` with ORM models, ensure you select all
> required (non-optional) fields. Pydantic validation will fail if required
> fields are missing from the query results.

You can also pass this as a parameter to the `select()` method:

```python
results = db.select(User, fields=["name", "age"]).fetch_all()
```

Note that using the `fields()` method will override any fields specified in the
'select()' method.

## Excluding Specific Fields

If you want to exclude specific fields from the results, you can use the
`exclude()` method:

```python
results = db.select(User).exclude(["email"]).fetch_all()
```

This will return all fields except the `email` field.

You can also pass this as a parameter to the `select()` method:

```python
results = db.select(User, exclude=["email"]).fetch_all()
```

## Returning exactly one explicit field only

If you only want to return a single field from the results, you can use the
`only()` method:

```python
result = db.select(User).only("name").fetch_first()
```

This will return only the `name` field for the first record.

This is exactly the same as using the `fields()` method with a single field, but
very specific and obvious. **There is NO equivalent argument to this in the
`select()` method**. An exception **WILL** be raised if you try to use this method
with more than one field.

## Complex Data Types

SQLiter supports storing complex Python data types in the database. The following types are supported:

- `list[T]`: Lists of any type T
- `dict[K, V]`: Dictionaries with keys of type K and values of type V
- `set[T]`: Sets of any type T
- `tuple[T, ...]`: Tuples of any type T

These types are automatically serialized and stored as BLOBs in the database. Here's an example of using complex types:

```python
from typing import Any
from sqliter import Model

class UserPreferences(Model):
    tags: list[str] = []  # List of string tags
    metadata: dict[str, Any] = {}  # Dictionary with string keys and any value type
    friends: set[int] = set()  # Set of user IDs
    coordinates: tuple[float, float] = (0.0, 0.0)  # Tuple of two floats

# Create and save an instance
prefs = UserPreferences(
    tags=["python", "sqlite", "orm"],
    metadata={"theme": "dark", "notifications": True},
    friends={1, 2, 3},
    coordinates=(51.5074, -0.1278)
)
prefs.save()

# Query and use the complex types
loaded_prefs = UserPreferences.get(prefs.id)
print(loaded_prefs.tags)  # ['python', 'sqlite', 'orm']
print(loaded_prefs.metadata["theme"])  # 'dark'
print(1 in loaded_prefs.friends)  # True
print(loaded_prefs.coordinates)  # (51.5074, -0.1278)
```

The complex types are automatically validated using Pydantic's type system, ensuring that only values of the correct type can be stored. When querying, the values are automatically deserialized back into their original Python types.

Note that since these types are stored as BLOBs, you cannot perform SQL operations on their contents (like searching or filtering). If you need to search or filter based on these values, you should consider storing them in a different format or in separate tables.
