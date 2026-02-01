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

user1 = db.insert(User(name="Alice", email="alice@example.com"))
print(f"Inserted: {user1.name} (pk={user1.pk})")

user2 = db.insert(User(name="Bob", email="bob@example.com"))
print(f"Inserted: {user2.name} (pk={user2.pk})")

db.close()
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

class Task(BaseDBModel):
    title: str
    done: bool = False

db = SqliterDB(memory=True)
db.create_table(Task)

task: Task = db.insert(Task(title="Buy groceries"))
print(f"Created: {task.title} (pk={task.pk})")

retrieved = db.get(Task, task.pk)
if retrieved is not None:
    task_retrieved = retrieved
    print(f"Retrieved: {task_retrieved.title}")
    print(f"Same object: {task_retrieved.pk == task.pk}")

db.close()
```

### When Record Doesn't Exist

Returns `None` if no record is found with that primary key.

## Update Records

Modify existing records.

```python
# --8<-- [start:update]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Item(BaseDBModel):
    name: str
    quantity: int

db = SqliterDB(memory=True)
db.create_table(Item)

item = db.insert(Item(name="Apples", quantity=5))
print(f"Created: {item.name} x{item.quantity}")

item.quantity = 10
db.update(item)
print(f"Updated: {item.name} x{item.quantity}")

db.close()
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

note = db.insert(Note(content="Temporary note"))
print(f"Created note (pk={note.pk})")

db.delete(Note, note.pk)
print(f"Deleted note with pk={note.pk}")

all_notes = db.select(Note).fetch_all()
print(f"Remaining notes: {len(all_notes)}")

db.close()
```

### Foreign Key Constraints

If other records reference this record (via foreign keys), the delete will fail unless you handle the dependencies first.

## Bulk Insert

Insert multiple records in a single transaction.

```python
# --8<-- [start:bulk-insert]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Product(BaseDBModel):
    name: str
    price: float

db = SqliterDB(memory=True)
db.create_table(Product)

products = [
    Product(name="Widget", price=9.99),
    Product(name="Gadget", price=24.99),
    Product(name="Gizmo", price=14.99),
]
results = db.bulk_insert(products)

print(f"Inserted {len(results)} products:")
for product in results:
    print(f"  pk={product.pk}: {product.name} (${product.price})")

total = db.select(Product).count()
print(f"\nTotal products in database: {total}")

db.close()
```

### What Happens

- `db.bulk_insert()` inserts all records in a single transaction
- Each returned instance has its `pk` field populated
- If any insert fails, all inserts in the batch are rolled back
- Auto-timestamps (`created_at`, `updated_at`) are set on each record

### When to Use Bulk Insert

- **Use** when inserting multiple records of the same model type
- **Use** for seeding data or importing batches
- **Don't use** for mixed model types (raises `ValueError`)

## Operation Summary

| Operation | Method | Returns |
|-----------|--------|---------|
| **Create** | `db.insert(Model(...))` | The model with `pk` set |
| **Create (batch)** | `db.bulk_insert([...])` | List of models with `pk` set |
| **Read** | `db.get(Model, pk)` | The model or `None` |
| **Update** | `db.update(model)` | Nothing (modifies in-place) |
| **Delete** | `db.delete(Model, pk)` | Nothing |

## Best Practices

### DO

- Keep the returned model from `insert()` for later use
- Use `get()` when you know the primary key
- Validate data before inserting (Pydantic does this automatically)
- Use transactions for multiple related operations

### DON'T

- Forget to call `db.update()` after modifying a model
- Assume `get()` always returns a record (check for `None`)
- Delete records without checking for foreign key dependencies

## Related Documentation

- [Models](models.md) - Define your data models
- [Query Results](results.md) - Fetch records in different ways
- [Transactions](transactions.md) - Group operations atomically
- [Filtering](filters.md) - Query records with conditions
