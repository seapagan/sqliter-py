"""Unit tests for transaction demo functions."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from sqliter.tui.demos import transactions
from sqliter.tui.demos.base import Demo

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


class TestContextManagerDemo:
    """Test the context manager demo."""

    def test_run_context_manager_transaction_returns_output(self) -> None:
        """Test that context manager demo returns expected output."""
        output = transactions._run_context_manager_transaction()

        assert "Before:" in output
        assert "After:" in output
        assert "Transaction auto-committed on success" in output


class TestRollbackDemo:
    """Test the rollback demo."""

    def test_run_rollback_returns_output(self) -> None:
        """Test that rollback demo returns expected output."""
        output = transactions._run_rollback()

        assert "Initial quantity: 10" in output
        assert "Inside transaction: updated to 5" in output
        assert "Error occurred - transaction rolled back" in output
        assert "Database value: 10" in output
        assert "✓ Rollback worked correctly" in output

    def test_run_rollback_handles_failed_rollback_case(
        self, mocker: MockerFixture
    ) -> None:
        """Test that rollback demo handles the case where rollback fails.

        This uses mocking to simulate the scenario where the database value
        doesn't match the expected value after rollback, forcing the else
        branch for coverage.
        """
        # Mock the SqliterDB class
        mock_db = MagicMock()
        mock_item = MagicMock()
        mock_item.pk = 1
        mock_item.quantity = 5  # Wrong value - rollback "failed"
        mock_db.get.return_value = mock_item

        # Patch SqliterDB to return our mock
        mocker.patch(
            "sqliter.tui.demos.transactions.SqliterDB", return_value=mock_db
        )

        # Run the demo
        output = transactions._run_rollback()

        # Should show the failure message
        assert "✗ Rollback failed: expected 10, got 5" in output


class TestManualCommitDemo:
    """Test the manual commit demo."""

    def test_run_manual_commit_returns_output(self) -> None:
        """Test that manual commit demo returns expected output."""
        output = transactions._run_manual_commit()

        assert "Inserted: First entry" in output
        assert "Not committed yet" in output
        assert "Committed" in output
        assert "Total logs: 2" in output


class TestGetCategory:
    """Test the get_category function."""

    def test_get_category_returns_valid_category(self) -> None:
        """Test that get_category returns a valid DemoCategory."""
        category = transactions.get_category()

        assert category.id == "transactions"
        assert category.title == "Transactions"
        assert len(category.demos) == 3

    def test_all_demos_are_executable(self) -> None:
        """Test that all transaction demos execute successfully."""
        category = transactions.get_category()

        for demo in category.demos:
            output = demo.execute()
            assert isinstance(output, str)
            assert len(output) > 0

    def test_demo_has_correct_metadata(self) -> None:
        """Test that all demos have required metadata."""
        category = transactions.get_category()

        for demo in category.demos:
            assert isinstance(demo, Demo)
            assert demo.id is not None
            assert demo.title is not None
            assert demo.description is not None
            assert demo.category == "transactions"
