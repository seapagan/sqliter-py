# Model Definition Demos

These demos show how to define data models using Pydantic with SQLiter.

## Basic Model

The simplest model definition with a primary key and string field.

```python
# --8<-- [start:basic-model]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    name: str
    age: int
    email: str

db = SqliterDB(memory=True)
db.create_table(User)

user = db.insert(User(name="Alice", age=30, email="alice@example.com"))
print(f"Created user: {user.name}")
print(f"Primary key: {user.pk}")
print(f"Age: {user.age}")
print(f"Email: {user.email}")

db.close()
# --8<-- [end:basic-model]
```

### What Happens Automatically

- **Primary Key**: `pk` field is automatically added as the primary key
- **Table Name**: Table name is automatically pluralized (`users` in this case)
- **Type Conversion**: Pydantic validates and converts types automatically

## Model with Defaults

Set default values for fields that are optional.

```python
# --8<-- [start:defaults]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Task(BaseDBModel):
    title: str
    completed: bool = False
    priority: int = 1

db = SqliterDB(memory=True)
db.create_table(Task)

task = db.insert(Task(title="New task"))
print(f"Task: {task.title}")
print(f"Completed: {task.completed} (default)")
print(f"Priority: {task.priority} (default)")

db.close()
# --8<-- [end:defaults]
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
from sqliter import SqliterDB
from sqliter.model import BaseDBModel
from datetime import datetime, timezone

class Product(BaseDBModel):
    name: str
    price: float
    in_stock: bool
    quantity: int
    created_at: int

db = SqliterDB(memory=True)
db.create_table(Product)

product = db.insert(
    Product(
        name="Widget",
        price=19.99,
        in_stock=True,
        quantity=100,
        created_at=int(datetime.now(timezone.utc).timestamp()),
    ),
)
print(f"Product: {product.name}")
print(f"Price: ${product.price}")
print(f"In stock: {product.in_stock}")
print(f"Quantity: {product.quantity}")
print(f"Created: {product.created_at}")

db.close()
# --8<-- [end:field-types]
```

## Model Relationships

Define relationships between models using foreign keys.

```python
# --8<-- [start:relationships]
from sqliter.model import BaseDBModel
from sqliter.orm.foreign_key import ForeignKey

class Author(BaseDBModel):
    """An author of books."""
    name: str

class Book(BaseDBModel):
    """A book with a foreign key to Author."""
    title: str
    author: ForeignKey[Author] = ForeignKey(Author)
```

## Complex Data Types

Store lists, dicts, and other complex types in your models.

```python
# --8<-- [start:unique-fields]
from typing import Union
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Document(BaseDBModel):
    title: str
    tags: list[str]
    metadata: dict[str, Union[str, int]]

db = SqliterDB(memory=True)
db.create_table(Document)

doc = db.insert(
    Document(
        title="Guide",
        tags=["python", "database", "tutorial"],
        metadata={"views": 1000, "rating": 4},
    ),
)
print(f"Document: {doc.title}")
print(f"Tags: {doc.tags}")
print(f"Metadata: {doc.metadata}")

db.close()
# --8<-- [end:unique-fields]
```

## Related Documentation

- [Database Connection](connection.md) - Connect to a database
- [CRUD Operations](crud.md) - Create and manipulate records
- [ORM Features](orm.md) - Work with model relationships
