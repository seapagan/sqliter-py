# Ordering Demos

These demos show how to sort query results.

## Order By Single Field

Sort results by a single field.

```python
# --8<-- [start:order-by]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Product(BaseDBModel):
    name: str
    price: float

db = SqliterDB(memory=True)
db.create_table(Product)

db.insert(Product(name="Widget", price=10.0))
db.insert(Product(name="Gadget", price=5.0))
db.insert(Product(name="Tool", price=15.0))

# Order by price (ascending)
products = db.select(Product).order_by("price").fetch_all()
for product in products:
    print(f"{product.name}: ${product.price}")
```

### Default Order
By default, `order_by()` sorts in **ascending** order (lowest to highest).

## Descending Order

Sort results in reverse order.

```python
# --8<-- [start:order-by-desc]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Article(BaseDBModel):
    title: str

db = SqliterDB(memory=True)
db.create_table(Article)

articles = [
    "First Post",
    "Second Post",
    "Third Post",
]
for title in articles:
    db.insert(Article(title=title))

# Order by primary key in descending order (newest first)
recent = db.select(Article).order_by("-pk").fetch_all()
```

### Descending Syntax
Prefix the field name with `-` for descending order:
- `"price"` → Ascending (low to high)
- `"-price"` → Descending (high to low)
- `"pk"` → Oldest first
- `"-pk"` → Newest first

## Order by Multiple Fields

Sort by multiple fields for complex ordering.

```python
# --8<-- [start:order-by-multiple]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Task(BaseDBModel):
    priority: int
    title: str

db = SqliterDB(memory=True)
db.create_table(Task)

db.insert(Task(priority=1, title="Low priority task"))
db.insert(Task(priority=1, title="Another low priority task"))
db.insert(Task(priority=2, title="High priority task"))

# Order by priority (ascending), then by title (alphabetically)
tasks = db.select(Task).order_by("priority", "title").fetch_all()
```

### How It Works
Results are sorted by the first field, then by the second field within ties, and so on.

### Common Pattern
```python
# Sort by category, then by name within each category
items = db.select(Item).order_by("category", "name").fetch_all()
```

## Ordering with Filtering

Combine filtering and ordering.

```python
# --8<-- [start:order-with-filter]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    name: str
    age: int

db = SqliterDB(memory=True)
db.create_table(User)

# Filter adults, order by age
adults = db.select(User).filter(
    age__gte=18
).order_by("age").fetch_all()
```

### Order Matters
The order of method chaining doesn't matter for the result, but affects readability:

```python
# Both are equivalent
db.select(User).filter(age__gte=18).order_by("age").fetch_all()
db.select(User).order_by("age").filter(age__gte=18).fetch_all()
```

## Ordering Field Types

Different field types have different sort behaviors:

### Numbers
Sorted numerically: `1, 2, 10, 100`

### Strings
Sorted alphabetically: `"Apple", "Banana", "Cherry"`

### Dates/Timestamps
Sorted chronologically (oldest to newest for `created_at`)

### Booleans
`False` (0) comes before `True` (1)

## Performance Considerations

### Indexes
Ordering by indexed fields is much faster:

```python
class User(BaseDBModel):
    username: unique(str)  # Indexed
    age: int  # Not indexed

# Fast: Uses index
db.select(User).order_by("username").fetch_all()

# Slower: Requires full table scan
db.select(User).order_by("age").fetch_all()
```

### Large Result Sets
Ordering requires the database to process all matching records before returning results.

## Best Practices

### DO:
- Order by indexed fields for better performance
- Use descending order (`-field`) for "newest first" queries
- Order by multiple fields when you need secondary sorting

### DON'T:
- Order by fields you don't need to sort by
- Forget that string sorting is case-sensitive
- Order large result sets without pagination

## Related Documentation

- [Query Results](results.md) - Fetch and paginate results
- [Filtering](filters.md) - Filter records before ordering
- [Field Selection](field-selection.md) - Control which fields are returned
