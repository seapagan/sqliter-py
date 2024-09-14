# TODO

- add an 'exists_ok' (default True) parameter to the 'create_table' method so it
  will raise an exception if the table already exists and this is set to False.
- add a `rollback` method to the main class to allow manual rollbacks.
- allow 'Select' to return a custom set of fields instead of all fields.
- allow adding multiple indexes to each table as well as the primary index.
- allow adding foreign keys and relationships to each table.
- add a migration system to allow updating the database schema without losing
  data.
- add support for more data types, though since it is using Pydantic it should
  be quite comprehensive already.
- add debug logging to show the SQL queries being executed.
- add more tests where 'auto_commit' is set to False to ensure that commit is
  not called automatically.

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
