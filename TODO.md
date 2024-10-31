# TODO

Items marked with :fire: are high priority.

## General Plans and Ideas

- add an 'execute' method to the main class to allow executing arbitrary SQL
  queries which can be chained to the 'find_first' etc methods or just used
  directly.
- add a `delete` method to the QueryBuilder class to allow deleting
  single/multiple records from the database based on the query. This is in
  addition to the `delete` method in the main class which deletes a single
  record based on the primary key.
- add a `rollback` method to the main class to allow manual rollbacks.
- :fire: allow adding foreign keys and relationships to each table.
- add a migration system to allow updating the database schema without losing
  data.
- add more tests where 'auto_commit' is set to False to ensure that commit is
  not called automatically.
- :fire: support structures like, `list`, `dict`, `set`, `tuple` etc. in the
  model. These will need to be `pickled` first then stored as a BLOB in the
  database
- :fire: similarly - perhaps add a `JSON` field type to allow storing JSON data
  in a field, and an `Object` field type to allow storing arbitrary Python
  objects? Perhaps a `Binary` field type to allow storing arbitrary binary data?
  (just uses the existing `bytes` mapping but more explicit)
- on update, check if the model has actually changed before sending the update
  to the database. This will prevent unnecessary updates and leave the
  `updated_at` correct. However, this will always require a query to the
  database to check the current values and so in large batch updates this could
  have a considerable performance impact. Probably best to gate this behind a
  flag.

## Housekeeping

- Tidy up the test suite - remove any duplicates, sort them into logical files
  (many already are), try to reduce and centralize fixtures.

## Documentation

- Nothing at the moment.

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
