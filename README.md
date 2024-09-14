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

> [!NOTE]
> This project is still in the early stages of development and is lacking some
> planned functionality. Please use with caution.
>
> See the [TODO](TODO.md) for planned features and improvements.

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Detailed Usage](#detailed-usage)
  - [Defining Models](#defining-models)
  - [Database Operations](#database-operations)
    - [Creating a Connection](#creating-a-connection)
    - [Creating Tables](#creating-tables)
    - [Inserting Records](#inserting-records)
    - [Querying Records](#querying-records)
    - [Updating Records](#updating-records)
    - [Deleting Records](#deleting-records)
    - [Commit your changes](#commit-your-changes)
    - [Close the Connection](#close-the-connection)
  - [Transactions](#transactions)
  - [Filter Options](#filter-options)
    - [Basic Filters](#basic-filters)
    - [Null Checks](#null-checks)
    - [Comparison Operators](#comparison-operators)
    - [List Operations](#list-operations)
    - [String Operations (Case-Sensitive)](#string-operations-case-sensitive)
    - [String Operations (Case-Insensitive)](#string-operations-case-insensitive)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## Features

- Table creation based on Pydantic models
- CRUD operations (Create, Read, Update, Delete)
- Basic query building with filtering, ordering, and pagination
- Transaction support
- Custom exceptions for better error handling

## Installation

You can install SQLiter using whichever method you prefer or is compatible with
your project setup.

With `pip`:

```bash
pip install sqliter-py
```

Or `Poetry`:

```bash
poetry add sqliter-py
```

Or `uv` which is rapidly becoming my favorite tool for managing projects and
virtual environments (`uv` is used for developing this project and in the CI):

```bash
uv add sqliter-py
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
        create_id = False  # Set to True to auto-create an ID field
```

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
ordered_users = db.select(User).order("age", direction="DESC").fetch_all()

# Limit and offset
paginated_users = db.select(User).limit(10).offset(20).fetch_all()
```

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
> the 'close()' method will also be called when the context manager exits, so you
> do not need to call it manually.

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

## License

This project is licensed under the MIT License.

## Acknowledgements

SQLiter was initially developed as an experiment to see how helpful ChatGPT and
Claud AI can be to speed up the development process. The initial version of the
code was generated by ChatGPT, with subsequent manual/AI refinements and
improvements.
