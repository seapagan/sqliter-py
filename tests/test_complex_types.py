"""Test serialization and deserialization of complex data types."""
# ruff: noqa: C405  # Allow set([...]) syntax in tests to verify we both handle both forms

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

    def test_update_list_field(
        self, model_instance: ComplexTypesModel, tmp_path: str
    ) -> None:
        """Test updating a record's list field."""
        db_path = f"{tmp_path}/test_update_list.db"
        db = SqliterDB(db_path)
        db.create_table(ComplexTypesModel)

        # Save initial record
        saved = db.insert(model_instance)
        assert saved.list_field == ["a", "b", "c"]

        # Update the list field
        saved.list_field = ["x", "y", "z"]
        db.update(saved)

        # Read back and verify
        loaded = db.get(ComplexTypesModel, saved.pk)
        assert loaded is not None
        assert isinstance(loaded.list_field, list)
        assert loaded.list_field == ["x", "y", "z"]

        db.close()

    def test_update_dict_field(
        self, model_instance: ComplexTypesModel, tmp_path: str
    ) -> None:
        """Test updating a record's dictionary field."""
        db_path = f"{tmp_path}/test_update_dict.db"
        db = SqliterDB(db_path)
        db.create_table(ComplexTypesModel)

        # Save initial record
        saved = db.insert(model_instance)
        assert saved.dict_field == {"key1": "value1", "key2": 123, "key3": True}

        # Update the dict field
        new_dict = {
            "new_key1": "new_value1",
            "new_key2": 456,
            "new_key3": False,
        }
        saved.dict_field = new_dict
        db.update(saved)

        # Read back and verify
        loaded = db.get(ComplexTypesModel, saved.pk)
        assert loaded is not None
        assert isinstance(loaded.dict_field, dict)
        assert loaded.dict_field == new_dict

        db.close()

    def test_update_set_field(
        self, model_instance: ComplexTypesModel, tmp_path: str
    ) -> None:
        """Test updating a record's set field."""
        db_path = f"{tmp_path}/test_update_set.db"
        db = SqliterDB(db_path)
        db.create_table(ComplexTypesModel)

        # Save initial record
        saved = db.insert(model_instance)
        assert saved.set_field == {1, 2, 3}

        # Update the set field
        new_set = {4, 5, 6}
        saved.set_field = new_set
        db.update(saved)

        # Read back and verify
        loaded = db.get(ComplexTypesModel, saved.pk)
        assert loaded is not None
        assert isinstance(loaded.set_field, set)
        assert loaded.set_field == new_set

        db.close()

    def test_update_tuple_field(
        self, model_instance: ComplexTypesModel, tmp_path: str
    ) -> None:
        """Test updating a record's tuple field."""
        db_path = f"{tmp_path}/test_update_tuple.db"
        db = SqliterDB(db_path)
        db.create_table(ComplexTypesModel)

        # Save initial record
        saved = db.insert(model_instance)
        assert saved.tuple_field == ("test", 42, True)

        # Update the tuple field
        new_tuple = ("updated", 99, False)
        saved.tuple_field = new_tuple
        db.update(saved)

        # Read back and verify
        loaded = db.get(ComplexTypesModel, saved.pk)
        assert loaded is not None
        assert isinstance(loaded.tuple_field, tuple)
        assert loaded.tuple_field == new_tuple

        db.close()

    def test_update_multiple_complex_fields(
        self, model_instance: ComplexTypesModel, tmp_path: str
    ) -> None:
        """Test updating multiple complex fields simultaneously."""
        db_path = f"{tmp_path}/test_update_multiple.db"
        db = SqliterDB(db_path)
        db.create_table(ComplexTypesModel)

        # Save initial record
        saved = db.insert(model_instance)

        # Update all complex fields
        saved.list_field = ["x", "y", "z"]
        saved.dict_field = {"new": "value"}
        saved.set_field = {7, 8, 9}
        saved.tuple_field = ("new", 100, False)
        db.update(saved)

        # Read back and verify
        loaded = db.get(ComplexTypesModel, saved.pk)
        assert loaded is not None

        # Verify all fields were updated correctly
        assert isinstance(loaded.list_field, list)
        assert loaded.list_field == ["x", "y", "z"]

        assert isinstance(loaded.dict_field, dict)
        assert loaded.dict_field == {"new": "value"}

        assert isinstance(loaded.set_field, set)
        assert loaded.set_field == {7, 8, 9}

        assert isinstance(loaded.tuple_field, tuple)
        assert loaded.tuple_field == ("new", 100, False)

        db.close()

    def test_complex_nested_list(self, tmp_path: str) -> None:
        """Test storing and retrieving a deeply nested list structure."""

        class NestedListModel(BaseDBModel):
            complex_list: list[Any]

        # Create a complex nested list with various Python types
        nested_list = [
            [1, 2, [3, 4, {"key": [5, 6, (7, 8)]}]],
            {"nested_dict": [9, 10, set([11, 12])]},
            (13, [14, {15, 16}]),
            [{"a": 1, "b": [2, 3, {"c": 4}]}, set([5, 6, 7])],
            [[[[1, 2], 3], 4], 5],  # Deep nesting
        ]

        model = NestedListModel(complex_list=nested_list)
        db = SqliterDB(f"{tmp_path}/test_nested_list.db")
        db.create_table(NestedListModel)

        # Test insert and retrieve
        saved = db.insert(model)
        loaded = db.get(NestedListModel, saved.pk)
        assert loaded is not None
        assert loaded.complex_list == nested_list
        assert isinstance(loaded.complex_list[0], list)
        assert isinstance(loaded.complex_list[1], dict)
        assert isinstance(loaded.complex_list[2], tuple)
        assert isinstance(loaded.complex_list[2][1], list)
        assert isinstance(loaded.complex_list[3][1], set)

        # Test update with even more complex structure
        new_nested_list = [
            *nested_list,
            {"more": [set([1, 2]), (3, 4), [{"deep": {"deeper": [5, 6]}}]]},
        ]
        saved.complex_list = new_nested_list
        db.update(saved)

        loaded = db.get(NestedListModel, saved.pk)
        assert loaded is not None
        assert loaded.complex_list == new_nested_list
        db.close()

    def test_complex_nested_dict(self, tmp_path: str) -> None:
        """Test storing and retrieving a deeply nested dictionary structure."""

        class NestedDictModel(BaseDBModel):
            complex_dict: dict[str, Any]

        # Create a complex nested dictionary
        nested_dict = {
            "simple": "value",
            "numbers": [1, 2, 3],
            "nested": {
                "list": [4, 5, {"key": "value"}],
                "tuple": (6, 7, [8, 9]),
                "set": {10, 11, 12},
                "dict": {
                    "deep": {
                        "deeper": {
                            "deepest": [{"a": 1}, set([2, 3]), (4, [5, {6, 7}])]
                        }
                    }
                },
            },
            "mixed": [{"a": (1, 2)}, set([3, 4]), [5, {"b": 6}]],
        }

        model = NestedDictModel(complex_dict=nested_dict)
        db = SqliterDB(f"{tmp_path}/test_nested_dict.db")
        db.create_table(NestedDictModel)

        # Test insert and retrieve
        saved = db.insert(model)
        loaded = db.get(NestedDictModel, saved.pk)
        assert loaded is not None
        assert loaded.complex_dict == nested_dict
        assert isinstance(loaded.complex_dict["numbers"], list)
        assert isinstance(loaded.complex_dict["nested"]["tuple"], tuple)
        assert isinstance(loaded.complex_dict["nested"]["set"], set)
        assert isinstance(
            loaded.complex_dict["nested"]["dict"]["deep"]["deeper"]["deepest"][
                1
            ],
            set,
        )

        # Test update with modified structure
        new_nested_dict = {
            **nested_dict,
            "additional": {
                "complex": [
                    set([1, 2]),
                    (3, {"nested": [4, 5, {6, 7}]}),
                    {"more": {"levels": {"here": [8, 9, 10]}}},
                ]
            },
        }
        saved.complex_dict = new_nested_dict
        db.update(saved)

        loaded = db.get(NestedDictModel, saved.pk)
        assert loaded is not None
        assert loaded.complex_dict == new_nested_dict
        db.close()

    def test_complex_nested_set(self, tmp_path: str) -> None:
        """Test storing and retrieving complex structures within a set."""

        class NestedSetModel(BaseDBModel):
            # Note: Set itself can only contain immutable items
            complex_set: set[tuple[Any, ...]]

        # Create a complex set with nested immutable structures
        nested_set = {
            (1, 2, (3, 4)),
            ("string", (5, 6, (7, 8))),
            (9, (10, (11, (12, 13)))),
            ("mixed", (14, "str", (15, 16))),
            (17, (tuple(range(18, 21)), "end")),
        }

        model = NestedSetModel(complex_set=nested_set)
        db = SqliterDB(f"{tmp_path}/test_nested_set.db")
        db.create_table(NestedSetModel)

        # Test insert and retrieve
        saved = db.insert(model)
        loaded = db.get(NestedSetModel, saved.pk)
        assert loaded is not None
        assert loaded.complex_set == nested_set
        assert all(isinstance(item, tuple) for item in loaded.complex_set)

        # Test update with modified structure
        new_nested_set = {
            *nested_set,
            (22, (23, (24, (25, 26)))),
            ("deep", ("nesting", ("here", ("too", "!")))),
        }
        saved.complex_set = new_nested_set
        db.update(saved)

        loaded = db.get(NestedSetModel, saved.pk)
        assert loaded is not None
        assert loaded.complex_set == new_nested_set
        db.close()

    def test_complex_nested_tuple(self, tmp_path: str) -> None:
        """Test storing and retrieving a deeply nested tuple structure."""

        class NestedTupleModel(BaseDBModel):
            complex_tuple: tuple[Any, ...]

        # Create a complex nested tuple
        nested_tuple = (
            1,
            (2, 3, (4, 5)),
            [6, 7, (8, 9)],
            {"key": (10, 11, [12, 13])},
            (14, {"nested": (15, [16, {"deep": (17, 18)}])}),
            (19, (20, (21, (22, (23, 24))))),
            [{"a": (1, 2)}, set([3, 4]), (5, [6, 7])],
        )

        model = NestedTupleModel(complex_tuple=nested_tuple)
        db = SqliterDB(f"{tmp_path}/test_nested_tuple.db")
        db.create_table(NestedTupleModel)

        # Test insert and retrieve
        saved = db.insert(model)
        loaded = db.get(NestedTupleModel, saved.pk)
        assert loaded is not None
        assert loaded.complex_tuple == nested_tuple
        assert isinstance(loaded.complex_tuple[1], tuple)
        assert isinstance(loaded.complex_tuple[2], list)
        assert isinstance(loaded.complex_tuple[3], dict)
        assert isinstance(loaded.complex_tuple[4][1]["nested"], tuple)

        # Test update with modified structure
        new_nested_tuple = (
            *nested_tuple,
            (25, (26, [27, {"complex": (28, {29, 30})}])),
        )
        saved.complex_tuple = new_nested_tuple
        db.update(saved)

        loaded = db.get(NestedTupleModel, saved.pk)
        assert loaded is not None
        assert loaded.complex_tuple == new_nested_tuple
        db.close()
