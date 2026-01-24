"""Auto Timestamp demos."""

from __future__ import annotations

import io
import time

from sqliter.tui.demos.base import Demo, DemoCategory


def _run_created_at() -> str:
    """Execute the created_at demo."""
    output = io.StringIO()

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel

    class Article(BaseDBModel):
        title: str

    db = SqliterDB(memory=True)
    db.create_table(Article)

    article1 = db.insert(Article(title="First Post"))
    output.write(f"Article: {article1.title}\n")
    output.write(f"Created: {article1.created_at}\n")

    time.sleep(0.1)

    article2 = db.insert(Article(title="Second Post"))
    output.write(f"\nArticle: {article2.title}\n")
    output.write(f"Created: {article2.created_at}\n")

    db.close()
    return output.getvalue()


def _run_updated_at() -> str:
    """Execute the updated_at demo."""
    output = io.StringIO()

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel

    class Task(BaseDBModel):
        title: str
        done: bool = False

    db = SqliterDB(memory=True)
    db.create_table(Task)

    task = db.insert(Task(title="Original Task"))
    output.write(f"Task: {task.title}\n")
    output.write(f"Created: {task.created_at}\n")
    output.write(f"Updated: {task.updated_at}\n")

    time.sleep(0.1)

    updated_task = db.update(task, title="Updated Task", done=True)
    output.write(f"\nAfter update:\n")
    output.write(f"Title: {updated_task.title}\n")
    output.write(f"Created: {updated_task.created_at}\n")
    output.write(f"Updated: {updated_task.updated_at}\n")

    db.close()
    return output.getvalue()


CREATED_AT_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Article(BaseDBModel):
    title: str

db = SqliterDB(memory=True)
db.create_table(Article)

article = db.insert(Article(title="My Post"))

# Automatically set on creation
print(article.created_at)
"""

UPDATED_AT_CODE = """
from sqliter import SqliterDB
from sqliter.model import BaseDBModel

class Task(BaseDBModel):
    title: str
    done: bool = False

db = SqliterDB(memory=True)
db.create_table(Task)

task = db.insert(Task(title="Original"))

# Update the record
updated = db.update(task, title="Updated", done=True)

# Both timestamps are tracked
print(f"Created: {updated.created_at}")
print(f"Updated: {updated.updated_at}")
"""


def get_category() -> DemoCategory:
    """Get the Auto Timestamp demo category."""
    return DemoCategory(
        id="timestamps",
        title="Auto Timestamps",
        icon="",
        demos=[
            Demo(
                id="timestamp_created",
                title="Auto created_at",
                description="Track when records are created",
                category="timestamps",
                code=CREATED_AT_CODE,
                execute=_run_created_at,
            ),
            Demo(
                id="timestamp_updated",
                title="Auto updated_at",
                description="Track when records are modified",
                category="timestamps",
                code=UPDATED_AT_CODE,
                execute=_run_updated_at,
            ),
        ],
    )
