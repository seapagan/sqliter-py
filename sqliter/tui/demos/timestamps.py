"""Auto Timestamp demos."""

from __future__ import annotations

import io
import time

from sqliter import SqliterDB
from sqliter.model import BaseDBModel
from sqliter.tui.demos.base import Demo, DemoCategory, extract_demo_code


def _run_created_at() -> str:
    """Automatically track when records are created.

    The created_at field is set automatically when you insert a record.
    """
    output = io.StringIO()

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
    """Automatically track when records are last modified.

    The updated_at field changes automatically when you update a record.
    """
    output = io.StringIO()

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

    task.title = "Updated Task"
    task.done = True
    db.update(task)
    updated_task = task
    output.write("\nAfter update:\n")
    output.write(f"Title: {updated_task.title}\n")
    output.write(f"Created: {updated_task.created_at}\n")
    output.write(f"Updated: {updated_task.updated_at}\n")

    db.close()
    return output.getvalue()


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
                code=extract_demo_code(_run_created_at),
                execute=_run_created_at,
            ),
            Demo(
                id="timestamp_updated",
                title="Auto updated_at",
                description="Track when records are modified",
                category="timestamps",
                code=extract_demo_code(_run_updated_at),
                execute=_run_updated_at,
            ),
        ],
    )
