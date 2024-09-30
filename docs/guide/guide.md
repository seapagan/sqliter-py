
# SQLiter Overview

SQLiter is a lightweight Python library designed to simplify database operations
using Pydantic models. It provides a range of functionality including table
creation, CRUD operations, querying, filtering, and more. This overview briefly
introduces each feature.

## Basic Setup

To get started, import the necessary modules and define a Pydantic model for
your table:

```python
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    name: str
    age: int
    email: str

# Create a database connection
db = SqliterDB("example.db")
```

## Table Creation

SQLiter allows you to create tables automatically based on your models:

```python
db.create_table(User)
```

This creates a table for the `User` model, with fields based on the attributes
of the model.

## Inserting Records

Inserting records is straightforward with SQLiter:

```python
user = User(name="John Doe", age=30, email="john@example.com")
db.insert(user)
```

## Basic Queries

You can easily query all records from a table:

```python
all_users = db.select(User).fetch_all()
```

### Filtering Results

SQLiter allows filtering of results using various conditions:

```python
young_users = db.select(User).filter(age__lt=30).fetch_all()
```

<!-- Multiple filters can be combined for more specific queries:

```python
results = db.select(User).filter(age__gt=20, age__lt=40).fetch_all()
```
-->

## Fetching Records

SQLiter provides methods to fetch multiple, single, or the last record in a
table.

### Fetching All Records

The `fetch_all()` method retrieves all records from the table that match the
query or filter:

```python
all_users = db.select(User).fetch_all()
```

This returns a list of all matching records. If no record matches, an empty list
is returned.

### Fetching One Record

The `fetch_one()` method retrieves a single record that matches the query or
filter:

```python
result = db.select(User).filter(name="John Doe").fetch_one()
```

If no record is found, `None` is returned.

### Fetching the Last Record

The `fetch_last()` method retrieves the last record in the table, typically
based on the `rowid`:

```python
last_user = db.select(User).fetch_last()
```

This fetches the most recently inserted record. If no record is found, `None` is
returned.

## Updating Records

Records can be updated seamlessly:

```python
user.age = 31
db.update(user)
```

## Deleting Records

Deleting records is simple as well:

```python
db.delete(User, "John Doe")
```

## Advanced Query Features

### Ordering

SQLiter supports ordering of results by specific fields:

```python
ordered_users = db.select(User).order("age", reverse=True).fetch_all()
```

### Limiting and Offsetting

Pagination is supported through `limit()` and `offset()`:

```python
paginated_users = db.select(User).limit(10).offset(20).fetch_all()
```

## Transactions

SQLiter supports transactions using Python's context manager. This ensures that
a group of operations are executed atomically, meaning either all of the
operations succeed or none of them are applied.

To use transactions, simply wrap the operations within a `with` block:

```python
with db:
    db.insert(User(name="Alice", age=30, email="alice@example.com"))
    db.insert(User(name="Bob", age=35, email="bob@example.com"))
    # If an exception occurs here, both inserts will be rolled back
```

If an error occurs within the transaction block, all changes made inside the
block will be rolled back automatically.

If no errors occur, the transaction will commit and changes will be saved. The
`close()` method will also be called when the context manager exits, so there is
no need to call it manually.

## Closing the Database

Always remember to close the connection when you're done:

```python
db.close()
```

> [!NOTE]
>
> If you are using the database connection as a context manager (see above), you
> do not need to call `close()` explicitly. The connection will be closed
> automatically when the context manager exits, and any changes **will be
> committed**.

This is a quick look at the core features of SQLiter. For more details on each
functionality, see the next section.