# Quick Start

Here's a quick example of how to use SQLiter:

```python
from typing import Optional

from sqliter import SqliterDB
from sqliter.model import BaseDBModel

# Define your model
class User(BaseDBModel):
    name: str
    age: int
    admin: Optional[bool] = False

    class Meta:
        create_pk = False
        primary_key = "name"

# Create a database connection
db = SqliterDB("example.db")

# Create the table
db.create_table(User)

# Insert a record
user = User(name="John Doe", age=30)
db.insert(user)

# Query records
results = db.select(User).filter(name="John Doe").fetch_all()
for user in results:
    print(f"User: {user.name}, Age: {user.age}, Admin: {user.admin}")

# Update a record
user.age = 31
db.update(user)

# Delete a record
db.delete(User, "John Doe")
```

See the [Guide](guide/guide.md) for more detailed information on how to use `SQLiter`.
