"""Tests for ORM field descriptors."""

from __future__ import annotations

from typing import Optional

import pytest
from pydantic.fields import FieldInfo

from sqliter.orm.fields import ForeignKey
from sqliter.orm.model import BaseDBModel


# Module-level models for testing annotation detection
class RelatedModel1(BaseDBModel):
    """Related model for non-optional FK."""

    name: str


class RelatedModel2(BaseDBModel):
    """Related model for optional FK."""

    name: str


class RelatedModel3(BaseDBModel):
    """Related model for assignment tests."""

    name: str


class OwnerWithNonOptionalFK(BaseDBModel):
    """Model with non-optional FK."""

    rel: ForeignKey[RelatedModel1] = ForeignKey(RelatedModel1)


class OwnerWithOptionalFK(BaseDBModel):
    """Model with optional FK."""

    rel: ForeignKey[Optional[RelatedModel2]] = ForeignKey(RelatedModel2)


class OwnerWithFK(BaseDBModel):
    """Model with optional FK for testing assignment."""

    related: ForeignKey[Optional[RelatedModel3]] = ForeignKey(RelatedModel3)


def test_fk_non_optional_annotation() -> None:
    """ForeignKey[Model] should have null=False."""
    fk_descriptor = OwnerWithNonOptionalFK.fk_descriptors["rel"]
    assert fk_descriptor.fk_info.null is False


def test_fk_optional_annotation_sets_nullable() -> None:
    """ForeignKey[Optional[Model]] should auto-set null=True."""
    fk_descriptor = OwnerWithOptionalFK.fk_descriptors["rel"]
    assert fk_descriptor.fk_info.null is True


def test_fk_assignment_with_none() -> None:
    """Setting FK field to None should set _id to None."""
    owner = OwnerWithFK()
    owner.related = None
    assert owner.related_id is None


def test_fk_assignment_with_int() -> None:
    """Setting FK field to int should set _id to that int."""
    owner = OwnerWithFK()
    owner.related = 42
    assert owner.related_id == 42


def test_fk_assignment_with_model_instance() -> None:
    """Setting FK field to model instance should extract pk."""
    related_obj = RelatedModel3(name="Test")
    related_obj.pk = 123

    owner = OwnerWithFK()
    owner.related = related_obj
    assert owner.related_id == 123


def test_fk_assignment_with_invalid_type_raises_error() -> None:
    """Setting FK field to invalid type should raise TypeError."""
    owner = OwnerWithFK()
    with pytest.raises(
        TypeError, match="FK value must be BaseModel, int, or None"
    ):
        owner.related = "invalid"


def test_fk_assignment_clears_cache() -> None:
    """Setting FK field should clear cached value."""
    owner = OwnerWithFK()
    owner.related_id = 5

    # Access the FK field to create a real LazyLoader in the cache
    _ = owner.related
    assert "_fk_cache" in owner.__dict__
    assert "related" in owner.__dict__["_fk_cache"]

    # Setting FK should delete the entry from cache (line 125)
    owner.related = None
    assert "related" not in owner.__dict__.get("_fk_cache", {})


def test_fk_detection_when_field_not_in_hints() -> None:
    """_detect_nullable_from_annotation when field name not in hints."""

    class RelatedModel(BaseDBModel):
        """Related model."""

        name: str

    class OwnerModel(BaseDBModel):
        """Owner model."""

        name: str

    # Create a descriptor and manually call detection with a field
    # name that doesn't exist in OwnerModel's hints
    fk_descriptor = ForeignKey(RelatedModel)
    # This should not crash, just return early (line 231)
    fk_descriptor._detect_nullable_from_annotation(OwnerModel, "nonexistent")
    assert fk_descriptor.fk_info.null is False  # Should remain default


def test_fk_detection_with_no_type_args() -> None:
    """_detect_nullable_from_annotation when FK has no type args."""

    class RelatedModel(BaseDBModel):
        """Related model."""

        name: str

    class OwnerModel(BaseDBModel):
        """Owner model with bare ForeignKey annotation."""

        name: str

    # Simulate a ForeignKey annotation with no type args
    # This would be something like: rel: ForeignKey = ForeignKey(RelatedModel)
    # which is invalid but we should handle it gracefully (line 237)
    OwnerModel.__annotations__["rel"] = "ForeignKey"

    fk_descriptor = ForeignKey(RelatedModel)
    fk_descriptor._detect_nullable_from_annotation(OwnerModel, "rel")
    # Should remain default (null=False) since we can't detect Optional
    assert fk_descriptor.fk_info.null is False


def test_fk_removed_from_model_fields_during_setup() -> None:
    """FK field should be removed from model_fields during _setup_orm_fields."""

    class RelatedModel(BaseDBModel):
        """Related model."""

        name: str

    class OwnerModel(BaseDBModel):
        """Owner model with FK."""

        # This will normally be removed before model_fields is built,
        # but we'll manually add it back to test the deletion path (line 247)
        rel: ForeignKey[Optional[RelatedModel]] = ForeignKey(RelatedModel)

    # Manually add the FK to model_fields to simulate it being there
    # (this could happen with unusual metaclass usage or direct manipulation)
    OwnerModel.model_fields["rel"] = FieldInfo.from_annotation(
        ForeignKey[Optional[RelatedModel]]
    )
    assert "rel" in OwnerModel.model_fields

    # Call _setup_orm_fields which should delete it (line 247)
    OwnerModel._setup_orm_fields()
    assert "rel" not in OwnerModel.model_fields
