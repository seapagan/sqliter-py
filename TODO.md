# TODO

## General Plans and Ideas

- add an option to the SQLiter constructor to delete the database file if it
  already exists. Default to False.
- add attributes to the BaseDBModel to read the table-name, file-name, is-memory
  etc.
- add an 'execute' method to the main class to allow executing arbitrary SQL
  queries which can be chained to the 'find_first' etc methods or just used
  directly.
- add a 'drop_table' method to the main class to allow dropping tables.
- add a method to drop the entire database easiest way is prob to just delete
  and recreate the database file.
- add an 'exists_ok' (default True) parameter to the 'create_table' method so it
  will raise an exception if the table already exists and this is set to False.
- add a `rollback` method to the main class to allow manual rollbacks.
- allow adding multiple indexes to each table as well as the primary key.
- allow adding foreign keys and relationships to each table.
- add a migration system to allow updating the database schema without losing
  data.
- add debug logging to show the SQL queries being executed.
- add more tests where 'auto_commit' is set to False to ensure that commit is
  not called automatically.
- the database is created with every field as TEXT. We should try to infer the
  correct type from the Pydantic model and map it to the correct SQLite type.
  The return model is created using the pydantic model, so these are converted
  correctly anyway, but it would be nice to have the database schema match the
  model schema.
- support structures like, `list`, `dict`, `set` etc. in the model. This will
  need to be stored as a JSON string or pickled in the database (the latter
  would be more versatile). Also support `date` which can be either stored as a
  string or more useful as a Unix timestamp in an integer field.
- for the `order()` allow ommitting the field name and just specifying the
  direction. This will default to the primary key field.

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
