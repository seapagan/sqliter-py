# CRUD Operations Demos

These demos demonstrate the basic Create, Read, Update, and Delete operations in SQLiter.

## Insert Records

Add new records to the database.

```python
# --8<-- [start:insert]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    name: str
    email: str

db = SqliterDB(memory=True)
db.create_table(User)

# Insert a single record
user = db.insert(User(name="Alice", email="alice@example.com"))
print(f"Created user with pk={user.pk}")

# Insert multiple records
users = [
    User(name="Bob", email="bob@example.com"),
    User(name="Charlie", email="charlie@example.com"),
]
for user in users:
    db.insert(user)
```

### Return Value
`db.insert()` returns the inserted model instance with the `pk` field populated.

### Performance
For bulk inserts, consider using transactions (see [Transactions](transactions.md)) for better performance.

## Get by Primary Key

Retrieve a single record by its primary key.

```python
# --8<-- [start:get-by-pk]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    name: str
    email: str

db = SqliterDB(memory=True)
db.create_table(User)

# Insert a user
user = db.insert(User(name="Alice", email="alice@example.com"))

# Retrieve by primary key
retrieved_user = db.get_by_pk(User, user.pk)
print(f"Retrieved: {retrieved_user.name}")
```

### When Record Doesn't Exist
Returns `None` if no record is found with that primary key.

## Update Records

Modify existing records.

```python
# --8<-- [start:update]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Task(BaseDBModel):
    title: str
    done: bool = False

db = SqliterDB(memory=True)
db.create_table(Task)

# Insert a task
task = db.insert(Task(title="Buy groceries"))

# Update the task
task.title = "Buy groceries and cook dinner"
task.done = True
db.update(task)

# Verify the update
updated_task = db.get_by_pk(Task, task.pk)
print(f"Task status: {updated_task.done}")
```

### Update Process
1. Retrieve the record (or keep reference from insert)
2. Modify the fields
3. Call `db.update()` with the modified object

### Auto-Timestamps
If your model has `updated_at`, it's automatically updated when you call `db.update()`.

## Delete Records

Remove records from the database.

```python
# --8<-- [start:delete]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Note(BaseDBModel):
    content: str

db = SqliterDB(memory=True)
db.create_table(Note)

# Insert a note
note = db.insert(Note(content="Temporary note"))

# Delete the note
db.delete(note)

# Verify deletion
deleted_note = db.get_by_pk(Note, note.pk)
print(f"Note exists: {deleted_note is not None}")  # False
```

### Foreign Key Constraints
If other records reference this record (via foreign keys), the delete will fail unless you handle the dependencies first.

## Operation Summary

| Operation | Method | Returns |
|-----------|--------|---------|
| **Create** | `db.insert(Model(...))` | The model with `pk` set |
| **Read** | `db.get_by_pk(Model, pk)` | The model or `None` |
| **Update** | `db.update(model)` | Nothing (modifies in-place) |
| **Delete** | `db.delete(model)` | Nothing |

## Best Practices

### DO:
- Keep the returned model from `insert()` for later use
- Use `get_by_pk()` when you know the primary key
- Validate data before inserting (Pydantic does this automatically)
- Use transactions for multiple related operations

### DON'T:
- Forget to call `db.update()` after modifying a model
- Assume `get_by_pk()` always returns a record (check for `None`)
- Delete records without checking for foreign key dependencies

## Related Documentation

- [Models](models.md) - Define your data models
- [Query Results](results.md) - Fetch records in different ways
- [Transactions](transactions.md) - Group operations atomically
- [Filtering](filters.md) - Query records with conditions
