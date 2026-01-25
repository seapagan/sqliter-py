# Auto Timestamp Demos

These demos show automatic timestamp tracking for records.

## Auto created_at

Track when records are created.

```python
# --8<-- [start:created-at]
from sqliter import SqliterDB
from sqliter.model import BaseDBModel
from datetime import datetime, timezone
import time

class Article(BaseDBModel):
    title: str

db = SqliterDB(memory=True)
db.create_table(Article)

article1 = db.insert(Article(title="First Post"))
dt1 = datetime.fromtimestamp(article1.created_at, tz=timezone.utc)
formatted_dt1 = dt1.strftime("%Y-%m-%d %H:%M:%S")
print(f"Article: {article1.title}")
print(f"Created: {article1.created_at} ({formatted_dt1} UTC)")

time.sleep(1)

article2 = db.insert(Article(title="Second Post"))
dt2 = datetime.fromtimestamp(article2.created_at, tz=timezone.utc)
formatted_dt2 = dt2.strftime("%Y-%m-%d %H:%M:%S")
print(f"\nArticle: {article2.title}")
print(f"Created: {article2.created_at} ({formatted_dt2} UTC)")

db.close()
# --8<-- [end:created-at]
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
from datetime import datetime, timezone
import time

class Task(BaseDBModel):
    title: str
    done: bool = False

db = SqliterDB(memory=True)
db.create_table(Task)

task = db.insert(Task(title="Original Task"))
created_dt = datetime.fromtimestamp(task.created_at, tz=timezone.utc)
updated_dt = datetime.fromtimestamp(task.updated_at, tz=timezone.utc)
formatted_created_dt = created_dt.strftime("%Y-%m-%d %H:%M:%S")
formatted_updated_dt = updated_dt.strftime("%Y-%m-%d %H:%M:%S")
print(f"Task: {task.title}")
print(f"Created: {task.created_at} ({formatted_created_dt} UTC)")
print(f"Updated: {task.updated_at} ({formatted_updated_dt} UTC)")

# Sleep for 1 second to ensure different timestamps on fast machines
time.sleep(1)

task.title = "Updated Task"
task.done = True
db.update(task)
updated_task = task
updated_created_dt = datetime.fromtimestamp(
    updated_task.created_at, tz=timezone.utc
)
updated_updated_dt = datetime.fromtimestamp(
    updated_task.updated_at, tz=timezone.utc
)
formatted_updated_created_dt = updated_created_dt.strftime(
    "%Y-%m-%d %H:%M:%S"
)
formatted_updated_updated_dt = updated_updated_dt.strftime(
    "%Y-%m-%d %H:%M:%S"
)
print("\nAfter update:")
print(f"Title: {updated_task.title}")
print(
    f"Created: {updated_task.created_at} "
    f"({formatted_updated_created_dt} UTC)"
)
print(
    f"Updated: {updated_task.updated_at} "
    f"({formatted_updated_updated_dt} UTC)"
)

db.close()
# --8<-- [end:updated-at]
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

db.close()
```

## Converting Timestamps

Convert Unix timestamps to readable dates.

```python
# --8<-- [start:convert-timestamps]
from datetime import datetime, timezone

from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Article(BaseDBModel):
    title: str

db = SqliterDB(memory=True)
db.create_table(Article)

article = db.insert(Article(title="Test"))

# Convert to human-readable format
dt = datetime.fromtimestamp(article.created_at, tz=timezone.utc)
readable = dt.strftime("%Y-%m-%d %H:%M:%S")
print(f"Created: {article.created_at} ({readable} UTC)")

db.close()
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
from datetime import datetime, timezone

now = datetime.now(tz=timezone.utc)
created = datetime.fromtimestamp(user.created_at, tz=timezone.utc)
updated = datetime.fromtimestamp(user.updated_at, tz=timezone.utc)
print(f"User created {now - created} ago")
print(f"Last updated {now - updated} ago")
```

### Soft Delete

Mark records as deleted instead of removing them:

```python
import time
from typing import Optional

from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Record(BaseDBModel):
    data: str
    deleted_at: Optional[int] = None  # Manual timestamp

db = SqliterDB(memory=True)
db.create_table(Record)

def soft_delete(record: Record) -> None:
    record.deleted_at = int(time.time())
    db.update(record)

# Example usage
record = db.insert(Record(data="Important data"))
soft_delete(record)
print(f"Record deleted at: {record.deleted_at}")

db.close()
```

## Timestamp Precision

Unix timestamps are in **seconds** since the epoch (January 1, 1970).

### Limitations

- **Second precision**: No milliseconds/microseconds
- **Timezone naive**: Stored as UTC, convert for display
- **Year 2038**: 32-bit integer limit (not an issue for 64-bit)

### Example Values

```text
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

db.close()
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
