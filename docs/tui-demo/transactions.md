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

# Create two accounts
account1 = db.insert(Account(name="Alice", balance=100.0))
account2 = db.insert(Account(name="Bob", balance=50.0))

# Transfer funds using a transaction
with db.transaction():
    account1.balance -= 10.0
    db.update(account1)

    account2.balance += 10.0
    db.update(account2)
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

class Account(BaseDBModel):
    name: str
    balance: float

db = SqliterDB(memory=True)
db.create_table(Account)

account1 = db.insert(Account(name="Alice", balance=100.0))

try:
    with db.transaction():
        account1.balance -= 200.0  # Would make balance negative
        db.update(account1)
        # Some validation that raises an error
        if account1.balance < 0:
            raise ValueError("Insufficient funds")
except ValueError:
    print("Transaction failed, changes rolled back")

# Verify balance is unchanged
reloaded = db.get_by_pk(Account, account1.pk)
print(f"Balance: {reloaded.balance}")  # Still 100.0
```

### Rollback Behavior

- All changes within the transaction are undone
- Database state is as if nothing happened
- Exception continues to propagate unless caught

## Manual Transaction Control

Explicitly commit or rollback.

```python
# --8<-- [start:manual-transaction]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Task(BaseDBModel):
    title: str

db = SqliterDB(memory=True)
db.create_table(Task)

# Start transaction
db.begin_transaction()

try:
    db.insert(Task(title="Task 1"))
    db.insert(Task(title="Task 2"))

    # Commit if successful
    db.commit()
except Exception:
    # Rollback on error
    db.rollback()
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

with db.transaction():
    # Increment counter
    counter.value += 1
    db.update(counter)

    # Value is 1 inside transaction
    print(f"Inside: {counter.value}")

# Value is still 1 after commit
reloaded = db.get_by_pk(Counter, counter.pk)
print(f"After commit: {reloaded.value}")
```

## Nested Transactions

SQLiter supports nested transaction contexts.

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
with db.transaction():
    order = db.insert(Order(total=100.0))

    # Inner transaction (conceptually part of outer)
    with db.transaction():
        payment = db.insert(Payment(amount=100.0))

    # Both are committed together
```

!!! note
    SQLite's nested transactions are actually savepoints - the outermost `commit()` finalizes everything.

## Performance Considerations

### Bulk Operations with Transactions

```python
# ❌ SLOW: Each insert is its own transaction
for i in range(1000):
    db.insert(User(name=f"User {i}"))

# ✅ FAST: All inserts in one transaction
with db.transaction():
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
def transfer(from_account: Account, to_account: Account, amount: float) -> None:
    """Transfer funds between accounts."""
    with db.transaction():
        from_account.balance -= amount
        to_account.balance += amount
        db.update(from_account)
        db.update(to_account)
```

### Create or Update Pattern

```python
def create_or_update(user: User) -> None:
    """Insert or update a user."""
    with db.transaction():
        existing = db.select(User).filter(
            email=user.email
        ).fetch_one()

        if existing:
            existing.name = user.name
            db.update(existing)
        else:
            db.insert(user)
```

## Best Practices

### DO

- Use transactions for multi-step operations
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
