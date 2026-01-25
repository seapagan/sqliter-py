# Database Connection Demos

These demos show different ways to connect to SQLite databases using SQLiter.

## In-Memory Database

The fastest option for temporary data or testing. Data is lost when the database connection closes.

```python
# --8<-- [start:memory-db]
from sqliter import SqliterDB

db = SqliterDB(memory=True)
print(f"Created database: {db}")
print(f"Is memory: {db.is_memory}")
print(f"Filename: {db.filename}")

db.connect()
print(f"Connected: {db.is_connected}")

db.close()
print(f"After close: {db.is_connected}")
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
import tempfile
from pathlib import Path

with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
    db_path = f.name

try:
    db = SqliterDB(db_path)
    print("Created file database")
    print(f"Filename: {db.filename}")
    print(f"Is memory: {db.is_memory}")

    db.connect()
    print(f"Connected to: {db_path}")
    db.close()
finally:
    Path(db_path).unlink(missing_ok=True)
    print("Cleaned up database file")
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

Using SQLiter as a context manager provides automatic transaction management with auto-commit on success.

```python
# --8<-- [start:context-manager]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Task(BaseDBModel):
    title: str
    done: bool = False

print("Using context manager for transactions:\n")

db = SqliterDB(memory=True)

with db:
    db.create_table(Task)
    task = db.insert(Task(title="Learn SQLiter", done=False))
    print(f"Inserted: {task.title} (pk={task.pk})")
    print("Transaction auto-commits on exit")

print(f"\nAfter context: connected={db.is_connected}")
# --8<-- [end:context-manager]
```

### Benefits

- **Automatic Commit**: Transaction commits when context exits successfully
- **Automatic Rollback**: Changes are rolled back if an error occurs
- **Cleaner Code**: No need to manually call `db.commit()`

### When to Use

- **Grouped Operations**: Multiple operations that should succeed or fail together
- **Data Integrity**: Operations that must be atomic
- **Error Safety**: Ensure changes aren't partially applied

## Debug Mode

Enable SQL query logging to see exactly what SQL SQLiter is executing.

```python
# --8<-- [start:debug-mode]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

print("Debug mode enables SQL query logging.")
print("When debug=True, all SQL queries are logged.\n")

db = SqliterDB(memory=True, debug=True)
db.create_table(BaseDBModel)

print("SQL queries would be logged to console:")
print('  CREATE TABLE IF NOT EXISTS "users" (...)')

db.close()
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
