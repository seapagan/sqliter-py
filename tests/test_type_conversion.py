"""Test serialization and deserialization of complex types."""

from datetime import date, datetime, timezone
from typing import Any

from pytest_mock import MockerFixture

from sqliter.model import BaseDBModel


class TestTypeConversion:
    """Test class for complex type conversion in BaseDBModel."""

    def test_serialize_datetime(self, mocker: MockerFixture) -> None:
        """Test serialization of datetime objects."""
        # Mock timezone-aware datetime
        dt = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
        expected_timestamp = 1704110400  # Known timestamp for this datetime

        model = BaseDBModel()
        result = model.serialize_field(dt)

        assert result == expected_timestamp

    def test_serialize_naive_datetime(self, mocker: MockerFixture) -> None:
        """Test serialization of naive datetime objects."""
        # Create a naive datetime
        dt = datetime(2024, 1, 1, 12, 0)  # noqa: DTZ001 # this is intentional
        expected_timestamp = int(dt.astimezone().timestamp())

        model = BaseDBModel()
        result = model.serialize_field(dt)

        assert result == expected_timestamp

    def test_serialize_date(self) -> None:
        """Test serialization of date objects."""
        test_date = date(2024, 1, 1)
        expected_timestamp = 1704067200  # Midnight UTC on 2024-01-01

        model = BaseDBModel()
        result = model.serialize_field(test_date)

        assert result == expected_timestamp

    def test_serialize_non_date_types(self) -> None:
        """Test serialization of non-date types returns original value."""
        test_values: list[Any] = [42, "test string", True, None, 3.14]

        model = BaseDBModel()
        for value in test_values:
            result = model.serialize_field(value)
            assert result == value

    def test_deserialize_to_datetime_utc(self) -> None:
        """Test deserialization of timestamp to UTC datetime."""
        timestamp = 1704110400  # 2024-01-01 12:00:00 UTC
        initial_dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)

        class TestModel(BaseDBModel):
            test_field: datetime
            name: str

        model = TestModel(test_field=initial_dt, name="test")
        result = model.deserialize_field(
            "test_field", timestamp, return_local_time=False
        )

        assert result == datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)

    def test_deserialize_to_datetime_local(self) -> None:
        """Test deserialization of timestamp to local datetime."""
        timestamp = 1704110400  # 2024-01-01 12:00:00 UTC
        initial_dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)

        class TestModel(BaseDBModel):
            test_field: datetime
            name: str

        model = TestModel(test_field=initial_dt, name="test")
        result = model.deserialize_field(
            "test_field", timestamp, return_local_time=True
        )

        assert isinstance(result, datetime)
        assert result.tzinfo is not None  # Should have timezone info
        assert (
            result.timestamp() == timestamp
        )  # Should represent same moment in time

    def test_deserialize_to_date(self) -> None:
        """Test deserialization of timestamp to date."""
        timestamp = 1704067200  # 2024-01-01 00:00:00 UTC
        initial_date = date(2024, 1, 1)

        class TestModel(BaseDBModel):
            test_field: date
            name: str

        model = TestModel(test_field=initial_date, name="test")
        result = model.deserialize_field(
            "test_field", timestamp, return_local_time=True
        )

        assert result == date(2024, 1, 1)

    def test_deserialize_non_timestamp_values(self) -> None:
        """Test deserialization of non-timestamp returns original value."""
        test_values: list[Any] = [42, "test string", True, None, 3.14]

        model = BaseDBModel()
        for value in test_values:
            result = model.deserialize_field(
                "test_field", value, return_local_time=True
            )
            assert result == value
