# Filtering Demos

These demos show how to filter query results using various comparison operators.

## Equal To

Find records where a field exactly matches a value.

```python
# --8<-- [start:filter-eq]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    name: str
    age: int

db = SqliterDB(memory=True)
db.create_table(User)

db.insert(User(name="Alice", age=30))
db.insert(User(name="Bob", age=25))
db.insert(User(name="Alice", age=35))

results = db.select(User).filter(name__eq="Alice").fetch_all()
print(f"Found {len(results)} users named 'Alice':")
for user in results:
    print(f"  - {user.name}, age {user.age}")

db.close()
# --8<-- [end:filter-eq]
```

### Alternative Syntax

`category="gadgets"` works the same as `category__eq="gadgets"`.

## Not Equal To

Find records where a field doesn't match a value.

```python
# --8<-- [start:filter-ne]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Item(BaseDBModel):
    name: str
    status: str

db = SqliterDB(memory=True)
db.create_table(Item)

db.insert(Item(name="Item 1", status="active"))
db.insert(Item(name="Item 2", status="archived"))
db.insert(Item(name="Item 3", status="active"))

results = db.select(Item).filter(status__ne="archived").fetch_all()
print(f"Non-archived items: {len(results)}")

db.close()
# --8<-- [end:filter-ne]
```

## Greater Than / Less Than

Filter numeric fields using comparison operators.

```python
# --8<-- [start:filter-comparison]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Product(BaseDBModel):
    name: str
    price: float

db = SqliterDB(memory=True)
db.create_table(Product)

db.insert(Product(name="Item A", price=10.0))
db.insert(Product(name="Item B", price=20.0))
db.insert(Product(name="Item C", price=30.0))

# Greater than
expensive = db.select(Product).filter(price__gt=15.0).fetch_all()
print(f"Products > $15: {len(expensive)}")

# Less than or equal
cheap = db.select(Product).filter(price__lte=20.0).fetch_all()
print(f"Products <= $20: {len(cheap)}")

db.close()
# --8<-- [end:filter-comparison]
```

### Available Operators

| Operator | Description |
|----------|-------------|
| `__gt` | Greater than |
| `__lt` | Less than |
| `__gte` | Greater than or equal |
| `__lte` | Less than or equal |

## In List

Find records where a field matches any value in a list.

```python
# --8<-- [start:filter-in]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Task(BaseDBModel):
    title: str
    status: str

db = SqliterDB(memory=True)
db.create_table(Task)

db.insert(Task(title="Task 1", status="todo"))
db.insert(Task(title="Task 2", status="done"))
db.insert(Task(title="Task 3", status="in_progress"))
db.insert(Task(title="Task 4", status="done"))

results = (
    db.select(Task).filter(status__in=["todo", "in_progress"]).fetch_all()  # type: ignore[arg-type]
)
print(f"Active tasks: {len(results)}")
for task in results:
    print(f"  - {task.title}: {task.status}")

db.close()
# --8<-- [end:filter-in]
```

### When to Use

- Filtering by multiple possible values
- Checking membership in a set
- Simplifying multiple `OR` conditions

## Null Checks

Find records where a field is null (None) or not null.

```python
# --8<-- [start:filter-null]
from typing import Optional
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Task(BaseDBModel):
    title: str
    assigned_to: Optional[str] = None

db = SqliterDB(memory=True)
db.create_table(Task)

db.insert(Task(title="Task 1", assigned_to="Alice"))
db.insert(Task(title="Task 2", assigned_to=None))  # Unassigned
db.insert(Task(title="Task 3", assigned_to="Bob"))
db.insert(Task(title="Task 4", assigned_to=None))  # Unassigned

# Find unassigned tasks
unassigned = db.select(Task).filter(assigned_to__isnull=True).fetch_all()
print(f"Unassigned tasks: {len(unassigned)}")
for task in unassigned:
    print(f"  - {task.title}")

# Find assigned tasks
assigned = db.select(Task).filter(assigned_to__notnull=True).fetch_all()
print(f"Assigned tasks: {len(assigned)}")
for task in assigned:
    print(f"  - {task.title}: {task.assigned_to}")

db.close()
# --8<-- [end:filter-null]
```

### Null vs Empty String

- `None` (null): Field was never set
- `""` (empty string): Field was explicitly set to empty
- Use `__isnull` to check for `None`

## Chaining Filters

Combine multiple filter conditions.

```python
# --8<-- [start:filter-chain]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    name: str
    age: int
    city: str

db = SqliterDB(memory=True)
db.create_table(User)

db.insert(User(name="Alice", age=30, city="NYC"))
db.insert(User(name="Bob", age=25, city="LA"))
db.insert(User(name="Charlie", age=30, city="NYC"))

results = (
    db.select(User).filter(age__gte=30).filter(city__eq="NYC").fetch_all()
)
print(f"Users in NYC aged 30+: {len(results)}")
for user in results:
    print(f"  - {user.name}, {user.age}")

db.close()
# --8<-- [end:filter-chain]
```

### How It Works

All filter conditions are combined with **AND** logic - only records matching ALL conditions are returned.

### Alternative One-Line Syntax

```python
affordable = db.select(Product).filter(
    price__lt=20.0,
    stock__gte=50
).fetch_all()
```

## Best Practices

### DO

- Use specific filter operators (`__eq`, `__gt`, etc.) for clarity
- Chain filters when you have multiple conditions
- Use `__in` for checking multiple values instead of multiple `OR` conditions

### DON'T

- Filter on non-indexed fields in large datasets (performance issue)
- Forget that text comparisons are case-sensitive
- Mix up `__gt` (greater than) with `__lt` (less than)

## Related Documentation

- [String Filters](string-filters.md) - Special string matching operators
- [Query Results](results.md) - Fetch filtered results
- [Ordering](ordering.md) - Sort filtered results
