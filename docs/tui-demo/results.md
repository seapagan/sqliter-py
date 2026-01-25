# Query Results Demos

These demos show different ways to fetch query results.

## Fetch One

Get a single record from a query.

```python
# --8<-- [start:fetch-one]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Task(BaseDBModel):
    title: str
    priority: int

db = SqliterDB(memory=True)
db.create_table(Task)

db.insert(Task(title="High priority", priority=1))
db.insert(Task(title="Medium priority", priority=2))
db.insert(Task(title="Low priority", priority=3))

task = db.select(Task).filter(priority__eq=1).fetch_one()
if task is not None:
    print(f"Single result: {task.title}")

# Also test no results case
no_task = db.select(Task).filter(priority__eq=999).fetch_one()
if no_task is None:
    print("No task found with priority 999")

db.close()
# --8<-- [end:fetch-one]
```

### When No Results

Returns `None` if no records match the query.

### Use Cases

- **Find specific user**: When you expect only one result
- **Get first match**: When you only need the first record
- **Existence checks**: Quick check if any records match

## Fetch All

Get all matching records.

```python
# --8<-- [start:fetch-all]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    name: str
    age: int

db = SqliterDB(memory=True)
db.create_table(User)

for i in range(5):
    db.insert(User(name=f"User {i}", age=20 + i))

results = db.select(User).fetch_all()
print(f"Total users: {len(results)}")
for user in results:
    print(f"  - {user.name}, age {user.age}")

db.close()
# --8<-- [end:fetch-all]
```

### Return Type

Returns a list of model instances. Empty list if no results.

### Memory Consideration

Be careful with large result sets - all records are loaded into memory.

## Fetch First / Limit Results

Get only the first N records (pagination).

```python
# --8<-- [start:fetch-first]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Item(BaseDBModel):
    name: str

db = SqliterDB(memory=True)
db.create_table(Item)

for name in ["Alpha", "Beta", "Gamma", "Delta"]:
    db.insert(Item(name=name))

first = db.select(Item).fetch_first()
if first is not None:
    print(f"First: {first.name}")

last = db.select(Item).fetch_last()
if last is not None:
    print(f"Last: {last.name}")

db.close()
# --8<-- [end:fetch-first]
```

### Use Cases

- **Pagination**: Show first page of results
- **Previews**: Display sample data
- **Limit load**: Prevent loading too many records

## Count Results

Count matching records without fetching them.

```python
# --8<-- [start:count]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Product(BaseDBModel):
    name: str
    category: str

db = SqliterDB(memory=True)
db.create_table(Product)

db.insert(Product(name="Laptop", category="electronics"))
db.insert(Product(name="Phone", category="electronics"))
db.insert(Product(name="Desk", category="furniture"))

total = db.select(Product).count()
print(f"Total products: {total}")

electronics = db.select(Product).filter(category__eq="electronics").count()
print(f"Electronics: {electronics}")

db.close()
# --8<-- [end:count]
```

### Benefits

- **Fast**: Database counts without transferring data
- **Memory efficient**: No records loaded into memory
- **Statistics**: Quick counts for dashboards

## Exists Check

Check if any records match without fetching them.

```python
# --8<-- [start:exists]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    username: str

db = SqliterDB(memory=True)
db.create_table(User)

db.insert(User(username="alice"))
db.insert(User(username="bob"))

exists = db.select(User).filter(username__eq="alice").exists()
print(f"User 'alice' exists: {exists}")

not_exists = db.select(User).filter(username__eq="charlie").exists()
print(f"User 'charlie' exists: {not_exists}")

db.close()
# --8<-- [end:exists]
```

### Use Cases

- **Validation**: Check if username/email already exists
- **Conditional logic**: Branch based on existence
- **Fast checks**: Quicker than fetching the actual record

## Comparison Table

| Method | Returns | Use When |
|--------|---------|----------|
| `fetch_one()` | Single record or `None` | You need exactly one record |
| `fetch_all()` | List of records (all) | You need all matching records |
| `limit(n).fetch_all()` | List of records (max n) | Pagination, limiting results |
| `count()` | Integer count | Statistics, validation |
| `exists()` | Boolean | Quick existence check |

## Performance Considerations

### Large Datasets

```python
# ❌ BAD: Loads all records into memory
all_users = db.select(User).fetch_all()

# ✅ GOOD: Process in batches using limit and offset
offset = 0
batch_size = 100
while True:
    batch = db.select(User).limit(batch_size).offset(offset).fetch_all()
    if not batch:
        break
    for user in batch:
        process(user)
    offset += batch_size
```

### Counting

```python
# ❌ BAD: Counts in Python (slow)
count = len(db.select(User).fetch_all())

# ✅ GOOD: Count in database (fast)
count = db.select(User).count()
```

## Best Practices

### DO

- Use `fetch_one()` when you expect a single result
- Use `count()` for statistics instead of counting in Python
- Use `limit()` with `offset()` for pagination
- Check for `None` when using `fetch_one()`

### DON'T

- Use `fetch_all()` on potentially huge datasets
- Count results with `len()` - use `count()` instead
- Forget that `fetch_one()` returns `None` if no results

## Related Documentation

- [Filtering](filters.md) - Filter which records are returned
- [Ordering](ordering.md) - Sort results before fetching
- [Field Selection](field-selection.md) - Control which fields are returned
