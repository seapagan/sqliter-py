"""Test cases for date and time conversion functions."""

import datetime

import pytest

from sqliter.helpers import from_unix_timestamp, to_unix_timestamp


class TestDates:
    """Test the data and time functionality."""

    def test_to_unix_timestamp_datetime_no_tz(self) -> None:
        """Test datetime without timezone conversion to UTC."""
        dt = datetime.datetime(  # noqa: DTZ001
            2023, 10, 20, 12, 0
        )  # Intentional Naive datetime, with no timezone info, so bite me Ruff!
        timestamp = to_unix_timestamp(dt)
        expected_timestamp = (
            datetime.datetime(2023, 10, 20, 12, 0)
            .astimezone(datetime.timezone.utc)
            .timestamp()
        )

        assert timestamp == int(expected_timestamp)

    def test_to_unix_timestamp_datetime_with_tz(self) -> None:
        """Test datetime with timezone conversion to UTC."""
        dt = datetime.datetime(
            2023,
            10,
            20,
            12,
            0,
            tzinfo=datetime.timezone(datetime.timedelta(hours=2)),
        )
        timestamp = to_unix_timestamp(dt)
        assert timestamp == 1697796000  # Adjusted to UTC (10:00 UTC)

    def test_to_unix_timestamp_date(self) -> None:
        """Test date conversion to Unix timestamp (midnight UTC)."""
        # Get the actual timestamp using the function (which stores as UTC)
        timestamp = to_unix_timestamp(datetime.date(2023, 10, 20))

        # Calculate expected timestamp for midnight UTC
        expected_timestamp = datetime.datetime(
            2023, 10, 20, 0, 0, tzinfo=datetime.timezone.utc
        ).timestamp()

        assert timestamp == int(expected_timestamp)

    def test_from_unix_timestamp_to_datetime_utc(self) -> None:
        """Test Unix timestamp to UTC datetime conversion."""
        timestamp = 1697803200  # 2023-10-20 12:00 UTC
        dt = from_unix_timestamp(timestamp, datetime.datetime, localize=False)
        assert dt == datetime.datetime(
            2023, 10, 20, 12, 0, tzinfo=datetime.timezone.utc
        )

    def test_from_unix_timestamp_to_datetime_localized(self) -> None:
        """Test Unix timestamp to localized datetime."""
        timestamp = 1697803200  # 2023-10-20 12:00 UTC

        # Assuming the local timezone is UTC-4 (eg, Eastern Daylight Time)
        dt = from_unix_timestamp(timestamp, datetime.datetime, localize=True)

        # The expected local time for UTC-4 is 2023-10-20 08:00:00-04:00
        expected_dt = datetime.datetime(
            2023,
            10,
            20,
            8,
            0,
            tzinfo=datetime.timezone(datetime.timedelta(hours=-4)),
        )

        assert dt == expected_dt

        timestamp = 1697803200  # 2023-10-20 12:00 UTC
        dt = from_unix_timestamp(timestamp, datetime.datetime, localize=True)
        assert dt == datetime.datetime(
            2023,
            10,
            20,
            8,
            0,
            tzinfo=datetime.timezone(datetime.timedelta(hours=-4)),
        )  # Localized to -4:00 (EDT)

    def test_from_unix_timestamp_to_date(self) -> None:
        """Test Unix timestamp to date conversion."""
        timestamp = 1697803200  # 2023-10-20 12:00 UTC
        d = from_unix_timestamp(timestamp, datetime.date)
        assert d == datetime.date(2023, 10, 20)

    def test_to_unix_timestamp_invalid_type(self) -> None:
        """Test invalid type for to_unix_timestamp."""
        with pytest.raises(TypeError):
            to_unix_timestamp("invalid_type")  # type: ignore # intentional error!

    def test_from_unix_timestamp_invalid_type(self) -> None:
        """Test invalid type for from_unix_timestamp."""
        with pytest.raises(TypeError):
            from_unix_timestamp(1697803200, str)
