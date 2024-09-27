"""Tests for the 'order' method in the QueryBuilder class."""

import pytest

from sqliter.exceptions import InvalidOrderError
from sqliter.model import BaseDBModel


class TestOrderMethod:
    """Test class for the 'order' method in the QueryBuilder class."""

    def test_order_by_primary_key_default(self, db_mock) -> None:
        """Test ordering by primary key when no field is specified."""

        class OrderTestModel(BaseDBModel):
            id: int
            name: str

            class Meta:
                table_name: str = "order_test_table"

        db_mock.create_table(OrderTestModel)
        db_mock.insert(OrderTestModel(id=1, name="Alice"))
        db_mock.insert(OrderTestModel(id=2, name="Bob"))
        db_mock.insert(OrderTestModel(id=3, name="Charlie"))

        results = db_mock.select(OrderTestModel).order().fetch_all()

        assert len(results) == 3
        assert results[0].id == 1
        assert results[1].id == 2
        assert results[2].id == 3

    def test_order_by_primary_key_reverse(self, db_mock) -> None:
        """Test ordering by primary key in descending order."""

        class OrderTestModel(BaseDBModel):
            id: int
            name: str

            class Meta:
                table_name: str = "order_test_table"

        db_mock.create_table(OrderTestModel)
        db_mock.insert(OrderTestModel(id=1, name="Alice"))
        db_mock.insert(OrderTestModel(id=2, name="Bob"))
        db_mock.insert(OrderTestModel(id=3, name="Charlie"))

        results = db_mock.select(OrderTestModel).order(reverse=True).fetch_all()

        assert len(results) == 3
        assert results[0].id == 3
        assert results[1].id == 2
        assert results[2].id == 1

    def test_order_by_specified_field(self, db_mock) -> None:
        """Test ordering by a specified field."""

        class OrderTestModel(BaseDBModel):
            id: int
            name: str

            class Meta:
                table_name: str = "order_test_table"

        db_mock.create_table(OrderTestModel)
        db_mock.insert(OrderTestModel(id=1, name="Charlie"))
        db_mock.insert(OrderTestModel(id=2, name="Alice"))
        db_mock.insert(OrderTestModel(id=3, name="Bob"))

        results = db_mock.select(OrderTestModel).order("name").fetch_all()

        assert len(results) == 3
        assert results[0].name == "Alice"
        assert results[1].name == "Bob"
        assert results[2].name == "Charlie"

    def test_order_by_specified_field_reverse(self, db_mock) -> None:
        """Test ordering by a specified field in descending order."""

        class OrderTestModel(BaseDBModel):
            id: int
            name: str

            class Meta:
                table_name: str = "order_test_table"

        db_mock.create_table(OrderTestModel)
        db_mock.insert(OrderTestModel(id=1, name="Charlie"))
        db_mock.insert(OrderTestModel(id=2, name="Alice"))
        db_mock.insert(OrderTestModel(id=3, name="Bob"))

        results = (
            db_mock.select(OrderTestModel)
            .order("name", reverse=True)
            .fetch_all()
        )

        assert len(results) == 3
        assert results[0].name == "Charlie"
        assert results[1].name == "Bob"
        assert results[2].name == "Alice"

    def test_order_with_reverse_false(self, db_mock) -> None:
        """Test the order method works with reverse=False (ascending order)."""

        class TestModel(BaseDBModel):
            name: str

            class Meta:
                table_name = "test_table"

        db_mock.create_table(TestModel)
        db_mock.insert(TestModel(name="Charlie"))
        db_mock.insert(TestModel(name="Alice"))
        db_mock.insert(TestModel(name="Bob"))

        # Ascending order
        results = (
            db_mock.select(TestModel).order("name", reverse=False).fetch_all()
        )
        assert len(results) == 3
        assert results[0].name == "Alice"
        assert results[1].name == "Bob"
        assert results[2].name == "Charlie"

    def test_order_invalid_field(self, db_mock) -> None:
        """Test ordering by an invalid field."""

        class OrderTestModel(BaseDBModel):
            id: int
            name: str

            class Meta:
                table_name: str = "order_test_table"

        db_mock.create_table(OrderTestModel)

        with pytest.raises(InvalidOrderError) as exc:
            db_mock.select(OrderTestModel).order("invalid_field").fetch_all()

        assert "Invalid order value - 'invalid_field' does not exist" in str(
            exc.value
        )

    def test_order_both_direction_and_reverse(self, db_mock) -> None:
        """Test ordering with both direction and reverse specified."""

        class OrderTestModel(BaseDBModel):
            id: int
            name: str

            class Meta:
                table_name: str = "order_test_table"

        db_mock.create_table(OrderTestModel)

        with pytest.raises(
            InvalidOrderError,
            match="Cannot specify both 'direction' and 'reverse'",
        ):
            db_mock.select(OrderTestModel).order(
                "name", direction="ASC", reverse=True
            ).fetch_all()

    def test_order_deprecation_warning(self, db_mock) -> None:
        """Test that using 'direction' raises a DeprecationWarning."""

        class TestModel(BaseDBModel):
            name: str

        with pytest.warns(
            DeprecationWarning, match="'direction' argument is deprecated"
        ):
            db_mock.select(TestModel).order("name", direction="ASC")

    def test_order_invalid_direction(self, db_mock) -> None:
        """Test that an invalid order direction raises an exception."""

        # Define a simple model for the test
        class TestModel(BaseDBModel):
            name: str

        # Create the table for the model
        db_mock.create_table(TestModel)

        # Attempt to order by an invalid direction
        with pytest.raises(InvalidOrderError) as exc:
            db_mock.select(TestModel).order("name", direction="invalid")

        assert (
            "Invalid order value - 'invalid' is not a valid sorting direction"
            in str(exc.value)
        )

    def test_order_direction_ascending(self, db_mock) -> None:
        """Test that the order method works as expected when ASC specified."""

        # Define a simple model for the test
        class OrderTestModel(BaseDBModel):
            name: str

            class Meta:
                table_name: str = "order_test_table"

        # Create the table and insert records
        db_mock.create_table(OrderTestModel)
        db_mock.insert(OrderTestModel(name="John Doe"))
        db_mock.insert(OrderTestModel(name="Jane Doe"))
        db_mock.insert(OrderTestModel(name="Jim Doe"))

        # Perform a query with ordering by name DESC
        results = (
            db_mock.select(OrderTestModel)
            .order("name", direction="asc")
            .fetch_all()
        )

        # Assert that the ordering works in descending order
        assert len(results) == 3
        assert results[0].name == "Jane Doe"
        assert results[1].name == "Jim Doe"
        assert results[2].name == "John Doe"

    def test_order_direction_desc(self, db_mock) -> None:
        """Test that the order method works as expected descending."""

        # Define a simple model for the test
        class OrderTestModel(BaseDBModel):
            name: str

            class Meta:
                table_name: str = "order_test_table"

        # Create the table and insert records
        db_mock.create_table(OrderTestModel)
        db_mock.insert(OrderTestModel(name="John Doe"))
        db_mock.insert(OrderTestModel(name="Jane Doe"))
        db_mock.insert(OrderTestModel(name="Jim Doe"))

        # Perform a query with ordering by name DESC
        results = (
            db_mock.select(OrderTestModel)
            .order("name", direction="desc")
            .fetch_all()
        )

        # Assert that the ordering works in descending order
        assert len(results) == 3
        assert results[0].name == "John Doe"
        assert results[1].name == "Jim Doe"
        assert results[2].name == "Jane Doe"
