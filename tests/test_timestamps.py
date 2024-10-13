"""Class to test the `created_at` and `updated_at` timestamps."""

from tests.conftest import ExampleModel


class TestTimestamps:
    """Test the `created_at` and `updated_at` timestamps."""

    def test_insert_timestamps(self, db_mock, mocker) -> None:
        """Test both timestamps are set on record insert."""
        # Mock time.time() to return a fixed timestamp
        mocker.patch("time.time", return_value=1234567890)

        new_instance = ExampleModel(
            slug="test", name="Test", content="Test content"
        )

        # Perform the insert operation
        returned_instance = db_mock.insert(new_instance)

        # Assert that both created_at and updated_at are set to the mocked
        # timestamp
        assert returned_instance.created_at == 1234567890
        assert returned_instance.updated_at == 1234567890

    def test_update_timestamps(self, db_mock, mocker) -> None:
        """Test that the `updated_at` timestamp is updated on record update."""
        # Mock time.time() to return a fixed timestamp for the update
        mocker.patch("time.time", return_value=1234567890)

        new_instance = ExampleModel(
            slug="test", name="Test", content="Test content"
        )

        # Perform the insert operation
        returned_instance = db_mock.insert(new_instance)

        mocker.patch("time.time", return_value=1234567891)

        # Perform the update operation
        db_mock.update(returned_instance)

        # Assert that created_at remains the same and updated_at changes to the
        # new mocked value
        assert (
            returned_instance.created_at == 1234567890
        )  # Should remain unchanged
        assert (
            returned_instance.updated_at == 1234567891
        )  # Should be updated to the new timestamp
