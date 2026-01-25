# String Filter Demos

These demos show special filtering operators for string fields.

## Starts With

Find strings that begin with a specific prefix.

```python
# --8<-- [start:startswith]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    username: str

db = SqliterDB(memory=True)
db.create_table(User)

db.insert(User(username="alice_wonder"))
db.insert(User(username="alice_smith"))
db.insert(User(username="bob_builder"))

# Find usernames starting with "alice"
results = db.select(User).filter(username__startswith="alice").fetch_all()
print(f"Users starting with 'alice': {len(results)}")
for user in results:
    print(f"  - {user.username}")

db.close()
# --8<-- [end:startswith]
```

### Use Cases

- **Prefix matching**: Find items with a specific code prefix
- **Name filtering**: Find users whose names start with certain letters
- **Category browsing**: Filter products by category prefix

## Ends With

Find strings that end with a specific suffix.

```python
# --8<-- [start:endswith]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class File(BaseDBModel):
    filename: str

db = SqliterDB(memory=True)
db.create_table(File)

db.insert(File(filename="document.txt"))
db.insert(File(filename="image.png"))
db.insert(File(filename="notes.txt"))
db.insert(File(filename="data.csv"))

# Find files ending with ".txt"
results = db.select(File).filter(filename__endswith=".txt").fetch_all()
print(f"Text files: {len(results)}")
for file in results:
    print(f"  - {file.filename}")

db.close()
# --8<-- [end:endswith]
```

### Use Cases

- **File extensions**: Filter by file type
- **Domain matching**: Find emails from a specific domain
- **Suffix filtering**: Items ending in specific codes

## Contains

Find strings that contain a specific substring.

```python
# --8<-- [start:contains]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Product(BaseDBModel):
    name: str

db = SqliterDB(memory=True)
db.create_table(Product)

db.insert(Product(name="Apple iPhone"))
db.insert(Product(name="Samsung Galaxy"))
db.insert(Product(name="Apple iPad"))
db.insert(Product(name="Google Pixel"))

# Find products containing "Apple"
results = db.select(Product).filter(name__contains="Apple").fetch_all()
print(f"Products containing 'Apple': {len(results)}")
for product in results:
    print(f"  - {product.name}")

db.close()
# --8<-- [end:contains]
```

### Use Cases

- **Search functionality**: Full-text search in descriptions
- **Keyword matching**: Find items with specific keywords
- **Pattern matching**: Flexible string matching

## Case-Insensitive Matching

Perform string filtering that ignores case.

```python
# --8<-- [start:case-insensitive]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    email: str

db = SqliterDB(memory=True)
db.create_table(User)

db.insert(User(email="ALICE@example.com"))
db.insert(User(email="bob@EXAMPLE.com"))
db.insert(User(email="charlie@test.com"))

# Find emails ending with "@example.com" (case-insensitive)
results = (
    db.select(User).filter(email__iendswith="@example.com").fetch_all()
)
print(f"Emails ending with '@example.com': {len(results)}")
for user in results:
    print(f"  - {user.email}")

# Find emails starting with "BOB" (case-insensitive)
bob_results = db.select(User).filter(email__istartswith="bob").fetch_all()
print(f"\nEmails starting with 'bob': {len(bob_results)}")

db.close()
# --8<-- [end:case-insensitive]
```

### Case-Insensitive Operators

| Operator | Description |
|----------|-------------|
| `__istartswith` | Starts with (case-insensitive) |
| `__iendswith` | Ends with (case-insensitive) |
| `__icontains` | Contains (case-insensitive) |

### When to Use

- **Email domains**: Users might type "Example.COM" or "example.com"
- **Usernames**: Username searches should ignore case
- **General search**: More user-friendly search experience

## Performance Considerations

### Indexes

String filters (especially `contains` and `startswith`) can be slow on large datasets without proper indexing.

### Optimization Tips

1. **Use `startswith` instead of `contains`** when possible - can use indexes better
2. **Consider case-sensitive filters** - they're slightly faster
3. **Limit results** with `fetch_first()` or pagination on large datasets

### Example: Optimized Search

```python
# Instead of this (slower on large datasets):
results = db.select(User).filter(email__contains="@example.com").fetch_all()

# Use this when you know the format:
results = db.select(User).filter(email__endswith="@example.com").fetch_all()
```

## Operator Reference

| Operator | Case-Sensitive | Description | Example |
|----------|----------------|-------------|---------|
| `__startswith` | Yes | Starts with prefix | `name__startswith="Apple"` |
| `__endswith` | Yes | Ends with suffix | `email__endswith=".com"` |
| `__contains` | Yes | Contains substring | `desc__contains="phone"` |
| `__istartswith` | No | Starts with (ignore case) | `name__istartswith="apple"` |
| `__iendswith` | No | Ends with (ignore case) | `email__iendswith=".COM"` |
| `__icontains` | No | Contains (ignore case) | `desc__icontains="PHONE"` |

## Related Documentation

- [Filtering](filters.md) - Comparison operators for filtering
- [Query Results](results.md) - Fetch and paginate results
- [Ordering](ordering.md) - Sort query results
