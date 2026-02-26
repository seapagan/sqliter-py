# TODO

Items marked with :fire: are high priority.

## General Plans and Ideas

- add ability to inspect existing SQLite databases and generate Pydantic models
  dynamically, including CLI tool for schema dumping.
- add an `execute` method to the main class to allow executing arbitrary SQL
  queries, with clear behavior for direct use and for integration with query
  fetch methods such as `fetch_first()`.
- add a `rollback` method to the main class to allow manual rollbacks.
- Investigate a mypy plugin to type reverse relationship accessors (avoid
  casts for dynamically injected attributes).
- Medium-term typing direction: replace runtime-injected reverse accessors
  with explicit reverse relationship declarations in model classes so
  reverse-side usage is mypy-friendly without casts or TYPE_CHECKING hacks.
- Short-term typing upgrade for user code: improve library type hints for
  dynamic ORM relationship APIs (reverse FK descriptors, M2M managers, and
  prefetched relation result types) to reduce required casts in normal
  application code and tests.
- Registry lifetime: global registry can cause cross-talk when models are
  defined repeatedly in one process (e.g., tests). Current mitigation exists
  via `ModelRegistry.reset()` and snapshot/restore helpers; longer-term option:
  make registry per-DB instance.
- Consider renaming to `ForeignKeyField` / `ManyToManyField` and keeping
  `ForeignKey` / `ManyToMany` as backwards-compatible aliases.
- Consider adding full atomicity for M2M add/remove within existing
  transactions (use savepoints to avoid partial writes).
- add a migration system to allow updating the database schema without losing
  data.
- add more tests where 'auto_commit' is set to False to ensure that commit is
  not called automatically.
- :fire: perhaps add a `JSON` field type to allow storing JSON data in a field,
  and an `Object` field type to allow storing arbitrary Python objects? Perhaps
  a `Binary` field type to allow storing arbitrary binary data? (just uses the
  existing `bytes` mapping but more explicit)
- Consider performance optimizations for field validation:
  - Benchmark shows ~50% overhead for field assignments with validation
  - Potential solutions:
    - Add a "fast mode" configuration option
    - Create bulk update methods that temporarily disable validation
    - Optimize validation for specific field types
- on update, check if the model has actually changed before sending the update
  to the database. This will prevent unnecessary updates and leave the
  `updated_at` correct. However, this will always require a query to the
  database to check the current values and so in large batch updates this could
  have a considerable performance impact. Probably best to gate this behind a
  flag.
- Refactor filter condition handling to use one centralized builder path and
  keep validation/SQL assembly behavior in sync across code paths
  (issue #136).
- Support `ForeignKey(..., db_column=...)` consistently across ORM runtime
  CRUD/query paths (issue #138). Once closed, rewrite temporary custom-column
  regression tests (currently using setup workarounds) to use normal ORM
  insert/query flows end-to-end.

## Housekeeping

- Tidy up the test suite - remove any duplicates, sort them into logical files
  (many already are), try to reduce and centralize fixtures.

## Documentation

None.

## Potential Filter Additions

- **Range filter**
  - `__range`: For selecting values within a specific range

- **Date and time filters**
  - `__year`, `__month`, `__day`: For filtering date fields
  - `__date`: For filtering the date part of a datetime field

- **Regular expression filter**
  - `__regex`: For more complex string matching

- **Numeric operations**
  - `__abs`: Absolute value comparison

- **Boolean filters**
  - `__istrue`, `__isfalse`: Explicit boolean checks

- **List field operations**
  - `__contains_all`: Check if a list field contains all specified values
  - `__contains_any`: Check if a list field contains any of the specified values

- **Negation filter**
  - `__not`: General negation for other filters

- **Distinct filter**
  - `__distinct`: To get distinct values in a field
