# TODO

- make `auto_commit` default to `True` instead of false. Provide a `commit`
  method off the main class to allow manual commits.
- allow adding multiple indexes to each table as well as the primary index.
- allow adding foreign keys and relationships to each table.
- improve the filter and query syntax to allow more complex queries - for
  example, `age__lt=25` to filter users with age less than 25.
- add a migration system to allow updating the database schema without losing
  data.
- add support for more data types, though since it is using Pydantic it should
  be quite comprehensive already.
