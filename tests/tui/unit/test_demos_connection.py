"""Unit tests for connection demo functions.

These tests directly call the demo execution functions to verify they work
correctly without needing to run the full TUI application.
"""

from __future__ import annotations

from sqliter.tui.demos import connection


class TestMemoryDbDemo:
    """Test the in-memory database demo."""

    def test_run_memory_db_returns_output(self) -> None:
        """Test that memory demo returns expected output."""
        output = connection._run_memory_db()

        assert "Created database:" in output
        assert "Is memory: True" in output
        assert "Filename: None" in output
        assert "Connected: True" in output
        assert "After close: False" in output

    def test_run_memory_db_creates_connection(self) -> None:
        """Test that memory demo creates a working database."""
        output = connection._run_memory_db()

        # Verify the demo runs without error
        assert isinstance(output, str)
        assert len(output) > 0


class TestFileDbDemo:
    """Test the file-based database demo."""

    def test_run_file_db_returns_output(self) -> None:
        """Test that file demo returns expected output."""
        output = connection._run_file_db()

        assert "Created file database" in output
        assert "Filename:" in output
        assert "Is memory: False" in output
        assert "Connected to:" in output
        assert "Cleaned up database file" in output

    def test_run_file_db_creates_and_cleans_temp_file(self) -> None:
        """Test that file demo properly cleans up temp file."""
        output = connection._run_file_db()

        # Verify the demo runs without error and cleans up
        assert isinstance(output, str)
        assert "Cleaned up" in output


class TestDebugModeDemo:
    """Test the debug mode demo."""

    def test_run_debug_mode_returns_output(self) -> None:
        """Test that debug mode demo returns expected output."""
        output = connection._run_debug_mode()

        assert "Debug mode enables SQL query logging" in output
        assert "When debug=True" in output
        assert "SQL queries would be logged" in output


class TestContextManagerDemo:
    """Test the context manager demo."""

    def test_run_context_manager_returns_output(self) -> None:
        """Test that context manager demo returns expected output."""
        output = connection._run_context_manager()

        assert "Using context manager for transactions" in output
        assert "Inserted:" in output
        assert "Transaction auto-commits on exit" in output
        assert "After context:" in output

    def test_context_manager_creates_task(self) -> None:
        """Test that context manager demo creates a task."""
        output = connection._run_context_manager()

        # Should have inserted a task
        assert "Learn SQLiter" in output


class TestGetCategory:
    """Test the get_category function."""

    def test_get_category_returns_valid_category(self) -> None:
        """Test that get_category returns a valid DemoCategory."""
        category = connection.get_category()

        assert category.id == "connection"
        assert category.title == "Connection & Setup"
        assert category.icon == ""
        assert len(category.demos) == 4

    def test_get_category_demos_have_required_fields(self) -> None:
        """Test that all demos have required fields."""
        category = connection.get_category()

        for demo in category.demos:
            assert demo.id
            assert demo.title
            assert demo.description
            assert demo.category == "connection"
            assert demo.code
            assert callable(demo.execute)

    def test_all_demos_are_executable(self) -> None:
        """Test that all demo execute functions work."""
        category = connection.get_category()

        for demo in category.demos:
            output = demo.execute()
            assert isinstance(output, str)
            assert len(output) > 0
