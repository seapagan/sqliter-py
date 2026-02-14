"""Tests for bulk update functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from pathlib import Path

import pytest

from sqliter import SqliterDB
from sqliter.exceptions import InvalidUpdateError
from sqliter.model.model import BaseDBModel
from sqliter.orm import BaseDBModel as ORMBaseDBModel
from sqliter.orm import ForeignKey

# ── Test models ──────────────────────────────────────────────────────


class SimpleModel(BaseDBModel):
    """Simple model for basic bulk update tests."""

    name: str
    value: int = 0
    status: str = "active"


class GroupModel(BaseDBModel):
    """Model for testing the issue's specific use case (group reassignment)."""

    title: str
    group_id: int = 0
    category: str = "default"


class TimestampModel(BaseDBModel):
    """Model for testing timestamp behavior on update."""

    label: str


class ParentModel(ORMBaseDBModel):
    """Parent model for FK constraint tests."""

    name: str


class ChildModel(ORMBaseDBModel):
    """Child model with FK for constraint tests."""

    title: str
    parent: ForeignKey[ParentModel] = ForeignKey(
        ParentModel, on_delete="CASCADE"
    )


class UniqueModel(BaseDBModel):
    """Model with a unique constraint for testing constraints."""

    class Meta:
        """Meta class for unique indexes."""

        unique_indexes: ClassVar[list[str]] = ["code"]

    code: str
    description: str = ""


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
def db() -> SqliterDB:
    """Create an in-memory database with test tables."""
    database = SqliterDB(memory=True)
    database.create_table(SimpleModel)
    database.create_table(GroupModel)
    database.create_table(TimestampModel)
    database.create_table(ParentModel)
    database.create_table(ChildModel)
    database.create_table(UniqueModel)
    return database


# ── Tests: QueryBuilder.update() ─────────────────────────────────────


class TestQueryBuilderUpdateBasic:
    """Basic QueryBuilder.update() functionality."""

    def test_update_single_field_single_row(self, db: SqliterDB) -> None:
        """Update a single field on a single row."""
        # Insert test data
        db.insert(SimpleModel(name="original", value=10))

        # Update using QueryBuilder
        count = db.select(SimpleModel).filter(pk=1).update({"value": 20})

        assert count == 1
        # Verify the update
        result = db.get(SimpleModel, 1)
        assert result is not None
        assert result.value == 20
        assert result.name == "original"  # Unchanged

    def test_update_multiple_fields(self, db: SqliterDB) -> None:
        """Update multiple fields at once."""
        db.insert(SimpleModel(name="test", value=10, status="active"))

        count = (
            db.select(SimpleModel)
            .filter(pk=1)
            .update({"value": 30, "status": "inactive"})
        )

        assert count == 1
        result = db.get(SimpleModel, 1)
        assert result is not None
        assert result.value == 30
        assert result.status == "inactive"

    def test_update_multiple_rows(self, db: SqliterDB) -> None:
        """Update multiple rows that match the filter."""
        # Insert multiple records
        db.bulk_insert(
            [
                SimpleModel(name="a", value=1),
                SimpleModel(name="b", value=1),
                SimpleModel(name="c", value=1),
            ]
        )

        # Update all where value=1
        count = db.select(SimpleModel).filter(value=1).update({"value": 100})

        assert count == 3

        # Verify all updated
        results = db.select(SimpleModel).fetch_all()
        for r in results:
            assert r.value == 100

    def test_update_zero_rows_no_match(self, db: SqliterDB) -> None:
        """Update returns 0 when no rows match."""
        db.insert(SimpleModel(name="test", value=10))

        count = db.select(SimpleModel).filter(value=999).update({"value": 50})

        assert count == 0
        # Original should be unchanged
        result = db.get(SimpleModel, 1)
        assert result is not None
        assert result.value == 10


class TestQueryBuilderUpdateFilters:
    """Test update with various filter types."""

    def test_update_with_greater_than(self, db: SqliterDB) -> None:
        """Update with __gt filter."""
        db.bulk_insert(
            [
                SimpleModel(name="low", value=5),
                SimpleModel(name="high", value=15),
                SimpleModel(name="mid", value=10),
            ]
        )

        count = (
            db.select(SimpleModel)
            .filter(value__gt=10)
            .update({"status": "high"})
        )

        assert count == 1
        results = db.select(SimpleModel).fetch_all()
        for r in results:
            if r.name == "high":
                assert r.status == "high"
            else:
                assert r.status == "active"

    def test_update_with_in_operator(self, db: SqliterDB) -> None:
        """Update with __in filter."""
        db.bulk_insert(
            [
                SimpleModel(name="a", value=1),
                SimpleModel(name="b", value=2),
                SimpleModel(name="c", value=3),
            ]
        )

        count = (
            db.select(SimpleModel)
            .filter(value__in=[1, 3])
            .update({"status": "odd"})
        )

        assert count == 2

    def test_update_with_multiple_filters(self, db: SqliterDB) -> None:
        """Update with multiple filter conditions."""
        db.bulk_insert(
            [
                SimpleModel(name="a", value=1, status="active"),
                SimpleModel(name="b", value=1, status="inactive"),
                SimpleModel(name="c", value=2, status="active"),
            ]
        )

        count = (
            db.select(SimpleModel)
            .filter(value=1, status="active")
            .update({"status": "updated"})
        )

        assert count == 1
        result = db.get(SimpleModel, 1)
        assert result is not None
        assert result.status == "updated"


class TestQueryBuilderUpdateErrors:
    """Test error handling in QueryBuilder.update()."""

    def test_update_invalid_field_raises_error(self, db: SqliterDB) -> None:
        """Updating an invalid field raises InvalidUpdateError."""
        db.insert(SimpleModel(name="test", value=10))

        with pytest.raises(InvalidUpdateError) as exc_info:
            db.select(SimpleModel).filter(pk=1).update({"invalid_field": 42})

        assert "invalid_field" in str(exc_info.value)

    def test_update_multiple_invalid_fields(self, db: SqliterDB) -> None:
        """Multiple invalid fields are reported."""
        db.insert(SimpleModel(name="test", value=10))

        with pytest.raises(InvalidUpdateError) as exc_info:
            db.select(SimpleModel).filter(pk=1).update({"foo": 1, "bar": 2})

        error_msg = str(exc_info.value)
        assert "foo" in error_msg
        assert "bar" in error_msg


# ── Tests: SqliterDB.update_where() ───────────────────────────────────


class TestUpdateWhereBasic:
    """Basic SqliterDB.update_where() functionality."""

    def test_update_where_simple_filter(self, db: SqliterDB) -> None:
        """Simple where filter works."""
        db.insert(SimpleModel(name="test", value=10))

        count = db.update_where(
            SimpleModel, where={"pk": 1}, values={"value": 25}
        )

        assert count == 1
        result = db.get(SimpleModel, 1)
        assert result is not None
        assert result.value == 25

    def test_update_where_matches_issue_use_case(self, db: SqliterDB) -> None:
        """Test the exact use case from issue #125 - group reassignment."""
        # Insert ideas in different groups
        db.bulk_insert(
            [
                GroupModel(title="Idea 1", group_id=1),
                GroupModel(title="Idea 2", group_id=1),
                GroupModel(title="Idea 3", group_id=2),
                GroupModel(title="Idea 4", group_id=1),
            ]
        )

        # Move all ideas from group 1 to group 10 (issue #125 use case)
        count = db.update_where(
            GroupModel, where={"group_id": 1}, values={"group_id": 10}
        )

        assert count == 3  # 3 ideas were in group 1

        # Verify
        results = db.select(GroupModel).fetch_all()
        for r in results:
            if r.title in ["Idea 1", "Idea 2", "Idea 4"]:
                assert r.group_id == 10
            else:
                assert r.group_id == 2  # Idea 3 stays in group 2

    def test_update_where_no_matches(self, db: SqliterDB) -> None:
        """update_where returns 0 when no matches."""
        db.insert(SimpleModel(name="test", value=10))

        count = db.update_where(
            SimpleModel, where={"value": 999}, values={"value": 50}
        )

        assert count == 0


class TestUpdateWhereFilters:
    """Test update_where with various filter types."""

    def test_update_where_with_operator(self, db: SqliterDB) -> None:
        """Update with comparison operators."""
        db.bulk_insert(
            [
                SimpleModel(name="a", value=5),
                SimpleModel(name="b", value=10),
                SimpleModel(name="c", value=15),
            ]
        )

        # Update all where value > 10
        count = db.update_where(
            SimpleModel, where={"value__gt": 10}, values={"status": "high"}
        )

        assert count == 1
        results = db.select(SimpleModel).fetch_all()
        for r in results:
            if r.value > 10:
                assert r.status == "high"

    def test_update_where_with_in(self, db: SqliterDB) -> None:
        """Update with __in filter."""
        db.bulk_insert(
            [
                SimpleModel(name="a", value=1),
                SimpleModel(name="b", value=2),
                SimpleModel(name="c", value=3),
            ]
        )

        count = db.update_where(
            SimpleModel, where={"value__in": [1, 2]}, values={"status": "low"}
        )

        assert count == 2


class TestUpdateWhereErrors:
    """Test error handling in update_where()."""

    def test_update_where_invalid_field(self, db: SqliterDB) -> None:
        """Invalid field in values raises InvalidUpdateError."""
        db.insert(SimpleModel(name="test", value=10))

        with pytest.raises(InvalidUpdateError):
            db.update_where(
                SimpleModel, where={"pk": 1}, values={"nonexistent": 42}
            )


# ── Tests: Cache Invalidation ───────────────────────────────────────


class TestBulkUpdateCache:
    """Test cache invalidation on bulk update."""

    def test_cache_invalidated_after_update(self) -> None:
        """Cache is invalidated after update."""
        db = SqliterDB(memory=True, cache_enabled=True)
        db.create_table(SimpleModel)

        # Insert and prime the cache
        db.insert(SimpleModel(name="test", value=10))
        db.select(SimpleModel).fetch_all()

        # Update should invalidate cache
        db.select(SimpleModel).filter(pk=1).update({"value": 20})

        # Verify fresh data
        results = db.select(SimpleModel).fetch_all()
        assert len(results) == 1
        assert results[0].value == 20


# ── Tests: Transaction Handling ─────────────────────────────────────


class TestBulkUpdateTransaction:
    """Test transaction handling in bulk update."""

    def test_update_within_transaction(self, tmp_path: Path) -> None:
        """Update within a transaction defers commit."""
        db_path = str(tmp_path / "txn_test.db")
        db = SqliterDB(db_path)
        db.create_table(SimpleModel)

        db.insert(SimpleModel(name="original", value=10))

        with db:
            count = db.select(SimpleModel).filter(pk=1).update({"value": 50})
            assert count == 1

        # Verify data persisted after context exit
        db2 = SqliterDB(db_path)
        db2.create_table(SimpleModel)
        result = db2.get(SimpleModel, 1)
        assert result is not None
        assert result.value == 50
        db2.close()

    def test_update_rollback_on_error(self, db: SqliterDB) -> None:
        """Update rolls back on error when possible."""
        db.insert(SimpleModel(name="test", value=10))
        result = db.get(SimpleModel, 1)
        assert result is not None
        original_value = result.value

        # Note: Since we validate fields before executing,
        # we test that validation errors don't leave partial state
        with pytest.raises(InvalidUpdateError):
            db.select(SimpleModel).filter(pk=1).update({"invalid_field": 42})

        # Verify no change
        result = db.get(SimpleModel, 1)
        assert result is not None
        assert result.value == original_value


# ── Tests: Edge Cases ─────────────────────────────────────────────


class TestBulkUpdateEdgeCases:
    """Edge case tests."""

    def test_update_without_filter(self, db: SqliterDB) -> None:
        """Update without filter updates all rows."""
        db.bulk_insert(
            [
                SimpleModel(name="a", value=1),
                SimpleModel(name="b", value=2),
                SimpleModel(name="c", value=3),
            ]
        )

        # Update all records
        count = db.select(SimpleModel).update({"status": "all"})

        assert count == 3

        results = db.select(SimpleModel).fetch_all()
        for r in results:
            assert r.status == "all"

    def test_update_preserves_other_fields(self, db: SqliterDB) -> None:
        """Updating one field preserves others."""
        db.insert(SimpleModel(name="test", value=10, status="active"))

        db.select(SimpleModel).filter(pk=1).update({"value": 99})

        result = db.get(SimpleModel, 1)
        assert result is not None
        assert result.name == "test"
        assert result.value == 99
        assert result.status == "active"
