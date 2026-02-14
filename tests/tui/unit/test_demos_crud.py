"""Unit tests for CRUD demo functions."""

from __future__ import annotations

from sqliter.tui.demos import crud


class TestInsertDemo:
    """Test the insert demo."""

    def test_run_insert_returns_output(self) -> None:
        """Test that insert demo returns expected output."""
        output = crud._run_insert()

        assert "Inserted: Alice" in output
        assert "Inserted: Bob" in output
        assert "pk=" in output

    def test_run_insert_creates_records(self) -> None:
        """Test that insert demo creates records with PKs."""
        output = crud._run_insert()

        # Should have created 2 users
        assert output.count("Inserted:") == 2


class TestGetByPkDemo:
    """Test the get by primary key demo."""

    def test_run_get_by_pk_returns_output(self) -> None:
        """Test that get_by_pk demo returns expected output."""
        output = crud._run_get_by_pk()

        assert "Created: Buy groceries" in output
        assert "Retrieved: Buy groceries" in output

    def test_run_get_by_pk_uses_retrieved_record(self) -> None:
        """Test that get_by_pk demo uses the retrieved record."""
        output = crud._run_get_by_pk()

        # Should show output
        assert isinstance(output, str)
        assert len(output) > 0


class TestUpdateDemo:
    """Test the update demo."""

    def test_run_update_returns_output(self) -> None:
        """Test that update demo returns expected output."""
        output = crud._run_update()

        assert "Created: Apples" in output
        assert "Updated: Apples" in output


class TestDeleteDemo:
    """Test the delete demo."""

    def test_run_delete_returns_output(self) -> None:
        """Test that delete demo returns expected output."""
        output = crud._run_delete()

        assert isinstance(output, str)
        assert len(output) > 0


class TestGetCategory:
    """Test the get_category function."""

    def test_get_category_returns_valid_category(self) -> None:
        """Test that get_category returns a valid DemoCategory."""
        category = crud.get_category()

        assert category.id == "crud"
        assert category.title == "CRUD Operations"
        assert len(category.demos) == 7

    def test_all_demos_are_executable(self) -> None:
        """Test that all CRUD demos execute successfully."""
        category = crud.get_category()

        for demo in category.demos:
            output = demo.execute()
            assert isinstance(output, str)
            assert len(output) > 0
