"""Auto Timestamp demos."""

from __future__ import annotations

import io
import time
from datetime import datetime, timezone

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
    dt1 = datetime.fromtimestamp(article1.created_at, tz=timezone.utc)
    formatted_dt1 = dt1.strftime("%Y-%m-%d %H:%M:%S")
    output.write(f"Article: {article1.title}\n")
    output.write(f"Created: {article1.created_at} ({formatted_dt1} UTC)\n")

    time.sleep(0.1)

    article2 = db.insert(Article(title="Second Post"))
    dt2 = datetime.fromtimestamp(article2.created_at, tz=timezone.utc)
    formatted_dt2 = dt2.strftime("%Y-%m-%d %H:%M:%S")
    output.write(f"\nArticle: {article2.title}\n")
    output.write(f"Created: {article2.created_at} ({formatted_dt2} UTC)\n")

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
    created_dt = datetime.fromtimestamp(task.created_at, tz=timezone.utc)
    updated_dt = datetime.fromtimestamp(task.updated_at, tz=timezone.utc)
    formatted_created_dt = created_dt.strftime("%Y-%m-%d %H:%M:%S")
    formatted_updated_dt = updated_dt.strftime("%Y-%m-%d %H:%M:%S")
    output.write(f"Task: {task.title}\n")
    output.write(f"Created: {task.created_at} ({formatted_created_dt} UTC)\n")
    output.write(f"Updated: {task.updated_at} ({formatted_updated_dt} UTC)\n")

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
    output.write("\nAfter update:\n")
    output.write(f"Title: {updated_task.title}\n")
    output.write(
        f"Created: {updated_task.created_at} "
        f"({formatted_updated_created_dt} UTC)\n"
    )
    output.write(
        f"Updated: {updated_task.updated_at} "
        f"({formatted_updated_updated_dt} UTC)\n"
    )

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
