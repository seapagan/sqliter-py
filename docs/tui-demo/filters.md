# Filtering Demos

These demos show how to filter query results using various comparison operators.

## Equal To

Find records where a field exactly matches a value.

```python
# --8<-- [start:filter-eq]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Product(BaseDBModel):
    name: str
    price: float
    category: str

db = SqliterDB(memory=True)
db.create_table(Product)

db.insert(Product(name="Widget", price=10.0, category="gadgets"))
db.insert(Product(name="Gadget", price=15.0, category="gadgets"))
db.insert(Product(name="Tool", price=20.0, category="tools"))

# Filter using exact match
results = db.select(Product).filter(category__eq="gadgets").fetch_all()
for product in results:
    print(f"{product.name}: ${product.price}")
```

### Alternative Syntax
`category="gadgets"` works the same as `category__eq="gadgets"`.

## Not Equal To

Find records where a field doesn't match a value.

```python
# --8<-- [start:filter-ne]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Task(BaseDBModel):
    title: str
    status: str

db = SqliterDB(memory=True)
db.create_table(Task)

db.insert(Task(title="Task 1", status="done"))
db.insert(Task(title="Task 2", status="pending"))
db.insert(Task(title="Task 3", status="done"))

# Find tasks that are not done
pending = db.select(Task).filter(status__ne="done").fetch_all()
print(f"Pending tasks: {len(pending)}")
```

## Greater Than / Less Than

Filter numeric fields using comparison operators.

```python
# --8<-- [start:filter-comparison]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    name: str
    age: int

db = SqliterDB(memory=True)
db.create_table(User)

# Insert users of various ages
for i in range(10, 50, 10):
    db.insert(User(name=f"User {i}", age=i))

# Find users older than 25
adults = db.select(User).filter(age__gt=25).fetch_all()

# Find users 30 or younger
young_users = db.select(User).filter(age__lte=30).fetch_all()
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

class Order(BaseDBModel):
    product_name: str
    status: str

db = SqliterDB(memory=True)
db.create_table(Order)

statuses = ["pending", "processing", "shipped"]
for status in statuses:
    db.insert(Order(product_name="Widget", status=status))

# Find only pending or processing orders
active_orders = db.select(Order).filter(
    status__in=["pending", "processing"]
).fetch_all()
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

# Insert some tasks with and without assignment
db.insert(Task(title="Unassigned task"))
db.insert(Task(title="Assigned task", assigned_to="Alice"))

# Find unassigned tasks
unassigned = db.select(Task).filter(assigned_to__isnull=True).fetch_all()

# Find assigned tasks
assigned = db.select(Task).filter(assigned_to__notnull=True).fetch_all()
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

class Product(BaseDBModel):
    name: str
    price: float
    stock: int

db = SqliterDB(memory=True)
db.create_table(Product)

db.insert(Product(name="Cheap Widget", price=5.0, stock=100))
db.insert(Product(name="Expensive Gadget", price=50.0, stock=5))
db.insert(Product(name="Cheap Tool", price=8.0, stock=50))

# Filter by multiple conditions (AND logic)
affordable = db.select(Product).filter(
    price__lt=20.0
).filter(
    stock__gte=50
).fetch_all()
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

### DO:
- Use specific filter operators (`__eq`, `__gt`, etc.) for clarity
- Chain filters when you have multiple conditions
- Use `__in` for checking multiple values instead of multiple `OR` conditions

### DON'T:
- Filter on non-indexed fields in large datasets (performance issue)
- Forget that text comparisons are case-sensitive
- Mix up `__gt` (greater than) with `__lt` (less than)

## Related Documentation

- [String Filters](string-filters.md) - Special string matching operators
- [Query Results](results.md) - Fetch filtered results
- [Ordering](ordering.md) - Sort filtered results
