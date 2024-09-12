# SQLiter

![PyPI - Version](https://img.shields.io/pypi/v/sqliter-py)
[![Test Suite](https://github.com/seapagan/sqliter-py/actions/workflows/testing.yml/badge.svg)](https://github.com/seapagan/sqliter-py/actions/workflows/testing.yml)
[![Linting](https://github.com/seapagan/sqliter-py/actions/workflows/linting.yml/badge.svg)](https://github.com/seapagan/sqliter-py/actions/workflows/linting.yml)
[![Type Checking](https://github.com/seapagan/sqliter-py/actions/workflows/mypy.yml/badge.svg)](https://github.com/seapagan/sqliter-py/actions/workflows/mypy.yml)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/sqliter-py)

SQLiter is a lightweight Object-Relational Mapping (ORM) library for SQLite
databases in Python. It provides a simplified interface for interacting with
SQLite databases using Pydantic models.

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

## Features

- Table creation based on Pydantic models
- CRUD operations (Create, Read, Update, Delete)
- Basic query building with filtering, ordering, and pagination
- Transaction support
- Custom exceptions for better error handling

## Installation

You can install SQLiter using pip:

```bash
pip install sqliter-py
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
db = SqliterDB("example.db", auto_commit=True)

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

db = SqliterDB("your_database.db", auto_commit=True)
```

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
ordered_users = db.select(User).order("age DESC").fetch_all()

# Limit and offset
paginated_users = db.select(User).limit(10).offset(20).fetch_all()
```

Note: The filtering in SQLiter is basic and supports exact matches. Complex
queries like `age__lt` are not supported in the current implementation.

#### Updating Records

```python
user.age = 26
db.update(user)
```

#### Deleting Records

```python
db.delete(User, "Jane Doe")
```

### Transactions

SQLiter supports transactions using Python's context manager:

```python
with db:
    db.insert(User(name="Alice", age=30, email="alice@example.com"))
    db.insert(User(name="Bob", age=35, email="bob@example.com"))
    # If an exception occurs, the transaction will be rolled back
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

## Acknowledgements

SQLiter was initially developed as an experiment using ChatGPT, with subsequent
manual refinements and improvements.
