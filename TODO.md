# TODO

- make `auto_commit` default to `True` instead of false. Provide a `commit`
  method off the main class to allow manual commits.
- add a `rollback` method to the main class to allow manual rollbacks.
- add a `close` method to the main class to allow closing the connection.
- allow 'Select' to return a custom set of fields instead of all fields.
- allow adding multiple indexes to each table as well as the primary index.
- allow adding foreign keys and relationships to each table.
- add a migration system to allow updating the database schema without losing
  data.
- add support for more data types, though since it is using Pydantic it should
  be quite comprehensive already.
- add debug logging to show the SQL queries being executed.
