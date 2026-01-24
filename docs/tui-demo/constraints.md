# Constraint Demos

These demos show how to define database constraints.

## Unique Fields

Ensure values in a field are unique across all records.

```python
# --8<-- [start:unique-field]
from sqliter.model import BaseDBModel, unique

class User(BaseDBModel):
    """User with unique username and email."""
    username: unique(str)
    email: unique(str)
```

### What It Does
- Creates a `UNIQUE` constraint in the database
- Database prevents duplicate values
- Query fails with error if you try to insert a duplicate

### When to Use
- **Usernames**: No two users can have the same username
- **Emails**: Prevent duplicate email registrations
- **Slugs**: Unique URL identifiers
- **Codes**: Unique coupon/promo codes

## Primary Key

Every model automatically gets a primary key field.

```python
# --8<-- [start:primary-key]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Product(BaseDBModel):
    """Product with auto-generated primary key."""
    name: str
    price: float

db = SqliterDB(memory=True)
db.create_table(Product)

product = db.insert(Product(name="Widget", price=10.0))
print(f"Primary key: {product.pk}")  # Auto-generated
```

### Automatic Behavior
- Field named `pk` is automatically added
- Auto-increments with each insert
- Guaranteed unique for each record
- Used by `get_by_pk()` and foreign keys

### Don't Define Your Own
```python
# ❌ WRONG: Don't do this
class User(BaseDBModel):
    id: int  # Conflicts with auto-generated pk

# ✅ CORRECT: Let SQLiter handle it
class User(BaseDBModel):
    name: str
```

## Not Null Constraints

Fields without defaults are implicitly NOT NULL.

```python
# --8<-- [start:not-null]
from sqliter.model import BaseDBModel
from typing import Optional

class Task(BaseDBModel):
    """Task with required and optional fields."""
    title: str  # Required (NOT NULL)
    description: Optional[str] = None  # Optional (can be NULL)
```

### Field Behavior
- **Required fields**: Must be provided when inserting
- **Optional fields**: Can be omitted, default to `None` or specified default

### Insert Behavior
```python
# ✅ Works: title is provided
db.insert(Task(title="Buy groceries"))

# ❌ Fails: title is required
db.insert(Task(description="Some task"))
```

## Default Values

Set default values for optional fields.

```python
# --8<-- [start:default-values]
from sqliter.model import BaseDBModel

class Settings(BaseDBModel):
    """Settings with default values."""
    theme: str = "dark"
    notifications_enabled: bool = True
    items_per_page: int = 20
```

### When Inserting
```python
# All defaults used
settings1 = db.insert(Settings())

# Override some defaults
settings2 = db.insert(Settings(theme="light"))

# Override all defaults
settings3 = db.insert(Settings(
    theme="light",
    notifications_enabled=False,
    items_per_page=50
))
```

## Check Constraints

Validate field values using Pydantic validators.

```python
# --8<-- [start:check-constraint]
from sqliter.model import BaseDBModel
from pydantic import field_validator

class Product(BaseDBModel):
    """Product with price validation."""
    name: str
    price: float

    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("Price must be positive")
        return value
```

### How It Works
- Pydantic validates before database insert
- Prevents invalid data from being stored
- Returns helpful error messages

## Constraint Summary

| Constraint | How to Define | Purpose |
|------------|---------------|---------|
| **Primary Key** | Automatic (`pk` field) | Unique identifier for each record |
| **Unique** | `unique(str)` | Field values must be unique |
| **Not Null** | No default value | Field must have a value |
| **Default Value** | `field: type = value` | Default value if not provided |
| **Check** | Pydantic validator | Custom validation logic |

## Error Handling

When constraints are violated:

```python
# --8<-- [start:error-handling]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel, unique
from sqliter.exceptions import IntegrityError

class User(BaseDBModel):
    username: unique(str)

db = SqliterDB(memory=True)
db.create_table(User)

# Insert first user
db.insert(User(username="alice"))

# Try to insert duplicate
try:
    db.insert(User(username="alice"))
except IntegrityError as e:
    print(f"Error: {e}")
```

## Best Practices

### DO:
- Use `unique()` for fields that must be unique
- Provide sensible defaults for optional fields
- Use Pydantic validators for complex constraints
- Handle `IntegrityError` for constraint violations

### DON'T:
- Define your own primary key field
- Forget that fields without defaults are required
- Use check constraints for simple validation (use Pydantic)

## Related Documentation

- [Models](models.md) - Define your data models
- [Error Handling](errors.md) - Handle constraint violations
- [CRUD Operations](crud.md) - Insert and update records
