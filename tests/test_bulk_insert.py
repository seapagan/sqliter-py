"""Tests for SqliterDB.bulk_insert() method."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from pathlib import Path

import pytest
from pydantic import Field

from sqliter import SqliterDB
from sqliter.exceptions import (
    ForeignKeyConstraintError,
    RecordInsertionError,
)
from sqliter.model.model import BaseDBModel
from sqliter.orm import BaseDBModel as ORMBaseDBModel
from sqliter.orm import ForeignKey

# ── Test models ──────────────────────────────────────────────────────


class SimpleModel(BaseDBModel):
    """Simple model for basic bulk insert tests."""

    name: str
    value: int = 0


class TimestampModel(BaseDBModel):
    """Model for testing timestamp behavior."""

    label: str


class ComplexModel(BaseDBModel):
    """Model with complex field types."""

    name: str
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, int] = Field(default_factory=dict)


class UniqueModel(BaseDBModel):
    """Model with a unique constraint for error testing."""

    class Meta:
        """Meta class for unique indexes."""

        unique_indexes: ClassVar[list[str]] = ["code"]

    code: str
    description: str = ""


class ParentModel(ORMBaseDBModel):
    """Parent model for FK constraint tests."""

    name: str


class ChildModel(ORMBaseDBModel):
    """Child model with FK for constraint tests."""

    title: str
    parent: ForeignKey[ParentModel] = ForeignKey(
        ParentModel, on_delete="CASCADE"
    )


class OtherModel(BaseDBModel):
    """A different model type for mixed-type tests."""

    color: str


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
def db() -> SqliterDB:
    """Create an in-memory database with test tables."""
    database = SqliterDB(memory=True)
    database.create_table(SimpleModel)
    database.create_table(TimestampModel)
    database.create_table(ComplexModel)
    database.create_table(UniqueModel)
    database.create_table(ParentModel)
    database.create_table(ChildModel)
    database.create_table(OtherModel)
    return database


# ── Tests ────────────────────────────────────────────────────────────


class TestBulkInsertBasic:
    """Basic bulk insert functionality."""

    def test_bulk_insert_multiple_records(self, db: SqliterDB) -> None:
        """Bulk insert returns instances with sequential PKs."""
        instances = [
            SimpleModel(name="a", value=1),
            SimpleModel(name="b", value=2),
            SimpleModel(name="c", value=3),
        ]
        results = db.bulk_insert(instances)

        assert len(results) == 3
        assert results[0].pk == 1
        assert results[1].pk == 2
        assert results[2].pk == 3

    def test_bulk_insert_empty_list(self, db: SqliterDB) -> None:
        """Bulk insert with an empty list returns []."""
        results: list[SimpleModel] = db.bulk_insert([])
        assert results == []

    def test_bulk_insert_single_item(self, db: SqliterDB) -> None:
        """Bulk insert with a single item works correctly."""
        results = db.bulk_insert([SimpleModel(name="only", value=42)])

        assert len(results) == 1
        assert results[0].pk == 1
        assert results[0].name == "only"
        assert results[0].value == 42

    def test_bulk_insert_large_batch(self, db: SqliterDB) -> None:
        """Bulk insert with a large batch assigns unique PKs."""
        instances = [SimpleModel(name=f"item_{i}", value=i) for i in range(500)]
        results = db.bulk_insert(instances)

        assert len(results) == 500
        pks = [r.pk for r in results]
        assert len(set(pks)) == 500

    def test_bulk_insert_field_values_match(self, db: SqliterDB) -> None:
        """Returned instances have correct field values."""
        instances = [
            SimpleModel(name="alpha", value=10),
            SimpleModel(name="beta", value=20),
        ]
        results = db.bulk_insert(instances)

        assert results[0].name == "alpha"
        assert results[0].value == 10
        assert results[1].name == "beta"
        assert results[1].value == 20


class TestBulkInsertTimestamps:
    """Timestamp handling in bulk insert."""

    def test_timestamps_set(self, db: SqliterDB) -> None:
        """created_at and updated_at are populated."""
        before = int(time.time())
        results = db.bulk_insert(
            [
                TimestampModel(label="first"),
                TimestampModel(label="second"),
            ]
        )
        after = int(time.time())

        for r in results:
            assert before <= r.created_at <= after
            assert before <= r.updated_at <= after

    def test_timestamp_override_preserves_values(self, db: SqliterDB) -> None:
        """timestamp_override=True preserves provided non-zero values."""
        results = db.bulk_insert(
            [
                TimestampModel(
                    label="custom",
                    created_at=1000000,
                    updated_at=2000000,
                ),
            ],
            timestamp_override=True,
        )

        assert results[0].created_at == 1000000
        assert results[0].updated_at == 2000000

    def test_timestamp_override_fills_zeros(self, db: SqliterDB) -> None:
        """timestamp_override=True fills in zero-valued timestamps."""
        results = db.bulk_insert(
            [TimestampModel(label="partial", created_at=1000000)],
            timestamp_override=True,
        )

        assert results[0].created_at == 1000000
        assert results[0].updated_at > 0


class TestBulkInsertComplexTypes:
    """Complex type serialization in bulk insert."""

    def test_complex_types_serialized(self, db: SqliterDB) -> None:
        """Lists and dicts are serialized and retrievable."""
        results = db.bulk_insert(
            [
                ComplexModel(
                    name="complex",
                    tags=["python", "sqlite"],
                    metadata={"version": 3},
                ),
            ]
        )

        assert results[0].pk is not None
        assert results[0].tags == ["python", "sqlite"]
        assert results[0].metadata == {"version": 3}

        # Verify by reading back from DB
        fetched = db.get(ComplexModel, results[0].pk)
        assert fetched is not None
        assert fetched.tags == ["python", "sqlite"]
        assert fetched.metadata == {"version": 3}


class TestBulkInsertErrorHandling:
    """Error handling in bulk insert."""

    def test_rollback_on_integrity_error(self, db: SqliterDB) -> None:
        """IntegrityError mid-batch rolls back all inserts."""
        db.insert(UniqueModel(code="unique", description="first"))

        with pytest.raises(RecordInsertionError):
            db.bulk_insert(
                [
                    UniqueModel(code="ok", description="fine"),
                    UniqueModel(code="unique", description="duplicate"),
                ]
            )

        # The first item in the batch should also be rolled back
        count = db.select(UniqueModel).count()
        assert count == 1  # Only the original pre-existing one

    def test_fk_constraint_error(self, db: SqliterDB) -> None:
        """FK constraint violation raises ForeignKeyConstraintError."""
        with pytest.raises(ForeignKeyConstraintError):
            db.bulk_insert(
                [
                    ChildModel(title="orphan", parent_id=9999),
                ]
            )

    def test_mixed_model_types_raises_value_error(self, db: SqliterDB) -> None:
        """Passing mixed model types raises ValueError."""
        with pytest.raises(ValueError, match="All instances must be"):
            db.bulk_insert(
                [
                    SimpleModel(name="a"),
                    OtherModel(color="red"),
                ]
            )

    def test_sqlite_error_rollback(self) -> None:
        """Generic sqlite3.Error triggers rollback."""
        db = SqliterDB(memory=True)
        # Don't create the table — insert should fail with sqlite error
        with pytest.raises(RecordInsertionError):
            db.bulk_insert([SimpleModel(name="fail")])


class TestBulkInsertTransaction:
    """Transaction context handling."""

    def test_within_transaction_defers_commit(self, tmp_path: Path) -> None:
        """Within `with db:`, commit is deferred to context exit."""
        db_path = str(tmp_path / "txn_test.db")
        db = SqliterDB(db_path)
        db.create_table(SimpleModel)

        with db:
            results = db.bulk_insert(
                [
                    SimpleModel(name="txn1", value=1),
                    SimpleModel(name="txn2", value=2),
                ]
            )
            assert len(results) == 2

        # Reopen and verify data persisted after context exit
        db2 = SqliterDB(db_path)
        db2.create_table(SimpleModel)
        count = db2.select(SimpleModel).count()
        assert count == 2
        db2.close()


class TestBulkInsertDBContext:
    """db_context set on returned instances."""

    def test_db_context_set_on_returned_instances(self, db: SqliterDB) -> None:
        """Returned instances have db_context set."""
        results = db.bulk_insert(
            [
                SimpleModel(name="ctx1"),
                SimpleModel(name="ctx2"),
            ]
        )

        for r in results:
            if hasattr(r, "db_context"):
                assert r.db_context is db


class TestBulkInsertCache:
    """Cache invalidation behavior."""

    def test_cache_invalidated_after_bulk_insert(self) -> None:
        """Cache is invalidated once after a successful bulk insert."""
        db = SqliterDB(memory=True, cache_enabled=True)
        db.create_table(SimpleModel)

        # Prime the cache
        db.select(SimpleModel).fetch_all()

        # Bulk insert should invalidate
        db.bulk_insert([SimpleModel(name="new", value=1)])

        # Subsequent select should reflect the new data
        results = db.select(SimpleModel).fetch_all()
        assert len(results) == 1
        assert results[0].name == "new"
