# SQLiter <!-- omit in toc -->

![PyPI - Version](https://img.shields.io/pypi/v/sqliter-py)
[![Test Suite](https://github.com/seapagan/sqliter-py/actions/workflows/testing.yml/badge.svg)](https://github.com/seapagan/sqliter-py/actions/workflows/testing.yml)
[![Linting](https://github.com/seapagan/sqliter-py/actions/workflows/linting.yml/badge.svg)](https://github.com/seapagan/sqliter-py/actions/workflows/linting.yml)
[![Type Checking](https://github.com/seapagan/sqliter-py/actions/workflows/mypy.yml/badge.svg)](https://github.com/seapagan/sqliter-py/actions/workflows/mypy.yml)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/sqliter-py)

SQLiter is a lightweight Object-Relational Mapping (ORM) library for SQLite
databases in Python. It provides a simplified interface for interacting with
SQLite databases using Pydantic models. The only external run-time dependency
is Pydantic itself.

It does not aim to be a full-fledged ORM like SQLAlchemy, but rather a simple
and easy-to-use library for basic database operations, especially for small
projects. It is NOT asynchronous and does not support complex queries (at this
time).

The ideal use case is more for Python CLI tools that need to store data in a
database-like format without needing to learn SQL or use a full ORM.

> [!IMPORTANT]
> This project is still in the early stages of development and is lacking some
> planned functionality. Please use with caution.
>
> Also, structures like `list`, `dict`, `set` etc are not supported **at this
> time** as field types, since SQLite does not have a native column type for
> these. I will look at implementing these in the future, probably by
> serializing them to JSON or pickling them and storing in a text field. For
> now, you can actually do this manually when creating your Model (use `TEXT` or
> `BLOB` fields), then serialize before saving after and retrieving data.
>
> See the [TODO](TODO.md) for planned features and improvements.

- [Features](#features)
- [Installation](#installation)
  - [Optional Dependencies](#optional-dependencies)
- [Quick Start](#quick-start)
- [Detailed Usage](#detailed-usage)
  - [Defining Models](#defining-models)
  - [Database Operations](#database-operations)
    - [Creating a Connection](#creating-a-connection)
    - [Using an In-Memory Database](#using-an-in-memory-database)
    - [Creating Tables](#creating-tables)
    - [Inserting Records](#inserting-records)
    - [Querying Records](#querying-records)
    - [Updating Records](#updating-records)
    - [Deleting Records](#deleting-records)
    - [Commit your changes](#commit-your-changes)
    - [Close the Connection](#close-the-connection)
  - [Transactions](#transactions)
  - [Ordering](#ordering)
  - [Field Control](#field-control)
    - [Selecting Specific Fields](#selecting-specific-fields)
    - [Excluding Specific Fields](#excluding-specific-fields)
    - [Returning exactly one explicit field only](#returning-exactly-one-explicit-field-only)
  - [Filter Options](#filter-options)
    - [Basic Filters](#basic-filters)
    - [Null Checks](#null-checks)
    - [Comparison Operators](#comparison-operators)
    - [List Operations](#list-operations)
    - [String Operations (Case-Sensitive)](#string-operations-case-sensitive)
    - [String Operations (Case-Insensitive)](#string-operations-case-insensitive)
- [Contributing](#contributing)
- [Exceptions](#exceptions)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## Features

- Table creation based on Pydantic models
- CRUD operations (Create, Read, Update, Delete)
- Basic query building with filtering, ordering, and pagination
- Transaction support
- Custom exceptions for better error handling
- Full type hinting and type checking
- No external dependencies other than Pydantic
- Full test coverage

## Installation

You can install SQLiter using whichever method you prefer or is compatible with
your project setup.

With `uv` which is rapidly becoming my favorite tool for managing projects and
virtual environments (`uv` is used for developing this project and in the CI):

```bash
uv add sqliter-py
```

With `pip`:

```bash
pip install sqliter-py
```

Or with `Poetry`:

```bash
poetry add sqliter-py
```

### Optional Dependencies

Currently by default, the only external dependency is Pydantic. However, there
are some optional dependencies that can be installed to enable additional
features:

- `inflect`: For pluralizing table names (if not specified). This just offers a
  more-advanced pluralization than the default method used. In most cases you
  will not need this.

These can be installed using `uv`:

```bash
uv add 'sqliter-py[extras]'
```

Or with `pip`:

```bash
pip install 'sqliter-py[extras]'
```

Or with `Poetry`:

```bash
poetry add 'sqliter-py[extras]'
```

## Quick Start

Here's a quick example of how to use SQLiter:

```python
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

# Define your model
class User(BaseDBModel):
    name: str
    age: int

    class Meta:
        table_name = "users"

# Create a database connection
db = SqliterDB("example.db")

# Create the table
db.create_table(User)

# Insert a record
user = User(name="John Doe", age=30)
db.insert(user)

# Query records
results = db.select(User).filter(name="John Doe").fetch_all()
for user in results:
    print(f"User: {user.name}, Age: {user.age}")

# Update a record
user.age = 31
db.update(user)

# Delete a record
db.delete(User, "John Doe")
```

## Detailed Usage

### Defining Models

Models in SQLiter are based on Pydantic's `BaseModel`. You can define your
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

For a standard database with an auto-incrementing integer 'id' primary key, you
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
> mentioned above. Of course, you can always specify the `table_name` manually
> in this case!

### Database Operations

#### Creating a Connection

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

#### Creating Tables

```python
db.create_table(User)
```

#### Inserting Records

```python
user = User(name="Jane Doe", age=25, email="jane@example.com")
db.insert(user)
```

#### Querying Records

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

#### Updating Records

```python
user.age = 26
db.update(user)
```

#### Deleting Records

```python
db.delete(User, "Jane Doe")
```

#### Commit your changes

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

#### Close the Connection

When you're done with the database connection, you should close it to release
resources:

```python
db.close()
```

Note that closing the connection will also commit any pending changes, unless
`auto_commit` is set to `False`.

### Transactions

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

### Ordering

For now we only support ordering by the single field. You can specify the
field to order by and whether to reverse the order:

```python
results = db.select(User).order("age", reverse=True).fetch_all()
```

This will order the results by the `age` field in descending order.

> [!WARNING]
>
> Previously ordering was done using the `direction` parameter with `asc` or
> `desc`, but this has been deprecated in favor of using the `reverse`
> parameter. The `direction` parameter still works, but will raise a
> `DeprecationWarning` and will be removed in a future release.

### Field Control

#### Selecting Specific Fields

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

#### Excluding Specific Fields

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

#### Returning exactly one explicit field only

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

### Filter Options

The `filter()` method in SQLiter supports various filter options to query records.

#### Basic Filters

- `__eq`: Equal to (default if no operator is specified)
  - Example: `name="John"` or `name__eq="John"`

#### Null Checks

- `__isnull`: Is NULL
  - Example: `email__isnull=True`
- `__notnull`: Is NOT NULL
  - Example: `email__notnull=True`

#### Comparison Operators

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

#### List Operations

- `__in`: In a list of values
  - Example: `status__in=["active", "pending"]`
- `__not_in`: Not in a list of values
  - Example: `category__not_in=["archived", "deleted"]`

#### String Operations (Case-Sensitive)

- `__startswith`: Starts with
  - Example: `name__startswith="A"`
- `__endswith`: Ends with
  - Example: `email__endswith=".com"`
- `__contains`: Contains
  - Example: `description__contains="important"`

#### String Operations (Case-Insensitive)

- `__istartswith`: Starts with (case-insensitive)
  - Example: `name__istartswith="a"`
- `__iendswith`: Ends with (case-insensitive)
  - Example: `email__iendswith=".COM"`
- `__icontains`: Contains (case-insensitive)
  - Example: `description__icontains="IMPORTANT"`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

See the [CONTRIBUTING](CONTRIBUTING.md) guide for more information.

Please note that this project is released with a Contributor Code of Conduct,
which you can read in the [CODE_OF_CONDUCT](CODE_OF_CONDUCT.md) file.

## Exceptions

SQLiter includes several custom exceptions to handle specific errors that may occur during database operations. These exceptions inherit from a common base class, `SqliterError`, to ensure consistency across error messages and behavior.

- **`SqliterError`**:
  - The base class for all exceptions in SQLiter. It captures the exception context and chains any previous exceptions.
  - **Message**: "An error occurred in the SQLiter package."

- **`DatabaseConnectionError`**:
  - Raised when the SQLite database connection fails.
  - **Message**: "Failed to connect to the database: '{}'."

- **`InvalidOffsetError`**:
  - Raised when an invalid offset value (0 or negative) is used in queries.
  - **Message**: "Invalid offset value: '{}'. Offset must be a positive integer."

- **`InvalidOrderError`**:
  - Raised when an invalid order value is used in queries, such as a non-existent field or an incorrect sorting direction.
  - **Message**: "Invalid order value - {}"

- **`TableCreationError`**:
  - Raised when a table cannot be created in the database.
  - **Message**: "Failed to create the table: '{}'."

- **`RecordInsertionError`**:
  - Raised when an error occurs during record insertion.
  - **Message**: "Failed to insert record into table: '{}'."

- **`RecordUpdateError`**:
  - Raised when an error occurs during record update.
  - **Message**: "Failed to update record in table: '{}'."

- **`RecordNotFoundError`**:
  - Raised when a record with the specified primary key is not found.
  - **Message**: "Failed to find a record for key '{}'".

- **`RecordFetchError`**:
  - Raised when an error occurs while fetching records from the database.
  - **Message**: "Failed to fetch record from table: '{}'."

- **`RecordDeletionError`**:
  - Raised when an error occurs during record deletion.
  - **Message**: "Failed to delete record from table: '{}'."

- **`InvalidFilterError`**:
  - Raised when an invalid filter field is used in a query.
  - **Message**: "Failed to apply filter: invalid field '{}'".

## License

This project is licensed under the MIT License.

Copyright (c) 2024 Grant Ramsay

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
OR OTHER DEALINGS IN THE SOFTWARE.

## Acknowledgements

SQLiter was initially developed as an experiment to see how helpful ChatGPT and
Claud AI can be to speed up the development process. The initial version of the
code was generated by ChatGPT, with subsequent manual/AI refinements and
improvements.
