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

    def test_insert_with_provided_timestamps(self, db_mock, mocker) -> None:
        """Test that user-provided timestamps are respected on insert."""
        # Mock time.time() to return a fixed timestamp
        mocker.patch("time.time", return_value=1234567890)

        # User-provided timestamps
        new_instance = ExampleModel(
            slug="test",
            name="Test",
            content="Test content",
            created_at=1111111111,  # User-provided
            updated_at=1111111111,  # User-provided
        )

        # Perform the insert operation
        returned_instance = db_mock.insert(
            new_instance, timestamp_override=True
        )

        # Assert that the user-provided timestamps are respected
        assert returned_instance.created_at == 1111111111
        assert returned_instance.updated_at == 1111111111

    def test_insert_with_default_timestamps(self, db_mock, mocker) -> None:
        """Test that timestamps are set when created_at and updated_at are 0."""
        # Mock time.time() to return a fixed timestamp
        mocker.patch("time.time", return_value=1234567890)

        # Create instance with default (0) timestamps
        new_instance = ExampleModel(
            slug="test",
            name="Test",
            content="Test content",
            created_at=0,
            updated_at=0,
        )

        # Perform the insert operation
        returned_instance = db_mock.insert(new_instance)

        # Assert that timestamps are set to the mocked time
        assert returned_instance.created_at == 1234567890
        assert returned_instance.updated_at == 1234567890

    def test_insert_with_mixed_timestamps(self, db_mock, mocker) -> None:
        """Test a mix of user-provided and default timestamps work on insert."""
        # Mock time.time() to return a fixed timestamp
        mocker.patch("time.time", return_value=1234567890)

        # Provide only created_at, leave updated_at as 0
        new_instance = ExampleModel(
            slug="test",
            name="Test",
            content="Test content",
            created_at=1111111111,  # User-provided
            updated_at=0,  # Default to current time
        )

        # Perform the insert operation
        returned_instance = db_mock.insert(
            new_instance, timestamp_override=True
        )

        # Assert that created_at is respected, and updated_at is set to the
        # current time
        assert returned_instance.created_at == 1111111111
        assert returned_instance.updated_at == 1234567890

    def test_update_timestamps_on_change(self, db_mock, mocker) -> None:
        """Test that only `updated_at` changes on update."""
        # Mock time.time() to return a fixed timestamp for the insert
        mocker.patch("time.time", return_value=1234567890)

        # Insert a new record
        new_instance = ExampleModel(
            slug="test", name="Test", content="Test content"
        )
        returned_instance = db_mock.insert(new_instance)

        # Mock time.time() to return a new timestamp for the update
        mocker.patch("time.time", return_value=1234567891)

        # Update the record
        returned_instance.name = "Updated Test"
        db_mock.update(returned_instance)

        # Assert that created_at stays the same and updated_at is changed
        assert returned_instance.created_at == 1234567890
        assert returned_instance.updated_at == 1234567891

    def test_no_change_if_timestamps_already_set(self, db_mock, mocker) -> None:
        """Test timestamps are not modified if already set during insert."""
        # Mock time.time() to return a fixed timestamp
        mocker.patch("time.time", return_value=1234567890)

        # User provides both timestamps
        new_instance = ExampleModel(
            slug="test",
            name="Test",
            content="Test content",
            created_at=1111111111,  # Already set
            updated_at=1111111111,  # Already set
        )

        # Perform the insert operation
        returned_instance = db_mock.insert(
            new_instance, timestamp_override=True
        )

        # Assert that timestamps are not modified
        assert returned_instance.created_at == 1111111111
        assert returned_instance.updated_at == 1111111111

    def test_override_but_no_timestamps_provided(self, db_mock, mocker) -> None:
        """Test missing timestamps always set to current time.

        Even with `timestamp_override=True`.
        """
        # Mock time.time() to return a fixed timestamp
        mocker.patch("time.time", return_value=1234567890)

        # User provides `0` for both timestamps, expecting them to be overridden
        new_instance = ExampleModel(
            slug="test",
            name="Test",
            content="Test content",
            created_at=0,  # Should default to current time
            updated_at=0,  # Should default to current time
        )

        # Perform the insert with timestamp_override=True
        returned_instance = db_mock.insert(
            new_instance, timestamp_override=True
        )

        # Assert that both timestamps are set to the current time, ignoring the
        # `0`
        assert returned_instance.created_at == 1234567890
        assert returned_instance.updated_at == 1234567890

    def test_partial_override_with_zero(self, db_mock, mocker) -> None:
        """Test changing `updated_at` only on create.

        When `timestamp_override=True
        """
        # Mock time.time() to return a fixed timestamp
        mocker.patch("time.time", return_value=1234567890)

        # User provides `created_at`, but leaves `updated_at` as 0
        new_instance = ExampleModel(
            slug="test",
            name="Test",
            content="Test content",
            created_at=1111111111,  # Provided by the user
            updated_at=0,  # Should be set to current time
        )

        # Perform the insert operation with timestamp_override=True
        returned_instance = db_mock.insert(
            new_instance, timestamp_override=True
        )

        # Assert that `created_at` is respected, and `updated_at` is set to the
        # current time
        assert returned_instance.created_at == 1111111111
        assert returned_instance.updated_at == 1234567890

    def test_insert_with_override_disabled(self, db_mock, mocker) -> None:
        """Test that timestamp_override=False ignores provided timestamps."""
        # Mock time.time() to return a fixed timestamp
        mocker.patch("time.time", return_value=1234567890)

        # User provides both timestamps, but they should be ignored
        new_instance = ExampleModel(
            slug="test",
            name="Test",
            content="Test content",
            created_at=1111111111,  # Should be ignored
            updated_at=1111111111,  # Should be ignored
        )

        # Perform the insert with timestamp_override=False (default)
        returned_instance = db_mock.insert(
            new_instance, timestamp_override=False
        )

        # Assert that both timestamps are set to the mocked current time
        assert returned_instance.created_at == 1234567890
        assert returned_instance.updated_at == 1234567890
