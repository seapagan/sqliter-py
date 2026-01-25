# Field Selection Demos

These demos show how to control which fields are returned in your queries.

## Select Specific Fields

Fetch only the columns you need to reduce data transfer.

```python
# --8<-- [start:select-fields]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    name: str
    email: str
    age: int
    city: str

db = SqliterDB(memory=True)
db.create_table(User)

db.insert(User(name="Alice", email="alice@example.com", age=30, city="NYC"))
db.insert(User(name="Bob", email="bob@example.com", age=25, city="LA"))

# Select only name and email
users = db.select(User).fields(["name", "email"]).fetch_all()
print("Selected only name and email fields:")
for user in users:
    print(f"  - {user.name}, {user.email}")

# Note: age and city are None since they weren't selected
print("(age and city not selected, set to None)")

db.close()
# --8<-- [end:select-fields]
```

### Benefits

- **Performance**: Less data transferred from database
- **Memory**: Lower memory usage for large result sets
- **Clarity**: Explicit about what data you need

### When to Use

- **API responses**: Only send needed fields to clients
- **Large records**: Records with many fields but you only need a few
- **Sensitive data**: Exclude fields like passwords

## Exclude Fields

Specify fields to exclude from results.

```python
# --8<-- [start:exclude-fields]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Product(BaseDBModel):
    name: str
    price: float
    description: str
    stock: int

db = SqliterDB(memory=True)
db.create_table(Product)

db.insert(
    Product(
        name="Laptop",
        price=999.99,
        description="Fast laptop",
        stock=10,
    )
)

# Exclude description and stock
product = db.select(Product).exclude(["description", "stock"]).fetch_one()
if product is not None:
    print(f"Product: {product.name}")
    print(f"Price: ${product.price}")
    print("(description and stock excluded)")

db.close()
# --8<-- [end:exclude-fields]
```

### Use Cases

- **Hidden fields**: Exclude internal metadata
- **Large fields**: Exclude large text/binary fields not needed for display
- **Sensitive data**: Exclude passwords, tokens, etc.

## Select Single Field

Fetch only one field from a query.

```python
# --8<-- [start:only-field]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Task(BaseDBModel):
    title: str
    status: str
    priority: int
    assigned_to: str

db = SqliterDB(memory=True)
db.create_table(Task)

db.insert(
    Task(title="Fix bug", status="todo", priority=1, assigned_to="Alice")
)
db.insert(
    Task(title="Add feature", status="done", priority=2, assigned_to="Bob")
)

# Select only the title field
tasks = db.select(Task).only("title").fetch_all()
print("Selected only title field:")
for task in tasks:
    print(f"  - {task.title}")

print("(status, priority, assigned_to not selected)")

db.close()
# --8<-- [end:only-field]
```

### When to Use

- **Lists/ dropdowns**: Only need display values
- **Aggregation**: Extract specific column values
- **Simple queries**: You only need one piece of information

## Field Selection vs. Filtering

Important distinction:

```python
# Field selection: Controls which COLUMNS are returned
db.select(User).fields(["name", "email"]).fetch_all()

# Filtering: Controls which ROWS are returned
db.select(User).filter(age__gte=18).fetch_all()
```

## Performance Impact

### Before Optimization

```python
# Fetches all fields (potentially large records)
users = db.select(User).fetch_all()  # All fields included
```

### After Optimization

```python
# Fetches only needed fields
users = db.select(User).fields(["name", "email"]).fetch_all()
```

### Performance Gains

- **Less memory**: Smaller objects in memory
- **Faster queries**: Database optimization can apply
- **Cleaner code**: Intent is explicit

## Limitations

### Partial Objects

Fields that aren't selected will be `None`:

```python
user = db.select(User).fields(["name"]).fetch_one()
print(user.name)    # Has value
print(user.email)   # None (not selected)
print(user.age)     # None (not selected)
```

### Updates

Be careful when updating partially fetched objects:

```python
# Fetch only name
user = db.select(User).fields(["name"]).fetch_one()
user.name = "New Name"
# user.email is None - don't call db.update() or you'll lose the email!
```

!!! warning
    Don't update partially fetched objects unless you're certain about the impact. Either fetch all fields first, or only update the fields you selected.

## Best Practices

### DO

- Select only the fields you need for display/processing
- Use field selection for API responses
- Consider memory usage for large datasets

### DON'T

- Update partially fetched objects without understanding the impact
- Use field selection if you need to update the record later
- Forget that unselected fields will be `None`

## Related Documentation

- [Query Results](results.md) - Fetch results in different ways
- [Filtering](filters.md) - Filter which rows are returned
- [CRUD Operations](crud.md) - Update and delete records
