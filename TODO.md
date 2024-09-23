# TODO

- BREAKING: change the 'create_id' meta field to 'create_pk' as it may not be
  called 'id' in the model.
- add an option to the SQLiter constructor to delete the database file if it
  already exists. Default to False.
- add attributes to the BaseDBModel to read the table-name, file-name, is-memory
  etc.
- deprectate 'direction=' in the 'order' method and replace with 'reverse=' with
  a default of False. Leave the 'direction=' parameter in place for now but
  raise a deprecation warning if it is used.
- add an 'execute' method to the main class to allow executing arbitrary SQL
  queries which can be chained to the 'find_first' etc methods or just used
  directly.
- add a 'drop_table' method to the main class to allow dropping tables.
- add a method to drop the entire database easiest way is prob to just delete
  and recreate the database file.
- add an 'exists_ok' (default True) parameter to the 'create_table' method so it
  will raise an exception if the table already exists and this is set to False.
- add a `rollback` method to the main class to allow manual rollbacks.
- allow adding multiple indexes to each table as well as the primary index.
- allow adding foreign keys and relationships to each table.
- add a migration system to allow updating the database schema without losing
  data.
- add support for more data types, though since it is using Pydantic it should
  be quite comprehensive already.
- add debug logging to show the SQL queries being executed.
- add more tests where 'auto_commit' is set to False to ensure that commit is
  not called automatically.
- add a documentation website.
- the database is created with every field as TEXT. We should try to infer the
  correct type from the Pydantic model and map it to the correct SQLite type.
  The return model is created using the pydantic model, so these are converted
  correctly anyway, but it would be nice to have the database schema match the
  model schema.
- update the auto table_name generation to convert to snake_case, and remove the
  'Model' suffix if present.
- support structures like, `list`, `dict`, `set` etc. in the model. This
  will need to be stored as a JSON string or pickled in the database. Also
  support `date` which can be either stored as a string or more useful as a Unix
  timestamp in an integer field.

## Potential Filter Additions

1. **Range filter**
   - `__range`: For selecting values within a specific range

2. **Date and time filters**
   - `__year`, `__month`, `__day`: For filtering date fields
   - `__date`: For filtering the date part of a datetime field

3. **Regular expression filter**
   - `__regex`: For more complex string matching

4. **Numeric operations**
   - `__abs`: Absolute value comparison

5. **Boolean filters**
   - `__istrue`, `__isfalse`: Explicit boolean checks

6. **List field operations**
   - `__contains_all`: Check if a list field contains all specified values
   - `__contains_any`: Check if a list field contains any of the specified values

7. **Negation filter**
   - `__not`: General negation for other filters

8. **Distinct filter**
    - `__distinct`: To get distinct values in a field
