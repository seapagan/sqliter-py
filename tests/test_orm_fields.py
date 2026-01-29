"""Tests for ORM field descriptors."""

from __future__ import annotations

from typing import Optional

from sqliter.orm.fields import ForeignKey
from sqliter.orm.model import BaseDBModel


# Module-level models for testing annotation detection
class RelatedModel1(BaseDBModel):
    """Related model for non-optional FK."""

    name: str


class RelatedModel2(BaseDBModel):
    """Related model for optional FK."""

    name: str


class OwnerWithNonOptionalFK(BaseDBModel):
    """Model with non-optional FK."""

    rel: ForeignKey[RelatedModel1] = ForeignKey(RelatedModel1)


class OwnerWithOptionalFK(BaseDBModel):
    """Model with optional FK."""

    rel: ForeignKey[Optional[RelatedModel2]] = ForeignKey(RelatedModel2)


def test_fk_non_optional_annotation() -> None:
    """ForeignKey[Model] should have null=False."""
    fk_descriptor = OwnerWithNonOptionalFK.fk_descriptors["rel"]
    assert fk_descriptor.fk_info.null is False


def test_fk_optional_annotation_sets_nullable() -> None:
    """ForeignKey[Optional[Model]] should auto-set null=True."""
    fk_descriptor = OwnerWithOptionalFK.fk_descriptors["rel"]
    assert fk_descriptor.fk_info.null is True
