# Error Handling Demos

These demos show how to handle errors that occur when working with SQLiter.

## Duplicate Record Error

Handle unique constraint violations.

```python
# --8<-- [start:duplicate-record]
from typing import Annotated
from sqliter import SqliterDB
from sqliter.model import BaseDBModel
from sqliter.model.unique import unique
from sqliter.exceptions import RecordInsertionError

class User(BaseDBModel):
    email: Annotated[str, unique()]
    name: str

db = SqliterDB(memory=True)
db.create_table(User)

db.insert(User(email="alice@example.com", name="Alice"))
print("Created user with email alice@example.com")

try:
    # Try to insert duplicate email
    db.insert(User(email="alice@example.com", name="Alice 2"))
except RecordInsertionError as e:
    print(f"\nCaught error: {type(e).__name__}")
    print(f"Message: {e}")

db.close()
# --8<-- [end:duplicate-record]
```

### Prevention

Check if record exists before inserting:

```python
existing = db.select(User).filter(email__eq="alice@example.com").fetch_one()
if not existing:
    db.insert(User(name="Alice", email="alice@example.com"))
```

## Record Not Found

Handle missing records gracefully.

```python
# --8<-- [start:not-found]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel
from sqliter.exceptions import RecordNotFoundError

class User(BaseDBModel):
    name: str

db = SqliterDB(memory=True)
db.create_table(User)

user = db.insert(User(name="Alice"))
print(f"Created user with pk={user.pk}")

try:
    # Try to delete non-existent record (raises RecordNotFoundError)
    db.delete(User, 9999)
except RecordNotFoundError as e:
    print(f"\nCaught error: {type(e).__name__}")
    print(f"Message: {e}")

db.close()
# --8<-- [end:not-found]
```

### Alternative Using Queries

Use `fetch_one()` which returns `None` instead of raising:

```python
user = db.select(User).filter(name__eq="Alice").fetch_one()
if user is None:
    print("User not found")
else:
    print(f"Found: {user.name}")
```

## Validation Errors

Pydantic validates data before it reaches the database, ensuring type safety and data integrity.

```python
# --8<-- [start:validation-error]
from pydantic import ValidationError

from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Product(BaseDBModel):
    name: str
    price: float
    quantity: int

db = SqliterDB(memory=True)
db.create_table(Product)

product = db.insert(Product(name="Widget", price=19.99, quantity=100))
print(f"Created product: {product.name}, price: ${product.price}")

# Try to create product with invalid data (wrong types)
print("\nAttempting to create product with invalid data...")

try:
    # Wrong types: price should be float, quantity should be int
    invalid_product = Product(name="Invalid Widget", price="free", quantity="lots")
    db.insert(invalid_product)
except ValidationError as e:
    print(f"\nCaught error: {type(e).__name__}")
    print(f"Message: {e}")

db.close()
# --8<-- [end:validation-error]
```

### Benefits

- **Data never reaches the database in invalid form** - Validation happens before insert
- **Clear error messages** - Pydantic tells you exactly what's wrong
- **Type safety** - Catch type mismatches at model instantiation, not at database insert
- **Automatic** - No manual validation code needed, Pydantic handles it

## Generic Error Handling

Catch all SQLiter errors with the base `SqliterError` class when you don't need to distinguish between specific error types.

```python
# --8<-- [start:generic-error]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel
from sqliter.exceptions import SqliterError

class Task(BaseDBModel):
    title: str

db = SqliterDB(memory=True)
db.create_table(Task)

task = db.insert(Task(title="My Task"))
print(f"Created task: {task.title}")

# Try to update a deleted record
try:
    task.title = "Updated"
    db.delete(Task, task.pk)
    db.update(task)  # This will fail
except SqliterError as e:
    print(f"\nCaught SqliterError: {type(e).__name__}")
    print(f"Message: {e}")

db.close()
# --8<-- [end:generic-error]
```

### When to Use Generic Error Handling

- **Simplified error handling**: When you don't need to take different actions based on error type
- **Logging or reporting**: When you just need to log that an error occurred
- **Top-level error handlers**: When you want to catch any SQLiter error at the application boundary

### Specific vs Generic

```python
# Specific - handle different error types differently
try:
    db.insert(user)
except RecordInsertionError:
    print("Duplicate user")
except ValidationError as e:
    print(f"Invalid data: {e}")

# Generic - catch all SQLiter errors
try:
    db.insert(user)
except SqliterError as e:
    print(f"Database error: {e}")
```

## Database Connection Errors

Handle connection failures.

```python
# --8<-- [start:connection-error]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    name: str

try:
    # Try to connect to non-existent directory
    db = SqliterDB(database="/invalid/path/db.sqlite")
    db.create_table(User)
except (OSError, IOError) as e:
    print(f"Connection failed: {e}")
```

### Common Causes

- Invalid directory (doesn't exist)
- Permission denied (can't write to directory)
- Database file corrupted

## Table Creation

Always create tables before using them.

```python
# --8<-- [start:table-not-found]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    name: str

db = SqliterDB(memory=True)

# Always create tables first
db.create_table(User)

# Now inserts will work
db.insert(User(name="Alice"))
```

### Prevention

Always call `create_table()` before inserting:

```python
db.create_table(User)  # Safe if called multiple times
db.insert(User(name="Alice"))
```

## Foreign Key Constraint Errors

Handle foreign key violations.

```python
# --8<-- [start:foreign-key-error]
from sqliter import SqliterDB
from sqliter.orm import BaseDBModel, ForeignKey
from sqliter.exceptions import ForeignKeyConstraintError

class Author(BaseDBModel):
    name: str

class Book(BaseDBModel):
    title: str
    author: ForeignKey[Author] = ForeignKey(Author, on_delete="RESTRICT")

db = SqliterDB(memory=True)
db.create_table(Author)
db.create_table(Book)

author = db.insert(Author(name="Jane"))
db.insert(Book(title="Book 1", author=author))
print("Created author and linked book")

# Attempt to insert book with non-existent author
print("\nAttempting to insert book with non-existent author...")

try:
    # Create book with invalid author_id (doesn't exist in database)
    invalid_book = Book(title="Orphan Book", author_id=9999)
    db.insert(invalid_book)
except ForeignKeyConstraintError as e:
    print(f"\nCaught error: {type(e).__name__}")
    print(f"Message: {e}")

db.close()
# --8<-- [end:foreign-key-error]
```

### Prevention

Ensure parent record exists:

```python
author = db.insert(Author(name="Jane Austen"))
db.insert(Book(title="Pride and Prejudice", author=author))
```

## Transaction Errors

Handle errors during transactions.

```python
# --8<-- [start:transaction-error]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Account(BaseDBModel):
    balance: float

db = SqliterDB(memory=True)
db.create_table(Account)

account = db.insert(Account(balance=100.0))

try:
    with db:
        account.balance -= 200.0  # Would go negative
        db.update(account)
        raise ValueError("Invalid operation")
except ValueError as e:
    print(f"Transaction failed: {e}")
    # Note: Changes are NOT rolled back due to bug (issue #104)

# Verify balance unchanged
reloaded = db.get(Account, account.pk)
if reloaded is not None:
    print(f"Balance: {reloaded.balance}")  # Was 100.0
```

## Error Handling Best Practices

### Specific Exceptions

Catch specific exceptions for different error types:

```python
from pydantic import ValidationError
from sqliter.exceptions import (
    RecordInsertionError,
    RecordNotFoundError,
    ForeignKeyConstraintError,
    SqliterError,
)

try:
    db.insert(user)
except RecordInsertionError:
    print("Duplicate record or constraint violation")
except ValidationError as e:
    print(f"Invalid data: {e}")
except SqliterError as e:
    print(f"Database error: {e}")
```

### User-Friendly Messages

Translate technical errors for users:

```python
from typing import Annotated

from sqliter.model import BaseDBModel
from sqliter.model.unique import unique
from sqliter.exceptions import RecordInsertionError

class User(BaseDBModel):
    username: Annotated[str, unique()]

try:
    db.insert(User(username="alice"))
except RecordInsertionError:
    print("Username already taken, please choose another")
```

### Logging

Log errors for debugging:

```python
import logging

from sqliter.model import BaseDBModel
from sqliter.exceptions import RecordInsertionError

logger = logging.getLogger(__name__)

class User(BaseDBModel):
    username: str

try:
    db.insert(User(username="alice"))
except RecordInsertionError as e:
    logger.error(f"Failed to create user: {e}")
    raise  # Re-raise for user-facing error
```

## Exception Hierarchy

```text
Exception
├── SqliterError
│   ├── RecordNotFoundError
│   ├── RecordInsertionError
│   ├── RecordUpdateError
│   ├── RecordDeletionError
│   └── ForeignKeyConstraintError
└── ValidationError (from Pydantic)
```

## Best Practices

### DO

- Catch specific exceptions for different error types
- Provide user-friendly error messages
- Log errors for debugging
- Validate data before database operations
- Use transactions for multi-step operations

### DON'T

- Catch all exceptions with bare `except:`
- Ignore errors silently
- Expose raw database errors to users
- Forget that validation errors prevent database writes

## Related Documentation

- [Constraints](constraints.md) - Define database constraints
- [Transactions](transactions.md) - Handle errors in transactions
- [CRUD Operations](crud.md) - Common operations and their errors
