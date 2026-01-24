# Error Handling Demos

These demos show how to handle errors that occur when working with SQLiter.

## Duplicate Record Error

Handle unique constraint violations.

```python
# --8<-- [start:duplicate-record]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel, unique
from sqliter.exceptions import IntegrityError

class User(BaseDBModel):
    """User with unique username."""
    username: unique(str)

db = SqliterDB(memory=True)
db.create_table(User)

# Insert first user
db.insert(User(username="alice"))

# Try to insert duplicate username
try:
    db.insert(User(username="alice"))
except IntegrityError as e:
    print(f"Error: Username already exists: {e}")
```

### Prevention
Check if record exists before inserting:

```python
existing = db.select(User).filter(username="alice").fetch_one()
if not existing:
    db.insert(User(username="alice"))
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

# Try to get non-existent record
try:
    user = db.get_by_pk(User, pk=999)
except RecordNotFoundError as e:
    print(f"Error: {e}")
```

### Safe Alternative
Use `fetch_one()` which returns `None` instead of raising:

```python
user = db.select(User).filter(name="Alice").fetch_one()
if user is None:
    print("User not found")
else:
    print(f"Found: {user.name}")
```

## Validation Errors

Pydantic validates data before database insert.

```python
# --8<-- [start:validation-error]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel
from pydantic import ValidationError

class Product(BaseDBModel):
    """Product with price validation."""
    name: str
    price: float

    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("Price must be positive")
        return value

db = SqliterDB(memory=True)
db.create_table(Product)

# Try to insert invalid product
try:
    db.insert(Product(name="Free Widget", price=-10.0))
except ValidationError as e:
    print(f"Validation error: {e}")
```

### Benefits
- Data never reaches the database in invalid form
- Clear error messages
- Type checking and validation

## Database Connection Errors

Handle connection failures.

```python
# --8<-- [start:connection-error]
from sqliter import SqliterDB
from sqliter.exceptions import DatabaseConnectionError

try:
    # Try to connect to non-existent directory
    db = SqliterDB(database="/invalid/path/db.sqlite")
    db.create_table(User)
except DatabaseConnectionError as e:
    print(f"Connection failed: {e}")
```

### Common Causes
- Invalid directory (doesn't exist)
- Permission denied (can't write to directory)
- Database file corrupted

## Table Not Found Error

Handle missing table errors.

```python
# --8<-- [start:table-not-found]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel
from sqliter.exceptions import TableNotFoundError

class User(BaseDBModel):
    name: str

db = SqliterDB(memory=True)

# Try to insert without creating table
try:
    db.insert(User(name="Alice"))
except TableNotFoundError as e:
    print(f"Error: {e}")
    # Create the table
    db.create_table(User)
    # Try again
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
from sqliter.model import BaseDBModel, ForeignKey
from sqliter.exceptions import IntegrityError

class Author(BaseDBModel):
    name: str

class Book(BaseDBModel):
    title: str
    author: ForeignKey[Author]

db = SqliterDB(memory=True)
db.create_table(Author)
db.create_table(Book)

# Try to insert book with non-existent author
try:
    db.insert(Book(title="Orphan Book", author=999))
except IntegrityError as e:
    print(f"Foreign key error: {e}")
```

### Prevention
Ensure parent record exists:

```python
author = db.insert(Author(name="Jane Austen"))
db.insert(Book(title="Pride and Prejudice", author=author.pk))
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
    with db.transaction():
        account.balance -= 200.0  # Would go negative
        db.update(account)
        raise ValueError("Invalid operation")
except ValueError as e:
    print(f"Transaction failed: {e}")
    # Changes are automatically rolled back

# Verify balance unchanged
reloaded = db.get_by_pk(Account, account.pk)
print(f"Balance: {reloaded.balance}")  # Still 100.0
```

## Error Handling Best Practices

### Specific Exceptions
Catch specific exceptions for different error types:

```python
from sqliter.exceptions import (
    IntegrityError,
    RecordNotFoundError,
    TableNotFoundError,
    ValidationError,
)

try:
    db.insert(user)
except IntegrityError:
    print("Duplicate record")
except ValidationError as e:
    print(f"Invalid data: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### User-Friendly Messages
Translate technical errors for users:

```python
try:
    db.insert(User(username="alice"))
except IntegrityError:
    print("Username already taken, please choose another")
```

### Logging
Log errors for debugging:

```python
import logging

logger = logging.getLogger(__name__)

try:
    db.insert(User(username="alice"))
except IntegrityError as e:
    logger.error(f"Failed to create user: {e}")
    raise  # Re-raise for user-facing error
```

## Exception Hierarchy

```
Exception
├── SQLiterError
│   ├── DatabaseConnectionError
│   ├── TableNotFoundError
│   ├── RecordNotFoundError
│   └── IntegrityError
└── ValidationError (from Pydantic)
```

## Best Practices

### DO:
- Catch specific exceptions for different error types
- Provide user-friendly error messages
- Log errors for debugging
- Validate data before database operations
- Use transactions for multi-step operations

### DON'T:
- Catch all exceptions with bare `except:`
- Ignore errors silently
- Expose raw database errors to users
- Forget that validation errors prevent database writes

## Related Documentation

- [Constraints](constraints.md) - Define database constraints
- [Transactions](transactions.md) - Handle errors in transactions
- [CRUD Operations](crud.md) - Common operations and their errors
