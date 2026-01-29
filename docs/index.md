# SQLiter <!-- omit in toc -->

[![PyPI version](https://badge.fury.io/py/sqliter-py.svg?cache_bust=1)](https://badge.fury.io/py/sqliter-py)
&nbsp;
[![Test Suite](https://github.com/seapagan/sqliter-py/actions/workflows/testing.yml/badge.svg?cache_bust=1)](https://github.com/seapagan/sqliter-py/actions/workflows/testing.yml)&nbsp;
[![Linting](https://github.com/seapagan/sqliter-py/actions/workflows/linting.yml/badge.svg?cache_bust=1)](https://github.com/seapagan/sqliter-py/actions/workflows/linting.yml)&nbsp;
[![Type Checking](https://github.com/seapagan/sqliter-py/actions/workflows/mypy.yml/badge.svg?cache_bust=1)](https://github.com/seapagan/sqliter-py/actions/workflows/mypy.yml)&nbsp;
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/sqliter-py?cache_bust=1)

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

> [!CAUTION]
> This project is still in the early stages of development and is lacking some
> planned functionality. Please use with caution - Classes and methods may
> change until a stable release is made. I'll try to keep this to an absolute
> minimum and the releases and documentation will be very clear about any
> breaking changes.
>
> See the [TODO](todo/index.md) for planned features and improvements.

## Features

- Table creation based on Pydantic models
- Supports `date` and `datetime` fields.
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

## API Reference

For detailed documentation of every class, method, property, and
constant, see the [API Reference](api-reference/index.md).

## Interactive Demo

SQLiter includes an interactive terminal-based demo (TUI) that lets you explore all features hands-on without writing any code. Run the demo to see live code examples and their output:

```bash
# Install with the demo extra
uv add sqliter-py[demo]
# or
pip install sqliter-py[demo]

# Run the interactive demo
python -m sqliter.tui
```

The demo includes:

- **14 demo categories** covering all SQLiter features
- **Live code display** with syntax highlighting
- **One-click execution** to see results in real-time
- **Organized tutorials** from basic to advanced topics

For more information, see the [Interactive Demo](tui-demo/index.md) documentation.

## License

This project is licensed under the terms of the [MIT license](license.md).
