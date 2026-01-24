# Auto Timestamp Demos

These demos show automatic timestamp tracking for records.

## Auto created_at

Track when records are created.

```python
# --8<-- [start:created-at]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Article(BaseDBModel):
    """Article with automatic creation timestamp."""
    title: str

db = SqliterDB(memory=True)
db.create_table(Article)

article1 = db.insert(Article(title="First Post"))
print(f"Created: {article1.created_at}")

# Slight delay for demonstration
import time
time.sleep(0.1)

article2 = db.insert(Article(title="Second Post"))
print(f"Created: {article2.created_at}")
```

### What It Does

- `created_at` field is automatically added to your model
- Set to current Unix timestamp when record is inserted
- Never changes after initial insert

### Field Type

`created_at` is stored as an integer (Unix timestamp in seconds).

## Auto updated_at

Track when records are last modified.

```python
# --8<-- [start:updated-at]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Task(BaseDBModel):
    """Task with automatic modification timestamp."""
    title: str
    done: bool = False

db = SqliterDB(memory=True)
db.create_table(Task)

task = db.insert(Task(title="Original Task"))
print(f"Updated: {task.updated_at}")

# Slight delay for demonstration
import time
time.sleep(1)

# Update the task
task.title = "Updated Task"
task.done = True
db.update(task)

# updated_at has changed
updated_task = db.get_by_pk(Task, task.pk)
print(f"Updated: {updated_task.updated_at}")
```

### How It Works

- `updated_at` starts same as `created_at`
- Automatically updated when you call `db.update()`
- Changes on every update operation

## Both Timestamps

Most models track both creation and modification times.

```python
# --8<-- [start:both-timestamps]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Document(BaseDBModel):
    """Document with both timestamps."""
    title: str
    content: str

db = SqliterDB(memory=True)
db.create_table(Document)

# Create document
doc = db.insert(Document(title="Draft", content="..."))
print(f"Created: {doc.created_at}")
print(f"Updated: {doc.updated_at}")

# Update document
doc.content = "Revised content"
db.update(doc)

# Check timestamps
print(f"Created: {doc.created_at}")  # Unchanged
print(f"Updated: {doc.updated_at}")  # Changed
```

## Converting Timestamps

Convert Unix timestamps to readable dates.

```python
# --8<-- [start:convert-timestamps]
from datetime import datetime, timezone

article = db.insert(Article(title="Test")))

# Convert to human-readable format
dt = datetime.fromtimestamp(article.created_at, tz=timezone.utc)
readable = dt.strftime("%Y-%m-%d %H:%M:%S")
print(f"Created: {article.created_at} ({readable} UTC)")
```

## When to Use Timestamps

### Audit Trails

Track when records were created and modified:

```python
class User(BaseDBModel):
    username: str
    # created_at and updated_at automatically added
```

### Synchronization

Determine if data needs to be synced:

```python
local_doc = db_local.get_by_pk(Document, doc_id)
remote_doc = db_remote.get_by_pk(Document, doc_id)

if remote_doc.updated_at > local_doc.updated_at:
    sync_document(remote_doc)
```

### Debugging

Understand the lifecycle of records:

```python
print(f"User created {datetime.now() - user.created_at} ago")
print(f"Last updated {datetime.now() - user.updated_at} ago")
```

### Soft Delete

Mark records as deleted instead of removing them:

```python
class Record(BaseDBModel):
    data: str
    deleted_at: Optional[int] = None  # Manual timestamp

def soft_delete(record: Record) -> None:
    record.deleted_at = int(time.time())
    db.update(record)
```

## Timestamp Precision

Unix timestamps are in **seconds** since the epoch (January 1, 1970).

### Limitations

- **Second precision**: No milliseconds/microseconds
- **Timezone naive**: Stored as UTC, convert for display
- **Year 2038**: 32-bit integer limit (not an issue for 64-bit)

### Example Values

```
1737739200 -> 2025-01-25 00:00:00 UTC
1737742800 -> 2025-01-25 01:00:00 UTC
```

## Comparing Timestamps

Find records by creation or modification time.

```python
# --8<-- [start:compare-timestamps]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel
import time

class LogEntry(BaseDBModel):
    message: str

db = SqliterDB(memory=True)
db.create_table(LogEntry)

# Insert entries at different times
entry1 = db.insert(LogEntry(message="First"))
time.sleep(1)
entry2 = db.insert(LogEntry(message="Second"))

# Find entries created after a certain time
cutoff = entry1.created_at
recent = db.select(LogEntry).filter(
    created_at__gt=cutoff
).fetch_all()
```

## Best Practices

### DO

- Use timestamps for audit trails
- Convert to readable format for display
- Store as UTC, convert to local time for users
- Use for synchronization checks

### DON'T

- Assume timestamps are in local time (they're UTC)
- Forget that precision is only in seconds
- Manually set timestamps (let SQLiter handle it)
- Use `created_at` for ordering by recency without understanding the limits

## Related Documentation

- [Models](models.md) - Define data models with timestamps
- [CRUD Operations](crud.md) - Update records (updates `updated_at`)
- [Filtering](filters.md) - Filter by timestamp values
