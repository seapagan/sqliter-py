"""Base classes for demo definitions."""

from __future__ import annotations

import inspect
import textwrap
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable


def extract_demo_code(func: Callable[..., str]) -> str:
    """Extract and format source code from a demo function.

    This function uses Python's inspect module to dynamically extract the
    source code from a demo function, ensuring the displayed code always
    matches what's actually executed.

    Args:
        func: The demo function to extract code from

    Returns:
        Formatted source code string with proper dedentation and whitespace
    """
    # Get the source code, dedent, and strip whitespace in one expression
    return textwrap.dedent(inspect.getsource(func)).strip()


__all__ = ["Demo", "DemoCategory", "extract_demo_code"]


@dataclass
class Demo:
    """Represents a single demo example.

    Attributes:
        id: Unique identifier for the demo (e.g., "conn_memory")
        title: Display title in the list (e.g., "In-memory Database")
        description: Brief description shown as tooltip/subtitle
        category: Category ID this demo belongs to
        code: The Python code to display (syntax highlighted)
        execute: Callable that runs the demo and returns output string
        setup_code: Optional setup code shown before main code
        teardown: Optional cleanup function called after execution
    """

    id: str
    title: str
    description: str
    category: str
    code: str
    execute: Callable[[], str]
    setup_code: str | None = None
    teardown: Callable[[], None] | None = None


@dataclass
class DemoCategory:
    """A category of related demos.

    Attributes:
        id: Unique identifier (e.g., "connection")
        title: Display title (e.g., "Connection & Setup")
        icon: Optional emoji icon for the category
        demos: List of demos in this category
        expanded: Whether category starts expanded in the tree
    """

    id: str
    title: str
    icon: str = ""
    demos: list[Demo] = field(default_factory=list)
    expanded: bool = False
