# Transaction Demos

These demos show how to group operations into atomic transactions.

## Basic Transaction

Group multiple operations that succeed or fail together.

```python
# --8<-- [start:basic-transaction]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Account(BaseDBModel):
    name: str
    balance: float

db = SqliterDB(memory=True)
db.create_table(Account)

alice: Account = db.insert(Account(name="Alice", balance=100.0))
bob: Account = db.insert(Account(name="Bob", balance=50.0))

print(f"Before: Alice=${alice.balance}, Bob=${bob.balance}")

# Transfer money using context manager
with db:
    alice.balance = alice.balance - 20.0
    bob.balance = bob.balance + 20.0
    db.update(alice)
    db.update(bob)
    alice_updated = alice
    bob_updated = bob

print(
    f"After: Alice=${alice_updated.balance}, Bob=${bob_updated.balance}"
)
print("Transaction auto-committed on success")

db.close()
# --8<-- [end:basic-transaction]
```

### What Happens

- Both updates succeed or both fail
- If an error occurs, all changes are rolled back
- Database remains in a consistent state

## Transaction Rollback

Automatically rollback on errors.

```python
# --8<-- [start:transaction-rollback]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Item(BaseDBModel):
    name: str
    quantity: int

db = SqliterDB(memory=True)
db.create_table(Item)

item: Item = db.insert(Item(name="Widget", quantity=10))
print(f"Initial quantity: {item.quantity}")

# Use context manager for automatic rollback on error
try:
    with db:
        item.quantity = 5
        db.update(item)
        print("Inside transaction: updated to 5")
        # If error occurs, changes are rolled back
        error_msg = "Intentional error for rollback"
        raise RuntimeError(error_msg)  # noqa: TRY301
except RuntimeError:
    print("Error occurred - transaction rolled back")
    print("Original value preserved (quantity=10)")

db.close()
# --8<-- [end:transaction-rollback]
```

!!! warning
    **Known Issue:** Transaction rollback is currently broken in SQLiter.
    The `update()`, `insert()`, and `delete()` methods use nested context
    managers that commit prematurely. This demo shows the expected behavior,
    but actual rollback may not work correctly until this is fixed.

### Rollback Behavior

- All changes within the transaction should be undone
- Database state should be as if nothing happened
- Exception continues to propagate unless caught

## Manual Transaction Control

Explicitly commit using the context manager or connect/commit methods.

```python
# --8<-- [start:manual-transaction]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Log(BaseDBModel):
    message: str

db = SqliterDB(memory=True)
db.create_table(Log)

# Manual transaction control
db.connect()
log1 = db.insert(Log(message="First entry"))
print(f"Inserted: {log1.message}")
print("Not committed yet")
db.commit()
print("Committed")

db.insert(Log(message="Second entry"))
db.commit()

all_logs = db.select(Log).fetch_all()
print(f"Total logs: {len(all_logs)}")

db.close()
# --8<-- [end:manual-transaction]
```

### When to Use

- **Complex logic**: Need conditional commit/rollback
- **Error handling**: Different rollback strategies
- **Nested operations**: Multiple validation steps

## Transaction Isolation

Transactions are isolated from other operations.

```python
# --8<-- [start:isolation]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Counter(BaseDBModel):
    value: int

db = SqliterDB(memory=True)
db.create_table(Counter)

counter = db.insert(Counter(value=0))

with db:
    # Increment counter
    counter.value += 1
    db.update(counter)

    # Value is 1 inside transaction
    print(f"Inside: {counter.value}")

# Value is still 1 after commit
reloaded = db.get(Counter, counter.pk)
if reloaded is not None:
    print(f"After commit: {reloaded.value}")
```

## Nested Transactions

SQLiter supports nested context manager usage.

```python
# --8<-- [start:nested]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Order(BaseDBModel):
    total: float

class Payment(BaseDBModel):
    amount: float

db = SqliterDB(memory=True)
db.create_table(Order)
db.create_table(Payment)

# Outer transaction
with db:
    order = db.insert(Order(total=100.0))

    # Inner context (part of same transaction)
    with db:
        payment = db.insert(Payment(amount=100.0))

    # Both are committed together
```

!!! note
    SQLite's nested contexts are part of the same transaction - the outermost context exit finalizes everything.

## Performance Considerations

### Bulk Operations with Transactions

```python
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    name: str

# ❌ SLOW: Each insert is its own transaction
for i in range(1000):
    db.insert(User(name=f"User {i}"))

# ✅ FAST: All inserts in one transaction
with db:
    for i in range(1000):
        db.insert(User(name=f"User {i}"))
```

### Performance Impact

- **Without transaction**: 1000 separate commits = slow
- **With transaction**: 1 commit for all records = 10-100x faster

## When to Use Transactions

### Always Use For

- **Related operations**: Multiple tables that must stay in sync
- **Financial data**: Money transfers must be atomic
- **Complex updates**: Changes that affect multiple records

### Optional For

- **Single operations**: One insert/update/delete
- **Independent records**: No relationship between operations
- **Non-critical data**: Temporary data, logs

### Never For

- **Long-running operations**: Transactions lock the database
- **Interactive operations**: Waiting for user input
- **Large bulk imports**: Consider periodic commits

## Common Patterns

### Transfer Pattern

```python
def transfer(db: SqliterDB, from_account: Account, to_account: Account, amount: float) -> None:
    """Transfer funds between accounts."""
    with db:
        from_account.balance -= amount
        to_account.balance += amount
        db.update(from_account)
        db.update(to_account)
```

### Create or Update Pattern

```python
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    name: str
    email: str

def create_or_update(db: SqliterDB, user: User) -> None:
    """Insert or update a user."""
    with db:
        existing = db.select(User).filter(
            email__eq=user.email
        ).fetch_one()

        if existing:
            existing.name = user.name
            db.update(existing)
        else:
            db.insert(user)
```

## Best Practices

### DO

- Use transactions for multistep operations
- Keep transactions short (don't hold locks)
- Use context managers for automatic cleanup
- Handle exceptions appropriately

### DON'T

- Forget that transactions lock the database
- Put user input inside transactions
- Use transactions for single operations (unnecessary overhead)
- Mix manual and automatic transaction control

## Related Documentation

- [CRUD Operations](crud.md) - Create, update, and delete records
- [Error Handling](errors.md) - Handle transaction errors
- [ORM Features](orm.md) - Work with related data in transactions
