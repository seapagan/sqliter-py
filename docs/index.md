# SQLiter <!-- omit in toc -->

[![PyPI version](https://badge.fury.io/py/sqliter-py.svg)](https://badge.fury.io/py/sqliter-py)
&nbsp;
[![Test Suite](https://github.com/seapagan/sqliter-py/actions/workflows/testing.yml/badge.svg)](https://github.com/seapagan/sqliter-py/actions/workflows/testing.yml)&nbsp;
[![Linting](https://github.com/seapagan/sqliter-py/actions/workflows/linting.yml/badge.svg)](https://github.com/seapagan/sqliter-py/actions/workflows/linting.yml)&nbsp;
[![Type Checking](https://github.com/seapagan/sqliter-py/actions/workflows/mypy.yml/badge.svg)](https://github.com/seapagan/sqliter-py/actions/workflows/mypy.yml)&nbsp;
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

> [!CAUTION]
> This project is still in the early stages of development and is lacking some
> planned functionality. Please use with caution.
>
> Also, structures like `list`, `dict`, `set` etc are not supported **at this
> time** as field types, since SQLite does not have a native column type for
> these. This is the **next planned enhancement**. These will need to be
> `pickled` first then stored as a BLOB in the database . Also support `date`
> which can be stored as a Unix timestamp in an integer field.
>
> See the [TODO](todo/index.md) for planned features and improvements.

## Features

- Table creation based on Pydantic models
- CRUD operations (Create, Read, Update, Delete)
- Basic query building with filtering, ordering, and pagination
- Transaction support
- Custom exceptions for better error handling
- Full type hinting and type checking
- Detailed documentation and examples
- No external dependencies other than Pydantic
- Full test coverage
- Can optionally output the raw SQL queries being executed for debugging
  purposes.

## License

This project is licensed under the terms of the [MIT license](license.md).