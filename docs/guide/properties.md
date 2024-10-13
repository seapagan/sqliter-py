
# SqliterDB Properties

## Overview

The `SqliterDB` class includes several useful **read-only** properties that
provide insight into the current state of the database. These properties allow
users to easily query key database attributes, such as the filename, whether the
database is in memory, auto-commit status, and the list of tables.

### Properties

1. **`filename`**
   Returns the filename of the database, or `None` if the database is in-memory.

   **Usage Example**:

   ```python
   db = SqliterDB(db_filename="test.db")
   print(db.filename)  # Output: 'test.db'
   ```

2. **`is_memory`**
   Returns `True` if the database is in-memory, otherwise `False`.

   **Usage Example**:

   ```python
   db = SqliterDB(memory=True)
   print(db.is_memory)  # Output: True
   ```

3. **`is_autocommit`**
   Returns `True` if the database is in auto-commit mode, otherwise `False`.

   **Usage Example**:

   ```python
   db = SqliterDB(auto_commit=True)
   print(db.is_autocommit)  # Output: True
   ```

4. **`table_names`**
   Returns a list of all user-defined table names in the database. The property temporarily reconnects if the connection is closed.

   **Usage Example**:

   ```python
   db = SqliterDB(memory=True)
   db.create_table(User)  # Assume 'User' is a predefined model
   print(db.table_names)  # Output: ['user']
   ```

## Property Details

### `filename`

This property allows users to retrieve the current database filename. For in-memory databases, this property returns `None`, as no filename is associated with an in-memory database.

- **Type**: `Optional[str]`
- **Returns**: The database filename or `None` if in memory.

### `is_memory`

This property indicates whether the database is in memory. It simplifies the check for memory-based databases, returning `True` for in-memory and `False` otherwise.

- **Type**: `bool`
- **Returns**: `True` if the database is in memory, otherwise `False`.

### `is_autocommit`

This property returns whether the database is in auto-commit mode. If `auto_commit` is enabled, every operation is automatically committed without requiring an explicit `commit()` call.

- **Type**: `bool`
- **Returns**: `True` if auto-commit mode is enabled, otherwise `False`.

### `table_names`

This property retrieves a list of user-defined table names from the database. It does not include system tables (`sqlite_`). If the database connection is closed, this property will temporarily reconnect to query the table names and close the connection afterward.

- **Type**: `list[str]`
- **Returns**: A list of user-defined table names in the database.
- **Raises**: `DatabaseConnectionError` if the database connection fails to re-establish.

## Example

Here's a complete example demonstrating the use of the new properties:

```python
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

# Define a simple model
class User(BaseDBModel):
    id: int
    name: str

# Create an in-memory database
db = SqliterDB(memory=True)
db.create_table(User)

# Access properties
print(db.filename)        # Output: None
print(db.is_memory)       # Output: True
print(db.is_autocommit)   # Output: True (this is the default)
print(db.table_names)     # Output: ['user']
```
