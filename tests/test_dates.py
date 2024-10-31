"""Test cases for date and time conversion functions."""

from datetime import date, datetime, timedelta, timezone

import pytest

from sqliter.helpers import from_unix_timestamp, to_unix_timestamp
from sqliter.model.model import BaseDBModel


class TestDates:
    """Test the data and time functionality."""

    def test_to_unix_timestamp_datetime_no_tz(self) -> None:
        """Test datetime without timezone conversion to UTC."""
        dt = datetime(  # noqa: DTZ001
            2023, 10, 20, 12, 0
        )  # Intentional Naive datetime, with no timezone info, so bite me Ruff!
        timestamp = to_unix_timestamp(dt)
        expected_timestamp = (
            datetime(2023, 10, 20, 12, 0).astimezone(timezone.utc).timestamp()
        )

        assert timestamp == int(expected_timestamp)

    def test_to_unix_timestamp_datetime_with_tz(self) -> None:
        """Test datetime with timezone conversion to UTC."""
        dt = datetime(
            2023,
            10,
            20,
            12,
            0,
            tzinfo=timezone(timedelta(hours=2)),
        )
        timestamp = to_unix_timestamp(dt)
        assert timestamp == 1697796000  # Adjusted to UTC (10:00 UTC)

    def test_to_unix_timestamp_date(self) -> None:
        """Test date conversion to Unix timestamp (midnight UTC)."""
        # Get the actual timestamp using the function (which stores as UTC)
        timestamp = to_unix_timestamp(date(2023, 10, 20))

        # Calculate expected timestamp for midnight UTC
        expected_timestamp = datetime(
            2023, 10, 20, 0, 0, tzinfo=timezone.utc
        ).timestamp()

        assert timestamp == int(expected_timestamp)

    def test_from_unix_timestamp_to_datetime_utc(self) -> None:
        """Test Unix timestamp to UTC datetime conversion."""
        timestamp = 1697803200  # 2023-10-20 12:00 UTC
        dt = from_unix_timestamp(timestamp, datetime, localize=False)
        assert dt == datetime(2023, 10, 20, 12, 0, tzinfo=timezone.utc)

    def test_from_unix_timestamp_to_datetime_localized(self) -> None:
        """Test Unix timestamp to localized datetime."""
        timestamp = 1697803200  # 2023-10-20 12:00 UTC

        # Assuming the local timezone is UTC-4 (eg, Eastern Daylight Time)
        dt = from_unix_timestamp(timestamp, datetime, localize=True)

        # The expected local time for UTC-4 is 2023-10-20 08:00:00-04:00
        expected_dt = datetime(
            2023,
            10,
            20,
            8,
            0,
            tzinfo=timezone(timedelta(hours=-4)),
        )

        assert dt == expected_dt

        timestamp = 1697803200  # 2023-10-20 12:00 UTC
        dt = from_unix_timestamp(timestamp, datetime, localize=True)
        assert dt == datetime(
            2023,
            10,
            20,
            8,
            0,
            tzinfo=timezone(timedelta(hours=-4)),
        )  # Localized to -4:00 (EDT)

    def test_from_unix_timestamp_to_date(self) -> None:
        """Test Unix timestamp to date conversion."""
        timestamp = 1697803200  # 2023-10-20 12:00 UTC
        d = from_unix_timestamp(timestamp, date)
        assert d == date(2023, 10, 20)

    def test_to_unix_timestamp_invalid_type(self) -> None:
        """Test invalid type for to_unix_timestamp."""
        with pytest.raises(TypeError):
            to_unix_timestamp("invalid_type")  # type: ignore # intentional error!

    def test_from_unix_timestamp_invalid_type(self) -> None:
        """Test invalid type for from_unix_timestamp."""
        with pytest.raises(TypeError):
            from_unix_timestamp(1697803200, str)

    def test_date_fields_create_integer_columns(self, db_mock) -> None:
        """Test that date & datetime fields create INTEGER columns in SQLite."""

        class DateModel(BaseDBModel):
            name: str
            date_field: date
            datetime_field: datetime

            class Meta:
                table_name = "date_test_table"

        # Create the table
        db_mock.create_table(DateModel)

        # Query the SQLite schema to check column types
        with db_mock.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(date_test_table);")
            columns = {
                row[1]: row[2] for row in cursor.fetchall()
            }  # name: type

        assert columns["date_field"] == "INTEGER"
        assert columns["datetime_field"] == "INTEGER"

    def test_date_field_roundtrip(self, db_mock) -> None:
        """Test that dates survive a round trip to and from the database."""
        test_datetime = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
        test_date = date(2024, 1, 1)

        class DateModel(BaseDBModel):
            name: str
            date_field: date
            datetime_field: datetime

            class Meta:
                table_name = "date_roundtrip_table"

        # Create and insert a record
        model = DateModel(
            name="test", date_field=test_date, datetime_field=test_datetime
        )

        db_mock.create_table(DateModel)
        inserted = db_mock.insert(model)

        # Fetch it back
        fetched = db_mock.get(DateModel, inserted.pk)

        assert fetched is not None
        assert fetched.date_field == test_date
        assert fetched.datetime_field == test_datetime

    def test_datetime_different_timezones(self, db_mock) -> None:
        """Test handling of datetimes in different timezones."""
        from datetime import timedelta, timezone

        class TimezoneModel(BaseDBModel):
            name: str
            dt_field: datetime

            class Meta:
                table_name = "timezone_test"

        # Create datetime in different timezones
        tz_plus_2 = timezone(timedelta(hours=2))
        tz_minus_5 = timezone(timedelta(hours=-5))

        test_dt_plus_2 = datetime(2024, 1, 1, 12, 0, tzinfo=tz_plus_2)
        test_dt_minus_5 = datetime(2024, 1, 1, 12, 0, tzinfo=tz_minus_5)

        db_mock.create_table(TimezoneModel)

        # Insert and retrieve both timestamps
        model_1 = TimezoneModel(name="plus_2", dt_field=test_dt_plus_2)
        model_2 = TimezoneModel(name="minus_5", dt_field=test_dt_minus_5)

        inserted_1 = db_mock.insert(model_1)
        inserted_2 = db_mock.insert(model_2)

        fetched_1 = db_mock.get(TimezoneModel, inserted_1.pk)
        fetched_2 = db_mock.get(TimezoneModel, inserted_2.pk)

        assert fetched_1 is not None
        assert fetched_2 is not None

        # Both should represent the same moment in time as their originals,
        # regardless of timezone
        assert fetched_1.dt_field.timestamp() == test_dt_plus_2.timestamp()
        assert fetched_2.dt_field.timestamp() == test_dt_minus_5.timestamp()

    def test_date_edge_cases(self, db_mock) -> None:
        """Test dates near Unix timestamp boundaries."""

        class EdgeDateModel(BaseDBModel):
            name: str
            dt_field: datetime

            class Meta:
                table_name = "edge_dates_test"

        db_mock.create_table(EdgeDateModel)

        # Test edge cases
        edge_dates = [
            datetime(1970, 1, 1, tzinfo=timezone.utc),  # Unix epoch
            datetime(
                2038, 1, 19, 3, 14, 7, tzinfo=timezone.utc
            ),  # 32-bit limit
            datetime(
                1969, 12, 31, 23, 59, 59, tzinfo=timezone.utc
            ),  # Pre-epoch
            datetime(2100, 1, 1, tzinfo=timezone.utc),  # Far future
        ]

        inserted_pks = []
        for i, test_dt in enumerate(edge_dates):
            model = EdgeDateModel(name=f"edge_{i}", dt_field=test_dt)
            inserted = db_mock.insert(model)
            inserted_pks.append(inserted.pk)

        # Verify all dates were stored and retrieved correctly
        for pk, original_dt in zip(inserted_pks, edge_dates):
            fetched = db_mock.get(EdgeDateModel, pk)
            assert fetched is not None
            assert fetched.dt_field.timestamp() == original_dt.timestamp()

    def test_optional_date_fields(self, db_mock) -> None:
        """Test handling of Optional[date] and Optional[datetime] fields."""
        from typing import Optional

        class OptionalDateModel(BaseDBModel):
            name: str
            date_field: Optional[date] = None
            dt_field: Optional[datetime] = None

            class Meta:
                table_name = "optional_dates_test"

        db_mock.create_table(OptionalDateModel)

        # Test with null values
        null_model = OptionalDateModel(name="null_dates")
        inserted_null = db_mock.insert(null_model)

        # Test with actual values
        value_model = OptionalDateModel(
            name="with_dates",
            date_field=date(2024, 1, 1),
            dt_field=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
        )
        inserted_value = db_mock.insert(value_model)

        # Verify null values
        fetched_null = db_mock.get(OptionalDateModel, inserted_null.pk)
        assert fetched_null is not None
        assert fetched_null.date_field is None
        assert fetched_null.dt_field is None

        # Verify actual values
        fetched_value = db_mock.get(OptionalDateModel, inserted_value.pk)
        assert fetched_value is not None
        assert fetched_value.date_field == date(2024, 1, 1)
        assert (
            fetched_value.dt_field.timestamp()
            == datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc).timestamp()
        )

    def test_update_date_fields(self, db_mock) -> None:
        """Test updating date and datetime fields."""

        class UpdateDateModel(BaseDBModel):
            name: str
            date_field: date
            dt_field: datetime

            class Meta:
                table_name = "update_dates_test"

        db_mock.create_table(UpdateDateModel)

        # Create initial record
        initial_model = UpdateDateModel(
            name="test",
            date_field=date(2024, 1, 1),
            dt_field=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
        )
        inserted = db_mock.insert(initial_model)

        # Update to new dates
        inserted.date_field = date(2024, 2, 1)
        inserted.dt_field = datetime(2024, 2, 1, 14, 30, tzinfo=timezone.utc)
        db_mock.update(inserted)

        # Verify updates
        fetched = db_mock.get(UpdateDateModel, inserted.pk)
        assert fetched is not None
        assert fetched.date_field == date(2024, 2, 1)
        assert (
            fetched.dt_field.timestamp()
            == datetime(2024, 2, 1, 14, 30, tzinfo=timezone.utc).timestamp()
        )

        # Update just one field
        fetched.dt_field = datetime(2024, 3, 1, 9, 15, tzinfo=timezone.utc)
        db_mock.update(fetched)

        # Verify partial update
        final = db_mock.get(UpdateDateModel, inserted.pk)
        assert final is not None
        assert final.date_field == date(2024, 2, 1)  # Unchanged
        assert (
            final.dt_field.timestamp()
            == datetime(2024, 3, 1, 9, 15, tzinfo=timezone.utc).timestamp()
        )
