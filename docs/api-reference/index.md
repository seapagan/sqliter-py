# API Reference

This section provides detailed documentation for every public class,
method, property, function, and constant in the SQLiter library. Each
entry includes the full signature, parameter descriptions, return
types, and usage examples.

> [!TIP]
> If you are new to SQLiter, start with the [Guide](../guide/guide.md)
> for a tutorial-style introduction. This API Reference is intended as a
> comprehensive lookup resource.

## Module Overview

| Module               | Import                                  | Description                              |
| -------------------- | --------------------------------------- | ---------------------------------------- |
| `sqliter`            | `from sqliter import SqliterDB`         | Main database class                      |
| `sqliter.model`      | `from sqliter.model import BaseDBModel` | Base model (legacy mode)                 |
| `sqliter.model`      | `from sqliter.model import unique`      | Unique constraint helper                 |
| `sqliter.model`      | `from sqliter.model import ForeignKey`  | Foreign key factory (legacy mode)        |
| `sqliter.orm`        | `from sqliter.orm import BaseDBModel`   | Base model (ORM mode)                    |
| `sqliter.orm`        | `from sqliter.orm import ForeignKey`    | Foreign key descriptor (ORM mode)        |
| `sqliter.orm`        | `from sqliter.orm import ModelRegistry` | Model registry                           |
| `sqliter.query`      | *(internal)*                            | QueryBuilder (returned by `db.select()`) |
| `sqliter.exceptions` | `from sqliter.exceptions import ...`    | Exception hierarchy                      |
| `sqliter.helpers`    | *(internal)*                            | Utility functions                        |
| `sqliter.constants`  | *(internal)*                            | Constant mappings                        |

> [!NOTE]
> The **ORM module** (`sqliter.orm`) is an alternative import mode that
> extends the legacy `sqliter.model` with lazy loading and reverse
> relationships. See [ORM Mode](orm.md) for details.

## Pages

- **[SqliterDB](sqliterdb.md)** -- Main entry point for all database
  operations: connections, tables, CRUD, caching, and transactions.

- **[BaseDBModel](base-model.md)** -- Pydantic-based base class for
  defining database models, plus the `unique()` constraint helper.

- **[QueryBuilder](query-builder.md)** -- Fluent API for filtering,
  ordering, paginating, and executing queries.

- **[Foreign Keys](foreign-keys.md)** -- `ForeignKey()` factory
  function, `ForeignKeyInfo` dataclass, and `FKAction` type alias
  (legacy mode).

- **[ORM Mode](orm.md)** -- Extended `BaseDBModel` with lazy loading,
  `ForeignKey` descriptor, `LazyLoader`, `ModelRegistry`,
  `ReverseQuery`, and `ReverseRelationship`.

- **[Exceptions](exceptions.md)** -- Full hierarchy of 17 exception
  classes with message templates and usage context.

- **[Helpers & Constants](helpers.md)** -- Internal utility functions
  and constant mappings used by the library.
