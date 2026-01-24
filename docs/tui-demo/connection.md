# Database Connection Demos

These demos show different ways to connect to SQLite databases using SQLiter.

## In-Memory Database

The fastest option for temporary data or testing. Data is lost when the database connection closes.

```python
# --8<-- [start:memory-db]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    name: str
    email: str

# Create an in-memory database
db = SqliterDB(memory=True)
db.create_table(User)

# Data exists only for the lifetime of the connection
user = db.insert(User(name="Alice", email="alice@example.com"))
db.close()
# Data is lost after close()
# --8<-- [end:memory-db]
```

### When to Use

- **Testing**: Perfect for unit tests where you need a fresh database each time
- **Caching**: Temporary cache data that doesn't need to persist
- **Prototyping**: Quickly test data models without creating files

### Performance

In-memory databases are typically 2-3x faster than file-based databases since there's no disk I/O.

## File-Based Database

For persistent data storage that survives application restarts.

```python
# --8<-- [start:file-db]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

import tempfile
import os

class User(BaseDBModel):
    name: str
    email: str

# Create a temporary database file
with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
    db_path = f.name

try:
    db = SqliterDB(database=db_path)
    db.create_table(User)

    # Data persists even after closing
    user = db.insert(User(name="Bob", email="bob@example.com"))
    db.close()

    # Reconnect and data is still there
    db = SqliterDB(database=db_path)
    users = db.select(User).fetch_all()
    print(f"Found {len(users)} users")
finally:
    # Clean up the test database
    if os.path.exists(db_path):
        os.remove(db_path)
# --8<-- [end:file-db]
```

### When to Use

- **Production Applications**: Any data that needs to persist
- **Data Analysis**: Working with existing SQLite databases
- **Web Applications**: Storing user data, sessions, etc.

### Best Practices

- Use absolute paths for database files to avoid confusion
- Consider database file location (e.g., user data directory)
- Handle file permissions appropriately

## Context Manager

Using SQLiter as a context manager ensures the database connection is properly closed, even if an error occurs.

```python
# --8<-- [start:context-manager]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Task(BaseDBModel):
    title: str
    done: bool = False

# Connection automatically closes when exiting the context
with SqliterDB(memory=True) as db:
    db.create_table(Task)
    task = db.insert(Task(title="Buy groceries"))
    # Connection is automatically closed here
# --8<-- [end:context-manager]
```

### Benefits

- **Automatic Cleanup**: Guaranteed connection closure
- **Exception Safety**: Connection closes even if errors occur
- **Cleaner Code**: No need to remember `db.close()`

### When to Use

- **Scripts**: Short-lived scripts that need database access
- **Batch Jobs**: Operations that open, process, and close
- **Testing**: Ensures clean test isolation

## Debug Mode

Enable SQL query logging to see exactly what SQL SQLiter is executing.

```python
# --8<-- [start:debug-mode]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Product(BaseDBModel):
    name: str
    price: float

# Enable debug mode to see SQL queries
db = SqliterDB(memory=True, debug=True)
db.create_table(Product)

product = db.insert(Product(name="Widget", price=19.99))
# Output shows: CREATE TABLE products...
# Output shows: INSERT INTO products...
# --8<-- [end:debug-mode]
```

### What You'll See

- `CREATE TABLE` statements when creating tables
- `INSERT` statements when adding records
- `SELECT` statements when querying data
- Parameter values being bound

### When to Use

- **Learning**: Understand how SQLiter translates Python to SQL
- **Debugging**: Troubleshoot query issues
- **Optimization**: Identify inefficient queries
- **Development**: See what's happening behind the scenes

!!! warning
    Debug mode outputs SQL queries to stderr. Don't enable in production unless needed for troubleshooting.

## Summary Table

| Method | Pros | Cons | Best For |
|--------|------|------|----------|
| **In-Memory** | Fast, no cleanup needed | Data lost on close | Tests, caching, prototyping |
| **File-Based** | Persistent data | Slower, file management | Production, real data |
| **Context Manager** | Auto cleanup, exception safe | Slightly more verbose | Scripts, batch jobs |
| **Debug Mode** | See SQL queries | Verbose output | Learning, debugging |

## Related Documentation

- [Models](models.md) - Define your data structure
- [CRUD Operations](crud.md) - Work with your data
- [Transactions](transactions.md) - Group operations atomically
