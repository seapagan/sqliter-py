# Detailed Usage

## Defining Models

Models in SQLiter use Pydantic to encapsulate the logic. All models should
inherit from SQLiter's `BaseDBModel`. You can define your
models like this:

```python
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    name: str
    age: int
    email: str

    class Meta:
        table_name = "users"
        primary_key = "name"  # Default is "id"
        create_pk = False  # disable auto-creating an incrementing primary key - default is True
```

For a standard database with an auto-incrementing integer `id` primary key, you
do not need to specify the `primary_key` or `create_pk` fields. If you want to
specify a different primary key field name, you can do so using the
`primary_key` field in the `Meta` class.

If `table_name` is not specified, the table name will be the same as the model
name, converted to 'snake_case' and pluralized (e.g., `User` -> `users`). Also,
any 'Model' suffix will be removed (e.g., `UserModel` -> `users`). To override
this behavior, you can specify the `table_name` in the `Meta` class manually as
above.

> [!NOTE]
>
> The pluralization is pretty basic by default, and just consists of adding an
> 's' if not already there. This will fail on words like 'person' or 'child'. If
> you need more advanced pluralization, you can install the `extras` package as
> mentioned in the [installation](installation.md#optional-dependencies). Of
> course, you can always specify the `table_name` manually in this case!

## Database Operations

### Creating a Connection

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

#### Using an In-Memory Database

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

#### Resetting the Database

If you want to reset the database when you create the SqliterDB object, you can
pass `reset=True`:

```python
db = SqliterDB("your_database.db", reset=True)
```

This will effectively drop all user tables from the database. The file itself is
not deleted, only the tables are dropped.

### Creating Tables

```python
db.create_table(User)
```

> [!IMPORTANT]
>
> The Table is created **regardless** of the `auto_commit` setting.

By default, if the table already exists, it will not be created again and no
error will be raised. If you want to raise an exception if the table already
exists, you can set `exists_ok=False`:

```python
db.create_table(User, exists_ok=False)
```

This will raise a `TableCreationError` if the table already exists.

### Dropping Tables

```python
db.drop_table(User)
```

> [!IMPORTANT]
>
> The Table is dropped **regardless** of the `auto_commit` setting.

## Data operations

### Inserting Records

```python
user = User(name="Jane Doe", age=25, email="jane@example.com")
db.insert(user)
```

### Querying Records

```python
# Fetch all users
all_users = db.select(User).fetch_all()

# Filter users
young_users = db.select(User).filter(age=25).fetch_all()

# Order users
ordered_users = db.select(User).order("age", reverse=True).fetch_all()

# Limit and offset
paginated_users = db.select(User).limit(10).offset(20).fetch_all()
```

> [!IMPORTANT]
>
> The `select()` MUST come first, before any filtering, ordering, or pagination
> etc. This is the starting point for building your query.

See below for more advanced filtering options.

### Updating Records

```python
user.age = 26
db.update(user)
```

### Deleting Records

```python
db.delete(User, "Jane Doe")
```

### Commit your changes

By default, SQLiter will automatically commit changes to the database after each
operation. If you want to disable this behavior, you can set `auto_commit=False`
when creating the database connection:

```python
db = SqliterDB("your_database.db", auto_commit=False)
```

You can then manually commit changes using the `commit()` method:

```python
db.commit()
```

### Close the Connection

When you're done with the database connection, you should close it to release
resources:

```python
db.close()
```

Note that closing the connection will also commit any pending changes, unless
`auto_commit` is set to `False`.

## Transactions

SQLiter supports transactions using Python's context manager:

```python
with db:
    db.insert(User(name="Alice", age=30, email="alice@example.com"))
    db.insert(User(name="Bob", age=35, email="bob@example.com"))
    # If an exception occurs, the transaction will be rolled back
```

> [!WARNING]
> Using the context manager will automatically commit the transaction
> at the end (unless an exception occurs), regardless of the `auto_commit`
> setting.
>
> the `close()` method will also be called when the context manager exits, so you
> do not need to call it manually.

## Ordering

For now we only support ordering by the single field. You can specify the
field to order by and whether to reverse the order:

```python
results = db.select(User).order("age", reverse=True).fetch_all()
```

This will order the results by the `age` field in descending order.

If you do not specify a field, the default is to order by the primary key field:

```python
results = db.select(User).order().fetch_all()
```

This will order the results by the primary key field in ascending order.

> [!WARNING]
>
> Previously ordering was done using the `direction` parameter with `asc` or
> `desc`, but this has been deprecated in favor of using the `reverse`
> parameter. The `direction` parameter still works, but will raise a
> `DeprecationWarning` and will be removed in a future release.

## Field Control

### Selecting Specific Fields

By default, all commands query and return all fields in the table. If you want
to select only specific fields, you can pass them using the `fields()`
method:

```python
results = db.select(User).fields(["name", "age"]).fetch_all()
```

This will return only the `name` and `age` fields for each record.

You can also pass this as a parameter to the `select()` method:

```python
results = db.select(User, fields=["name", "age"]).fetch_all()
```

Note that using the `fields()` method will override any fields specified in the
'select()' method.

### Excluding Specific Fields

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

### Returning exactly one explicit field only

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

## Filter Options

The `filter()` method in SQLiter supports various filter options to query records.

### Basic Filters

- `__eq`: Equal to (default if no operator is specified)
  - Example: `name="John"` or `name__eq="John"`

### Null Checks

- `__isnull`: Is NULL
  - Example: `email__isnull=True`
- `__notnull`: Is NOT NULL
  - Example: `email__notnull=True`

### Comparison Operators

- `__lt`: Less than
  - Example: `age__lt=30`
- `__lte`: Less than or equal to
  - Example: `age__lte=30`
- `__gt`: Greater than
  - Example: `age__gt=30`
- `__gte`: Greater than or equal to
  - Example: `age__gte=30`
- `__ne`: Not equal to
  - Example: `status__ne="inactive"`

### List Operations

- `__in`: In a list of values
  - Example: `status__in=["active", "pending"]`
- `__not_in`: Not in a list of values
  - Example: `category__not_in=["archived", "deleted"]`

### String Operations (Case-Sensitive)

- `__startswith`: Starts with
  - Example: `name__startswith="A"`
- `__endswith`: Ends with
  - Example: `email__endswith=".com"`
- `__contains`: Contains
  - Example: `description__contains="important"`

### String Operations (Case-Insensitive)

- `__istartswith`: Starts with (case-insensitive)
  - Example: `name__istartswith="a"`
- `__iendswith`: Ends with (case-insensitive)
  - Example: `email__iendswith=".COM"`
- `__icontains`: Contains (case-insensitive)
  - Example: `description__icontains="IMPORTANT"`

## Debug Logging

You can enable debug logging to see the SQL queries being executed by SQLiter.
This can be useful for debugging and understanding the behavior of your
application. It is disabled by default, and can be set on the `SqliterDB` class:

```python
db = SqliterDB("your_database.db", debug=True)
```

This will print the SQL queries to the console as they are executed. If there is
an existing logger in your application then SQLiter will use that logger,
otherwise it will create and use a new logger named `sqliter`.
