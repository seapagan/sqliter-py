"""Test serialization and deserialization of complex data types."""

import pickle
from typing import Any, ClassVar, Union

import pytest
from pydantic_core import ValidationError

from sqliter import SqliterDB
from sqliter.model import BaseDBModel


class ComplexTypesModel(BaseDBModel):
    """Model for testing complex data types."""

    list_field: list[str]
    dict_field: dict[str, Any]
    set_field: set[int]
    tuple_field: tuple[str, int, bool]
    empty_list: ClassVar[list[str]] = []
    empty_dict: ClassVar[dict[str, Any]] = {}
    empty_set: ClassVar[set[int]] = set()
    empty_tuple: ClassVar[tuple[()]] = ()


class TestComplexTypes:
    """Test class for complex type serialization/deserialization."""

    @pytest.fixture
    def model_instance(self) -> ComplexTypesModel:
        """Create a test model instance with complex types."""
        return ComplexTypesModel(
            list_field=["a", "b", "c"],
            dict_field={"key1": "value1", "key2": 123, "key3": True},
            set_field={1, 2, 3},
            tuple_field=("test", 42, True),
            empty_list=[],
            empty_dict={},
            empty_set=set(),
            empty_tuple=(),
        )

    def test_serialize_list(self, model_instance: ComplexTypesModel) -> None:
        """Test serialization of list field."""
        result = model_instance.serialize_field(model_instance.list_field)
        assert isinstance(result, bytes)  # Should be pickled
        assert model_instance.deserialize_field(
            "list_field", result, return_local_time=True
        ) == ["a", "b", "c"]

    def test_serialize_dict(self, model_instance: ComplexTypesModel) -> None:
        """Test serialization of dictionary field."""
        result = model_instance.serialize_field(model_instance.dict_field)
        assert isinstance(result, bytes)  # Should be pickled
        assert model_instance.deserialize_field(
            "dict_field", result, return_local_time=True
        ) == {"key1": "value1", "key2": 123, "key3": True}

    def test_serialize_set(self, model_instance: ComplexTypesModel) -> None:
        """Test serialization of set field."""
        result = model_instance.serialize_field(model_instance.set_field)
        assert isinstance(result, bytes)  # Should be pickled
        assert model_instance.deserialize_field(
            "set_field", result, return_local_time=True
        ) == {1, 2, 3}

    def test_serialize_tuple(self, model_instance: ComplexTypesModel) -> None:
        """Test serialization of tuple field."""
        result = model_instance.serialize_field(model_instance.tuple_field)
        assert isinstance(result, bytes)  # Should be pickled
        assert model_instance.deserialize_field(
            "tuple_field", result, return_local_time=True
        ) == ("test", 42, True)

    def test_list_type_preservation(
        self, model_instance: ComplexTypesModel
    ) -> None:
        """Test list maintains its type after serialization/deserialization."""
        result = model_instance.serialize_field(model_instance.list_field)
        deserialized = model_instance.deserialize_field(
            "list_field", result, return_local_time=True
        )
        assert isinstance(deserialized, list)
        assert deserialized == model_instance.list_field

    def test_dict_type_preservation(
        self, model_instance: ComplexTypesModel
    ) -> None:
        """Test dict maintains its type after serialization/deserialization."""
        result = model_instance.serialize_field(model_instance.dict_field)
        deserialized = model_instance.deserialize_field(
            "dict_field", result, return_local_time=True
        )
        assert isinstance(deserialized, dict)
        assert deserialized == model_instance.dict_field

    def test_set_type_preservation(
        self, model_instance: ComplexTypesModel
    ) -> None:
        """Test set maintains its type after serialization/deserialization."""
        result = model_instance.serialize_field(model_instance.set_field)
        deserialized = model_instance.deserialize_field(
            "set_field", result, return_local_time=True
        )
        assert isinstance(deserialized, set)
        assert deserialized == model_instance.set_field

    def test_tuple_type_preservation(
        self, model_instance: ComplexTypesModel
    ) -> None:
        """Test tuple maintains its type after serialization/deserialization."""
        result = model_instance.serialize_field(model_instance.tuple_field)
        deserialized = model_instance.deserialize_field(
            "tuple_field", result, return_local_time=True
        )
        assert isinstance(deserialized, tuple)
        assert deserialized == model_instance.tuple_field

    def test_empty_containers(self, model_instance: ComplexTypesModel) -> None:
        """Test serialization of empty containers."""
        # Test empty list
        result = model_instance.serialize_field(model_instance.empty_list)
        assert isinstance(result, bytes)
        assert pickle.loads(result) == []

        # Test empty dict
        result = model_instance.serialize_field(model_instance.empty_dict)
        assert isinstance(result, bytes)
        assert pickle.loads(result) == {}

        # Test empty set
        result = model_instance.serialize_field(model_instance.empty_set)
        assert isinstance(result, bytes)
        assert pickle.loads(result) == set()

        # Test empty tuple
        result = model_instance.serialize_field(model_instance.empty_tuple)
        assert isinstance(result, bytes)
        assert pickle.loads(result) == ()

    def test_nested_structures(self) -> None:
        """Test serialization of nested data structures."""

        class NestedModel(BaseDBModel):
            nested_field: list[dict[str, list[int]]]

        nested_data = [{"nums": [1, 2, 3]}, {"nums": [4, 5, 6]}]
        model = NestedModel(nested_field=nested_data)

        result = model.serialize_field(model.nested_field)
        assert isinstance(result, bytes)
        assert (
            model.deserialize_field(
                "nested_field", result, return_local_time=True
            )
            == nested_data
        )

    def test_invalid_pickle_data(
        self, model_instance: ComplexTypesModel
    ) -> None:
        """Test handling of invalid pickle data."""
        invalid_bytes = b"invalid pickle data"
        # Should return the original value when unpickling fails
        assert (
            model_instance.deserialize_field(
                "list_field", invalid_bytes, return_local_time=True
            )
            == invalid_bytes
        )

    def test_none_values(self, model_instance: ComplexTypesModel) -> None:
        """Test handling of None values."""
        assert (
            model_instance.deserialize_field(
                "list_field", None, return_local_time=True
            )
            is None
        )

    @pytest.mark.parametrize(
        ("field_name", "invalid_value"),
        [
            ("list_field", "not a list"),
            ("dict_field", [1, 2, 3]),  # List instead of dict
            ("set_field", {"key": "value"}),  # Dict instead of set
            ("tuple_field", {1, 2, 3}),  # Set instead of tuple
        ],
        ids=["list", "dict", "set", "tuple"],
    )
    def test_type_validation(
        self,
        model_instance: ComplexTypesModel,
        field_name: str,
        invalid_value: Union[
            list[Any], dict[Any, Any], set[Any], tuple[Any, ...]
        ],
    ) -> None:
        """Test validation of incorrect types."""
        with pytest.raises(ValidationError):
            setattr(model_instance, field_name, invalid_value)

    def test_db_roundtrip_type_preservation(
        self, model_instance: ComplexTypesModel, tmp_path: str
    ) -> None:
        """Test complex types maintain their types after database save/load."""
        db_path = f"{tmp_path}/test.db"
        db = SqliterDB(db_path)
        db.create_table(ComplexTypesModel)

        # Save to database
        saved = db.insert(model_instance)

        # Read back from database
        loaded = db.get(ComplexTypesModel, saved.pk)

        # Ensure we got a result back
        assert loaded is not None, "Failed to load model from database"

        # Check each field maintains both type and value
        assert isinstance(loaded.list_field, list)
        assert loaded.list_field == ["a", "b", "c"]

        assert isinstance(loaded.dict_field, dict)
        assert loaded.dict_field == {
            "key1": "value1",
            "key2": 123,
            "key3": True,
        }

        assert isinstance(loaded.set_field, set)
        assert loaded.set_field == {1, 2, 3}

        assert isinstance(loaded.tuple_field, tuple)
        assert loaded.tuple_field == ("test", 42, True)

        db.close()
