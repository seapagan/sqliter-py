# SQLiter <!-- omit in toc -->

[![PyPI version](https://badge.fury.io/py/sqliter-py.svg)](https://badge.fury.io/py/sqliter-py)
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

Full documentation is available on the [Website](https://sqliter.grantramsay.dev)

> [!CAUTION]
>
> This project is still in the early stages of development and is lacking some
> planned functionality. Please use with caution - Classes and methods may
> change until a stable release is made. I'll try to keep this to an absolute
> minimum and the releases and documentation will be very clear about any
> breaking changes.
>
> See the [TODO](TODO.md) for planned features and improvements.

- [Features](#features)
- [Installation](#installation)
  - [Optional Dependencies](#optional-dependencies)
- [Quick Start](#quick-start)
- [Contributing](#contributing)
- [License](#license)

## Features

- Table creation based on Pydantic models
- Supports `date` and `datetime` fields
- Support for complex data types (`list`, `dict`, `set`, `tuple`) stored as
  BLOBs
- Foreign key relationships with referential integrity and CASCADE actions
- Automatic primary key generation
- User defined indexes on any field
- Set any field as UNIQUE
- CRUD operations (Create, Read, Update, Delete)
- Chained Query building with filtering, ordering, and pagination
- Transaction support
- Optional query result caching with LRU eviction, TTL, and memory limits
- Custom exceptions for better error handling
- Full type hinting and type checking
- Detailed documentation and examples
- Interactive TUI demo for exploring features
- No external dependencies other than Pydantic
- Full test coverage
- Can optionally output the raw SQL queries being executed for debugging
  purposes.

## Installation

You can install SQLiter using whichever method you prefer or is compatible with
your project setup.

With `uv` which is rapidly becoming my favorite tool for managing projects and
virtual environments (`uv` is used for developing this project and in the CI):

```bash
uv add sqliter-py
```

With `Poetry`:

```bash
poetry add sqliter-py
```

Or with `pip`:

```bash
pip install sqliter-py
```

### Optional Dependencies

Currently by default, the only external dependency is Pydantic. However, there
are some optional dependencies that can be installed to enable additional
features:

- `demo`: Installs the Textual TUI framework for the interactive demo
- `extras`: Installs Inflect for better pluralization of table names
- `full`: Installs all optional dependencies (Textual and Inflect)

See [Installing Optional
Dependencies](https://sqliter.grantramsay.dev/installation#optional-dependencies)
for more information.

## Quick Start

Here's a quick example of how to use SQLiter:

```python
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

# Define your model
class User(BaseDBModel):
    name: str
    age: int

# Create a database connection
db = SqliterDB("example.db")

# Create the table
db.create_table(User)

# Insert a record
user = User(name="John Doe", age=30)
new_user = db.insert(user)

# Query records
results = db.select(User).filter(name="John Doe").fetch_all()
for user in results:
    print(f"User: {user.name}, Age: {user.age}")

# Update a record
new_user.age = 31
db.update(new_user)

# Delete a record by primary key
db.delete(User, new_user.pk)

# Delete all records returned from a query:
delete_count = db.select(User).filter(age__gt=30).delete()
```

See the [Guide](https://sqliter.grantramsay.dev/guide/guide/) section of the
documentation for more detailed information on how to use SQLiter, and advanced
features.

You can also run the interactive TUI demo to explore SQLiter features hands-on:

```bash
# Install the demo
uv add sqliter-py[demo]

# Run the demo
sqliter-demo
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

See the [CONTRIBUTING](CONTRIBUTING.md) guide for more information.

Please note that this project is released with a Contributor Code of Conduct,
which you can read in the [CODE_OF_CONDUCT](CODE_OF_CONDUCT.md) file.

## License

This project is licensed under the MIT License.

```pre
Copyright (c) 2024-2026 Grant Ramsay

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
```
