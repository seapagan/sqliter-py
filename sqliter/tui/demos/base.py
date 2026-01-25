"""Base classes for demo definitions."""

from __future__ import annotations

import inspect
import textwrap
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable


def extract_demo_code(func: Callable[..., str]) -> str:
    """Extract and format source code from a demo function.

    This function uses Python's inspect module to dynamically extract the
    source code from a demo function, ensuring the displayed code always
    matches what's actually executed.

    Removes demo infrastructure (function definition, output setup, return)
    but keeps the docstring for context.

    Args:
        func: The demo function to extract code from

    Returns:
        Formatted source code string with proper dedentation and whitespace
    """
    # Get the source code and split into lines
    source = inspect.getsource(func)
    lines = source.splitlines()

    # Skip decorator lines and function definition
    start_idx = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(("def ", "async def ")):
            start_idx = i + 1
            break
    lines = lines[start_idx:]

    # Dedent the remaining code
    code = textwrap.dedent("\n".join(lines))
    lines = code.splitlines()

    # Filter out unwanted lines
    filtered: list[str] = []
    for original_line in lines:
        # Skip output setup
        if "output = io.StringIO()" in original_line:
            continue
        # Rename output.write to print
        line = original_line
        if "output.write(" in line:
            line = line.replace("output.write(", "print(")
        # Stop at return statement
        if "return output.getvalue()" in line:
            break

        filtered.append(line)

    # Remove trailing empty lines
    while filtered and not filtered[-1].strip():
        filtered.pop()

    return "\n".join(filtered).strip()


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
    setup_code: Optional[str] = None
    teardown: Optional[Callable[[], None]] = None


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
