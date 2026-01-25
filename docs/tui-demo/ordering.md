# Ordering Demos

These demos show how to sort query results.

## Order By Single Field

Sort results by a single field.

```python
# --8<-- [start:order-by]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    name: str
    age: int

db = SqliterDB(memory=True)
db.create_table(User)

db.insert(User(name="Charlie", age=35))
db.insert(User(name="Alice", age=25))
db.insert(User(name="Bob", age=30))

results = db.select(User).order("age").fetch_all()
print("Users ordered by age (ascending):")
for user in results:
    print(f"  - {user.name}: {user.age}")

db.close()
# --8<-- [end:order-by]
```

### Default Order

By default, `order()` sorts in **ascending** order (lowest to highest).

## Descending Order

Sort results in reverse order.

```python
# --8<-- [start:order-by-desc]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Product(BaseDBModel):
    name: str
    price: float

db = SqliterDB(memory=True)
db.create_table(Product)

db.insert(Product(name="Item A", price=10.0))
db.insert(Product(name="Item B", price=30.0))
db.insert(Product(name="Item C", price=20.0))

results = db.select(Product).order("price", reverse=True).fetch_all()
print("Products ordered by price (descending):")
for product in results:
    print(f"  - {product.name}: ${product.price}")

db.close()
# --8<-- [end:order-by-desc]
```

### Descending Syntax

Use `reverse=True` for descending order:

- `order("price")` → Ascending (low to high)
- `order("price", reverse=True)` → Descending (high to low)
- `order("pk")` → Oldest first
- `order("pk", reverse=True)` → Newest first

## Limit Results

Limit the number of results returned for pagination.

```python
# --8<-- [start:order-by-multiple]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Article(BaseDBModel):
    title: str

db = SqliterDB(memory=True)
db.create_table(Article)

for i in range(1, 11):
    db.insert(Article(title=f"Article {i}"))

results = db.select(Article).limit(3).fetch_all()
print("Top 3 articles:")
for article in results:
    print(f"  - {article.title}")

db.close()
# --8<-- [end:order-by-multiple]
```

### Use Cases

- **Pagination**: Display first page of results
- **Previews**: Show sample data
- **Performance**: Avoid loading too many records

## Offset Results (Pagination)

Skip a specified number of results for pagination.

```python
# --8<-- [start:order-with-filter]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Item(BaseDBModel):
    name: str

db = SqliterDB(memory=True)
db.create_table(Item)

for i in range(1, 11):
    db.insert(Item(name=f"Item {i}"))

results = db.select(Item).limit(5).offset(5).fetch_all()
print("Items 6-10:")
for item in results:
    print(f"  - {item.name}")

db.close()
# --8<-- [end:order-with-filter]
```

### How Pagination Works

- `offset(5)` skips the first 5 records
- `limit(5)` takes the next 5 records
- Together they implement page 2 of a paginated result set

### Common Pattern

```python
page = 2
page_size = 10
offset_value = (page - 1) * page_size

results = db.select(User).limit(page_size).offset(offset_value).fetch_all()
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
from sqliter.model.unique import unique

class User(BaseDBModel):
    username: str = unique()  # Indexed
    age: int  # Not indexed

# Fast: Uses index
db.select(User).order("username").fetch_all()

# Slower: Requires full table scan
db.select(User).order("age").fetch_all()
```

### Large Result Sets

Ordering requires the database to process all matching records before returning results.

## Best Practices

### DO

- Order by indexed fields for better performance
- Use descending order (`reverse=True`) for "newest first" queries
- Combine with `limit()` for pagination on large datasets

### DON'T

- Order by fields you don't need to sort by
- Forget that string sorting is case-sensitive
- Order large result sets without pagination

## Related Documentation

- [Query Results](results.md) - Fetch and paginate results
- [Filtering](filters.md) - Filter records before ordering
- [Field Selection](field-selection.md) - Control which fields are returned
