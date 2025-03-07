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

# Create a database connection
db = SqliterDB("example.db")

# Create the table
db.create_table(User)

# Insert a record
user = User(name="John Doe", age=30)
new_user = db.insert(user)

# Query records
results = db.select(User).filter(name="John Doe").fetch_all()
for user in results:
    print(f"User: {user.name}, Age: {user.age}, Admin: {user.admin}")

# Update a record
new_user.age = 31
db.update(new_user)

results = db.select(User).filter(name="John Doe").fetch_one()

print("Updated age:", results.age)

# Delete a record by primary key
db.delete(User, new_user.pk)

# Delete all records returned from a query:
delete_count = db.select(User).filter(age__gt=30).delete()
```

See the [Guide](guide/guide.md) for more detailed information on how to use
`SQLiter`.
