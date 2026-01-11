# Connecting to the Database

## Creating a Connection

To connect to a database (and create the file if it does not already exist), you
create an instance of the `SqliterDB` class. This will automatically take care
of connecting to or creating the database file.

```python
from sqliter import SqliterDB

db = SqliterDB("your_database.db")
```

The default behavior is to automatically commit changes to the database after
each operation. If you want to disable this behavior, you can set `auto_commit=False`
when creating the database connection:

```python
db = SqliterDB("your_database.db", auto_commit=False)
```

It is then up to you to manually commit changes using the `commit()` method.
This can be useful when you want to perform multiple operations in a single
transaction without the overhead of committing after each operation.

### Using an In-Memory Database

If you want to use an in-memory database, you can set `memory=True` when
creating the database connection:

```python
db = SqliterDB(memory=True)
```

This will create an in-memory database that is not persisted to disk. If you
also specify a database name, it will be ignored.

```python
db = SqliterDB("ignored.db", memory=True)
```

The `ignored.db` file will not be created, and the database will be in-memory.
If you do not specify a database name, and do NOT set `memory=True`, an
exception will be raised.

> [!NOTE]
>
> You can also use `":memory:"` as the database name (same as normal with
> Sqlite) to create an in-memory database, this is just a cleaner and more
> descriptive way to do it.
>
> ```python
> db = SqliterDB(":memory:")
> ```

### Resetting the Database

If you want to reset an existing database when you create the SqliterDB object,
you can pass `reset=True`:

```python
db = SqliterDB("your_database.db", reset=True)
```

This will effectively drop all user tables from the database. The file itself is
not deleted, only the tables are dropped.

### Caching Options

SQLiter provides optional query result caching to improve performance by reducing
database queries. See the [Caching](caching.md) page for detailed information.

```python
db = SqliterDB(
    "your_database.db",
    cache_enabled=True,        # Enable caching (default: False)
    cache_max_size=1000,       # Max cached queries per table
    cache_ttl=60,              # Time-to-live in seconds (None = no expiry)
    cache_max_memory_mb=100,   # Memory limit per table in MB
)
```

## Database Properties

The `SqliterDB` class provides several properties to access information about
the database instance once it has been created. See the
[Properties](properties.md) page (next) for more details.
