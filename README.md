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

Full documentation is available on the [Documentation
Website](https://sqliter.grantramsay.dev)

> [!CAUTION]
> This project is still in the early stages of development and is lacking some
> planned functionality. Please use with caution - Classes and methods may
> change until a stable release is made. I'll try to keep this to an absolute
> minimum and the releases and documentation will be very clear about any
> breaking changes.
>
> Also, structures like `list`, `dict`, `set` etc are not supported **at this
> time** as field types, since SQLite does not have a native column type for
> these. This is the **next planned enhancement**. These will need to be
> `pickled` first then stored as a BLOB in the database . Also support `date`
> which can be stored as a Unix timestamp in an integer field.
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
- Automatic primary key generation
- User defined indexes on any field
- Set any field as UNIQUE
- CRUD operations (Create, Read, Update, Delete)
- Chained Query building with filtering, ordering, and pagination
- Transaction support
- Custom exceptions for better error handling
- Full type hinting and type checking
- Detailed documentation and examples
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

- `inflect`: For pluralizing the auto-generated table names (if not explicitly
  set in the Model) This just offers a more-advanced pluralization than the
  default method used. In most cases you will not need this.

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

# Delete a record
db.delete(User, new_user.pk)
```

See the [Usage](https://sqliter.grantramsay.dev/usage) section of the documentation
for more detailed information on how to use SQLiter, and advanced features.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

See the [CONTRIBUTING](CONTRIBUTING.md) guide for more information.

Please note that this project is released with a Contributor Code of Conduct,
which you can read in the [CODE_OF_CONDUCT](CODE_OF_CONDUCT.md) file.

## License

This project is licensed under the MIT License.

```pre
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
```
