# Exceptions

SQLiter includes several custom exceptions to handle specific errors that may
occur during database operations. These exceptions inherit from a common base
class, `SqliterError`, to ensure consistency across error messages and behavior.

- **`SqliterError`**:
  - The base class for all exceptions in SQLiter. It captures the exception
    context and chains any previous exceptions.
  - **Message**: "An error occurred in the SQLiter package."

- **`DatabaseConnectionError`**:
  - **Raised** when the SQLite database connection fails.
  - **Message**: "Failed to connect to the database: '{}'."

- **`InvalidOffsetError`**:
  - **Raised** when an invalid offset value (0 or negative) is used in queries.
  - **Message**: "Invalid offset value: '{}'. Offset must be a positive
    integer."

- **`InvalidOrderError`**:
  - **Raised** when an invalid order value is used in queries, such as a
    non-existent field or an incorrect sorting direction.
  - **Message**: "Invalid order value - '{}'"

- **`TableCreationError`**:
  - **Raised** when a table cannot be created in the database.
  - **Message**: "Failed to create the table: '{}'."

- **`RecordInsertionError`**:
  - **Raised** when an error occurs during record insertion.
  - **Message**: "Failed to insert record into table: '{}'."

- **`RecordUpdateError`**:
  - **Raised** when an error occurs during record update.
  - **Message**: "Failed to update record in table: '{}'."

- **`RecordNotFoundError`**:
  - **Raised** when a record with the specified primary key is not found.
  - **Message**: "Failed to find a record for key '{}'".

- **`RecordFetchError`**:
  - **Raised** when an error occurs while fetching records from the database.
  - **Message**: "Failed to fetch record from table: '{}'."

- **`RecordDeletionError`**:
  - **Raised** when an error occurs during record deletion.
  - **Message**: "Failed to delete record from table: '{}'."

- **`InvalidFilterError`**:
  - **Raised** when an invalid filter field is used in a query.
  - **Message**: "Failed to apply filter: invalid field '{}'".

- **`TableDeletionError`**:
  - **Raised** when a table cannot be deleted from the database.
  - **Message**: "Failed to delete the table: '{}'."

- **SqlExecutionError**
  - **Raised** when an error occurs during SQL query execution.
  - **Message**: "Failed to execute SQL: '{}'."

- **InvalidIndexError**
  - **Raised** when an invalid index is specified for a model.
  - **Message**: "Invalid fields for indexing in model '{}': {}"
