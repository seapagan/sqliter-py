# Model Definition Demos

These demos show how to define data models using Pydantic with SQLiter.

## Basic Model

The simplest model definition with a primary key and string field.

```python
# --8<-- [start:basic-model]
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    """A simple user model."""
    name: str
    email: str
```

### What Happens Automatically
- **Primary Key**: `pk` field is automatically added as the primary key
- **Table Name**: Table name is automatically pluralized (`users` in this case)
- **Type Conversion**: Pydantic validates and converts types automatically

## Model with Defaults

Set default values for fields that are optional.

```python
# --8<-- [start:defaults]
from sqliter.model import BaseDBModel

class Task(BaseDBModel):
    """Task model with default values."""
    title: str
    completed: bool = False
    priority: int = 5
```

### Field Behavior
- Fields with defaults are optional when inserting
- If not provided, the default value is used
- You can override defaults by explicitly passing values

## Auto Timestamps

Automatically track when records are created and last modified.

```python
# --8<-- [start:timestamps]
from sqliter.model import BaseDBModel

class Article(BaseDBModel):
    """Article with automatic timestamps."""
    title: str
    content: str
```

### Auto-Generated Fields
- **`created_at`**: Unix timestamp set when the record is inserted
- **`updated_at`**: Unix timestamp updated automatically when the record is modified

## Field Types

SQLiter supports all Pydantic field types:

```python
# --8<-- [start:field-types]
from typing import List
from sqliter.model import BaseDBModel

class Product(BaseDBModel):
    """Product demonstrating various field types."""
    name: str                # String
    price: float             # Decimal number
    in_stock: bool           # Boolean
    quantity: int            # Integer
    tags: List[str]          # List (serialized as BLOB)
```

## Model Relationships

Define relationships between models using foreign keys.

```python
# --8<-- [start:relationships]
from sqliter.model import BaseDBModel, ForeignKey

class Author(BaseDBModel):
    """An author of books."""
    name: str

class Book(BaseDBModel):
    """A book with a foreign key to Author."""
    title: str
    author: ForeignKey[Author]
```

## Unique Fields

Ensure field values are unique across all records.

```python
# --8<-- [start:unique-fields]
from sqliter.model import BaseDBModel, unique

class User(BaseDBModel):
    """User with unique email."""
    username: unique(str)
    email: unique(str)
```

## Related Documentation

- [Database Connection](connection.md) - Connect to a database
- [CRUD Operations](crud.md) - Create and manipulate records
- [ORM Features](orm.md) - Work with model relationships
