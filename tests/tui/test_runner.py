"""Tests for the demo runner."""
# ruff : noqa: T201, PLC0415

from __future__ import annotations

from sqliter.tui.demos.base import Demo
from sqliter.tui.runner import DemoRunner, ExecutionResult, _runner, run_demo

# Error message constants for testing
DEMO_FAILED_ERROR = "Demo failed"
INNER_ERROR = "Inner error"
TEARDOWN_FAILED_ERROR = "Teardown failed"


class DemoTestError(Exception):
    """Custom exception for testing demo error handling."""


class TestExecutionResult:
    """Test the ExecutionResult dataclass."""

    def test_execution_result_creation_success(self) -> None:
        """Test creating a successful execution result."""
        result = ExecutionResult(
            success=True,
            output="Demo output",
        )

        assert result.success is True
        assert result.output == "Demo output"
        assert result.error is None
        assert result.traceback is None

    def test_execution_result_creation_failure(self) -> None:
        """Test creating a failed execution result."""
        result = ExecutionResult(
            success=False,
            output="Partial output",
            error="Exception occurred",
            traceback="Traceback...",
        )

        assert result.success is False
        assert result.output == "Partial output"
        assert result.error == "Exception occurred"
        assert result.traceback == "Traceback..."


class TestDemoRunner:
    """Test the DemoRunner class."""

    def test_successful_execution(self) -> None:
        """Test running a demo successfully."""
        demo = Demo(
            id="test",
            title="Test",
            description="Test",
            category="test",
            code="code",
            execute=lambda: "Demo output",
        )

        runner = DemoRunner()
        result = runner.run(demo)

        assert result.success is True
        assert result.output == "Demo output"
        assert result.error is None
        assert result.traceback is None

    def test_output_capture_stdout(self) -> None:
        """Test capturing stdout from demo."""

        def demo_func() -> str:
            print("Printed to stdout")
            return "Returned value"

        demo = Demo(
            id="test",
            title="Test",
            description="Test",
            category="test",
            code="code",
            execute=demo_func,
        )

        runner = DemoRunner()
        result = runner.run(demo)

        assert result.success is True
        assert "Printed to stdout" in result.output
        assert "Returned value" in result.output

    def test_stderr_capture(self) -> None:
        """Test capturing stderr from demo."""

        def demo_func() -> str:
            import sys

            print("Error message", file=sys.stderr)
            return "return"

        demo = Demo(
            id="test",
            title="Test",
            description="Test",
            category="test",
            code="code",
            execute=demo_func,
        )

        runner = DemoRunner()
        result = runner.run(demo)

        assert result.success is True
        assert "[stderr]" in result.output
        assert "Error message" in result.output

    def test_combined_output(self) -> None:
        """Test combining stdout, stderr, and return value."""

        def demo_func() -> str:
            print("stdout")
            import sys

            print("stderr", file=sys.stderr)
            return "return"

        demo = Demo(
            id="test",
            title="Test",
            description="Test",
            category="test",
            code="code",
            execute=demo_func,
        )

        runner = DemoRunner()
        result = runner.run(demo)

        assert result.success is True
        assert "stdout" in result.output
        assert "[stderr]" in result.output
        assert "stderr" in result.output
        assert "return" in result.output

    def test_stdout_and_return_value_separated_by_newline(
        self,
    ) -> None:
        """Test that stdout and return value are separated by newline."""

        def demo_func() -> str:
            # Print without newline to trigger the newline insertion
            print("stdout message", end="")
            return "return value"

        demo = Demo(
            id="test",
            title="Test",
            description="Test",
            category="test",
            code="code",
            execute=demo_func,
        )

        runner = DemoRunner()
        result = runner.run(demo)

        assert result.success is True
        # Output should contain both parts
        assert "stdout message" in result.output
        assert "return value" in result.output
        # The return value should be on a new line after stdout
        assert result.output == "stdout message\nreturn value"

    def test_exception_handling(self) -> None:
        """Test handling exceptions in demo code."""

        def failing_demo() -> str:
            raise DemoTestError(DEMO_FAILED_ERROR)

        demo = Demo(
            id="test",
            title="Test",
            description="Test",
            category="test",
            code="code",
            execute=failing_demo,
        )

        runner = DemoRunner()
        result = runner.run(demo)

        assert result.success is False
        assert result.error == "Exception in demo code"
        assert result.traceback is not None
        assert "DemoTestError" in result.traceback
        assert DEMO_FAILED_ERROR in result.traceback

    def test_exception_with_stderr(self) -> None:
        """Test that stderr is captured when demo raises exception."""

        def failing_demo_with_stderr() -> str:
            import sys

            print("Error from demo", file=sys.stderr)
            raise DemoTestError(DEMO_FAILED_ERROR)

        demo = Demo(
            id="test",
            title="Test",
            description="Test",
            category="test",
            code="code",
            execute=failing_demo_with_stderr,
        )

        runner = DemoRunner()
        result = runner.run(demo)

        assert result.success is False
        assert result.error == "Exception in demo code"
        assert result.traceback is not None
        # Verify stderr is included in error output
        assert "[stderr]" in result.output
        assert "Error from demo" in result.output

    def test_traceback_capture(self) -> None:
        """Test that full traceback is captured."""

        def failing_demo() -> str:
            def inner_function() -> None:
                raise DemoTestError(INNER_ERROR)

            inner_function()
            return "never reached"

        demo = Demo(
            id="test",
            title="Test",
            description="Test",
            category="test",
            code="code",
            execute=failing_demo,
        )

        runner = DemoRunner()
        result = runner.run(demo)

        assert result.success is False
        assert result.traceback is not None
        assert "inner_function" in result.traceback
        assert "DemoTestError" in result.traceback

    def test_teardown_execution(self) -> None:
        """Test that teardown is called after successful execution."""
        teardown_called = []

        def teardown() -> None:
            teardown_called.append(True)

        demo = Demo(
            id="test",
            title="Test",
            description="Test",
            category="test",
            code="code",
            execute=lambda: "success",
            teardown=teardown,
        )

        runner = DemoRunner()
        runner.run(demo)

        assert teardown_called == [True]

    def test_teardown_on_error(self) -> None:
        """Test that teardown is called even after exception."""
        teardown_called = []

        def teardown() -> None:
            teardown_called.append(True)

        def failing_demo() -> str:
            raise DemoTestError(DEMO_FAILED_ERROR)

        demo = Demo(
            id="test",
            title="Test",
            description="Test",
            category="test",
            code="code",
            execute=failing_demo,
            teardown=teardown,
        )

        runner = DemoRunner()
        runner.run(demo)

        assert teardown_called == [True]

    def test_teardown_error_suppressed(self) -> None:
        """Test that errors in teardown are suppressed."""

        def failing_teardown() -> None:
            raise DemoTestError(TEARDOWN_FAILED_ERROR)

        demo = Demo(
            id="test",
            title="Test",
            description="Test",
            category="test",
            code="code",
            execute=lambda: "success",
            teardown=failing_teardown,
        )

        runner = DemoRunner()
        # Should not raise exception
        result = runner.run(demo)

        # Demo itself should still be successful
        assert result.success is True

    def test_last_result_property(self) -> None:
        """Test that last_result stores the most recent result."""
        demo1 = Demo(
            id="test1",
            title="Test 1",
            description="Test",
            category="test",
            code="code",
            execute=lambda: "first",
        )
        demo2 = Demo(
            id="test2",
            title="Test 2",
            description="Test",
            category="test",
            code="code",
            execute=lambda: "second",
        )

        runner = DemoRunner()
        assert runner.last_result is None

        runner.run(demo1)
        assert runner.last_result is not None
        assert runner.last_result.output == "first"

        runner.run(demo2)
        assert runner.last_result.output == "second"

    def test_no_output_placeholder(self) -> None:
        """Test that demos with no output show placeholder."""
        demo = Demo(
            id="test",
            title="Test",
            description="Test",
            category="test",
            code="code",
            execute=lambda: "",
        )

        runner = DemoRunner()
        result = runner.run(demo)

        assert result.success is True
        assert result.output == "(No output)"

    def test_empty_string_output(self) -> None:
        """Test handling of empty string output."""
        demo = Demo(
            id="test",
            title="Test",
            description="Test",
            category="test",
            code="code",
            execute=lambda: "",
        )

        runner = DemoRunner()
        result = runner.run(demo)

        assert result.success is True
        assert result.output == "(No output)"


class TestGlobalRunner:
    """Test the global runner instance."""

    def test_run_demo_function(self) -> None:
        """Test the run_demo convenience function."""
        demo = Demo(
            id="test",
            title="Test",
            description="Test",
            category="test",
            code="code",
            execute=lambda: "global runner output",
        )

        result = run_demo(demo)

        assert result.success is True
        assert result.output == "global runner output"

    def test_global_runner_persistence(self) -> None:
        """Test that global runner maintains state."""
        demo1 = Demo(
            id="test1",
            title="Test 1",
            description="Test",
            category="test",
            code="code",
            execute=lambda: "first",
        )
        demo2 = Demo(
            id="test2",
            title="Test 2",
            description="Test",
            category="test",
            code="code",
            execute=lambda: "second",
        )

        # Import the global runner
        run_demo(demo1)
        assert _runner.last_result is not None
        assert _runner.last_result.output == "first"

        run_demo(demo2)
        assert _runner.last_result.output == "second"
