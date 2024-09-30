from typing import Optional

import pytest

from sqliter.model.model import BaseDBModel

"""Test the Model and it's methods."""


class TestBaseDBModel:
    def test_should_create_pk(self) -> None:
        """Test that 'should_create_pk' returns True."""
        assert BaseDBModel.should_create_pk() is True

    def test_get_primary_key(self) -> None:
        """Test that 'get_primary_key' returns 'pk'."""
        assert BaseDBModel.get_primary_key() == "pk"

    def test_get_table_name_default(self) -> None:
        """Test that 'get_table_name' returns the default table name."""

        class TestModel(BaseDBModel):
            pass

        assert TestModel.get_table_name() == "tests"

    def test_get_table_name_custom(self) -> None:
        """Test that 'get_table_name' returns the custom table name."""

        class TestModel(BaseDBModel):
            class Meta:
                table_name = "custom_table"

        assert TestModel.get_table_name() == "custom_table"

    def test_model_validate_partial(self) -> None:
        """Test 'model_validate_partial' with partial data."""

        class TestModel(BaseDBModel):
            name: str
            age: Optional[int]

        data = {"name": "John"}
        model_instance = TestModel.model_validate_partial(data)
        assert model_instance.name == "John"
        with pytest.raises(AttributeError):
            _ = model_instance.age
