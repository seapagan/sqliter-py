"""Demo execution engine with output capture."""

from __future__ import annotations

import io
import traceback
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass

from sqliter.tui.demos.base import Demo


@dataclass
class ExecutionResult:
    """Result of executing a demo.

    Attributes:
        success: Whether the demo ran without exceptions
        output: Combined stdout/stderr and returned output
        error: Exception message if failed
        traceback: Full traceback string if failed
    """

    success: bool
    output: str
    error: str | None = None
    traceback: str | None = None


class DemoRunner:
    """Executes demos and captures all output."""

    def __init__(self) -> None:
        """Initialize the demo runner."""
        self._last_result: ExecutionResult | None = None

    def run(self, demo: Demo) -> ExecutionResult:
        """Execute a demo and capture all output.

        Args:
            demo: The demo to execute.

        Returns:
            ExecutionResult with output and status.
        """
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                output = demo.execute()

            # Combine all output sources
            combined = ""
            stdout_val = stdout_capture.getvalue()
            stderr_val = stderr_capture.getvalue()

            if stdout_val:
                combined += stdout_val
            if output:
                if combined and not combined.endswith("\n"):
                    combined += "\n"
                combined += output
            if stderr_val:
                combined += f"\n[stderr]\n{stderr_val}"

            self._last_result = ExecutionResult(
                success=True,
                output=combined or "(No output)",
            )

        except Exception as e:
            tb = traceback.format_exc()
            self._last_result = ExecutionResult(
                success=False,
                output=stdout_capture.getvalue(),
                error=str(e),
                traceback=tb,
            )

        finally:
            # Run teardown if defined
            if demo.teardown:
                try:
                    demo.teardown()
                except Exception:
                    pass  # Ignore teardown errors

        return self._last_result

    @property
    def last_result(self) -> ExecutionResult | None:
        """Get the last execution result."""
        return self._last_result


# Global runner instance
_runner = DemoRunner()


def run_demo(demo: Demo) -> ExecutionResult:
    """Run a demo using the global runner."""
    return _runner.run(demo)
