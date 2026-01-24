# Query Results Demos

These demos show different ways to fetch query results.

## Fetch One

Get a single record from a query.

```python
# --8<-- [start:fetch-one]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    name: str
    email: str

db = SqliterDB(memory=True)
db.create_table(User)

db.insert(User(name="Alice", email="alice@example.com"))
db.insert(User(name="Bob", email="bob@example.com"))

# Get the first matching record
user = db.select(User).fetch_one()
print(f"First user: {user.name}")
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

class Product(BaseDBModel):
    name: str
    price: float

db = SqliterDB(memory=True)
db.create_table(Product)

db.insert(Product(name="Widget", price=10.0))
db.insert(Product(name="Gadget", price=15.0))
db.insert(Product(name="Tool", price=20.0))

# Get all products
products = db.select(Product).fetch_all()
for product in products:
    print(f"{product.name}: ${product.price}")
```

### Return Type

Returns a list of model instances. Empty list if no results.

### Memory Consideration

Be careful with large result sets - all records are loaded into memory.

## Fetch First

Get only the first N records (pagination).

```python
# --8<-- [start:fetch-first]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Article(BaseDBModel):
    title: str

db = SqliterDB(memory=True)
db.create_table(Article)

# Insert many articles
for i in range(100):
    db.insert(Article(title=f"Article {i}"))

# Get only the first 10
recent = db.select(Article).fetch_first(10)
print(f"Showing {len(recent)} articles")
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

class Order(BaseDBModel):
    status: str

db = SqliterDB(memory=True)
db.create_table(Order)

# Insert various orders
for status in ["pending", "shipped", "delivered"]:
    for _ in range(5):
        db.insert(Order(status=status))

# Count pending orders
pending_count = db.select(Order).filter(
    status="pending"
).count()
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

# Check if username exists
has_alice = db.select(User).filter(
    username="alice"
).exists()
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
| `fetch_first(n)` | List of records (max n) | Pagination, limiting results |
| `count()` | Integer count | Statistics, validation |
| `exists()` | Boolean | Quick existence check |

## Performance Considerations

### Large Datasets

```python
# ❌ BAD: Loads all records into memory
all_users = db.select(User).fetch_all()

# ✅ GOOD: Process in batches or use pagination
while True:
    batch = db.select(User).fetch_first(100)
    if not batch:
        break
    for user in batch:
        process(user)
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
- Use `fetch_first()` for pagination
- Check for `None` when using `fetch_one()`

### DON'T

- Use `fetch_all()` on potentially huge datasets
- Count results with `len()` - use `count()` instead
- Forget that `fetch_one()` returns `None` if no results

## Related Documentation

- [Filtering](filters.md) - Filter which records are returned
- [Ordering](ordering.md) - Sort results before fetching
- [Field Selection](field-selection.md) - Control which fields are returned
