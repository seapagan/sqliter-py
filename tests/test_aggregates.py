"""Tests for aggregate/group-by projection query support."""

from __future__ import annotations

import sqlite3
from re import escape
from typing import Any

import pytest

from sqliter.exceptions import (
    InvalidProjectionError,
    InvalidRelationshipError,
    RecordFetchError,
)
from sqliter.orm import BaseDBModel, ForeignKey, ManyToMany
from sqliter.query import AggregateSpec, func
from sqliter.sqliter import SqliterDB


class Sale(BaseDBModel):
    """Simple model for aggregate tests."""

    category: str
    amount: float


class AuthorAgg(BaseDBModel):
    """Author model for reverse-FK with_count tests."""

    name: str


class BookAgg(BaseDBModel):
    """Book model for reverse-FK with_count tests."""

    title: str
    author: ForeignKey[AuthorAgg] = ForeignKey(
        AuthorAgg,
        on_delete="CASCADE",
        related_name="books",
    )


class TagAgg(BaseDBModel):
    """Tag model for M2M with_count tests."""

    name: str


class ArticleAgg(BaseDBModel):
    """Article model for M2M with_count tests."""

    title: str
    tags: ManyToMany[TagAgg] = ManyToMany(TagAgg, related_name="articles")


class UnresolvedOwnerAgg(BaseDBModel):
    """Model with unresolved M2M target for error-path testing."""

    name: str
    pending: ManyToMany[Any] = ManyToMany("MissingAgg")


def _build_sales_db(*, cache_enabled: bool = False) -> SqliterDB:
    """Create the shared sales fixture data set."""
    db = SqliterDB(":memory:", cache_enabled=cache_enabled)
    db.create_table(Sale)
    db.insert(Sale(category="books", amount=10.0))
    db.insert(Sale(category="books", amount=15.0))
    db.insert(Sale(category="books", amount=20.0))
    db.insert(Sale(category="games", amount=40.0))
    db.insert(Sale(category="music", amount=5.0))
    return db


@pytest.fixture
def sales_db() -> SqliterDB:
    """Create aggregate test data for grouped reports."""
    return _build_sales_db()


@pytest.fixture
def sales_db_cached() -> SqliterDB:
    """Create aggregate test data with query cache enabled."""
    return _build_sales_db(cache_enabled=True)


@pytest.fixture
def relation_db() -> SqliterDB:
    """Create ORM relation fixtures for with_count tests."""
    db = SqliterDB(":memory:")
    db.create_table(AuthorAgg)
    db.create_table(BookAgg)
    db.create_table(TagAgg)
    db.create_table(ArticleAgg)

    alice = db.insert(AuthorAgg(name="Alice"))
    bob = db.insert(AuthorAgg(name="Bob"))
    db.insert(AuthorAgg(name="No Books"))

    db.insert(BookAgg(title="A1", author=alice))
    db.insert(BookAgg(title="A2", author=alice))
    db.insert(BookAgg(title="B1", author=bob))

    python = db.insert(TagAgg(name="python"))
    sqlite = db.insert(TagAgg(name="sqlite"))
    db.insert(TagAgg(name="unused"))

    guide = db.insert(ArticleAgg(title="Guide"))
    tips = db.insert(ArticleAgg(title="Tips"))
    db.insert(ArticleAgg(title="No Tags"))

    guide.tags.add(python, sqlite)
    tips.tags.add(python)
    return db


def test_group_by_aggregate_helpers_and_having(sales_db: SqliterDB) -> None:
    """Grouped projection supports aggregate helpers and HAVING filters."""
    rows = (
        sales_db.select(Sale)
        .group_by("category")
        .annotate(
            total=func.sum("amount"),
            average=func.avg("amount"),
            lowest=func.min("amount"),
            highest=func.max("amount"),
            entries=func.count("amount"),
        )
        .having(total__gt=20)
        .order("total", reverse=True)
        .fetch_dicts()
    )

    assert rows == [
        {
            "category": "books",
            "total": 45.0,
            "average": 15.0,
            "lowest": 10.0,
            "highest": 20.0,
            "entries": 3,
        },
        {
            "category": "games",
            "total": 40.0,
            "average": 40.0,
            "lowest": 40.0,
            "highest": 40.0,
            "entries": 1,
        },
    ]


def test_aggregate_only_projection_returns_dict_rows(
    sales_db: SqliterDB,
) -> None:
    """Aggregate-only projections work without GROUP BY."""
    rows = (
        sales_db.select(Sale)
        .annotate(total_rows=func.count(), total_amount=func.sum("amount"))
        .fetch_dicts()
    )

    assert rows == [{"total_rows": 5, "total_amount": 90.0}]


def test_projection_mode_rejects_model_fetch_methods(
    sales_db: SqliterDB,
) -> None:
    """Projection queries should require fetch_dicts()."""
    query = (
        sales_db.select(Sale)
        .group_by("category")
        .annotate(total=func.sum("amount"))
    )

    with pytest.raises(InvalidProjectionError, match="fetch_dicts"):
        query.fetch_all()


def test_with_count_reverse_fk_includes_zero_rows(
    relation_db: SqliterDB,
) -> None:
    """with_count on reverse FK includes parents with no children."""
    rows = (
        relation_db.select(AuthorAgg)
        .with_count("books", alias="usage")
        .order("name")
        .fetch_dicts()
    )

    usage_by_name = {row["name"]: row["usage"] for row in rows}
    assert usage_by_name == {"Alice": 2, "Bob": 1, "No Books": 0}


def test_with_count_reverse_m2m_includes_zero_rows(
    relation_db: SqliterDB,
) -> None:
    """with_count on reverse M2M includes rows with no relations."""
    rows = (
        relation_db.select(TagAgg)
        .with_count("articles", alias="usage")
        .order("name")
        .fetch_dicts()
    )

    usage_by_tag = {row["name"]: row["usage"] for row in rows}
    assert usage_by_tag == {"python": 2, "sqlite": 1, "unused": 0}


def test_with_count_forward_m2m_includes_zero_rows(
    relation_db: SqliterDB,
) -> None:
    """with_count on forward M2M includes rows with zero related entries."""
    rows = (
        relation_db.select(ArticleAgg)
        .with_count("tags", alias="usage")
        .order("title")
        .fetch_dicts()
    )

    usage_by_article = {row["title"]: row["usage"] for row in rows}
    assert usage_by_article == {"Guide": 2, "No Tags": 0, "Tips": 1}


def test_with_count_supports_having_filter(relation_db: SqliterDB) -> None:
    """HAVING can filter on aggregate aliases from with_count()."""
    rows = (
        relation_db.select(AuthorAgg)
        .with_count("books", alias="usage")
        .having(usage__gt=1)
        .fetch_dicts()
    )

    assert len(rows) == 1
    assert rows[0]["name"] == "Alice"
    assert rows[0]["usage"] == 2


def test_with_count_reuses_join_for_same_path_with_multiple_aliases(
    relation_db: SqliterDB,
) -> None:
    """Counting the same relationship twice should not duplicate joins."""
    rows = (
        relation_db.select(AuthorAgg)
        .with_count("books", alias="first")
        .with_count("books", alias="second")
        .order("name")
        .fetch_dicts()
    )

    counts_by_name = {
        row["name"]: (row["first"], row["second"]) for row in rows
    }
    assert counts_by_name == {
        "Alice": (2, 2),
        "Bob": (1, 1),
        "No Books": (0, 0),
    }


def test_aggregate_spec_requires_field_for_non_count() -> None:
    """SUM/MIN/MAX/AVG must specify a concrete source field."""
    with pytest.raises(ValueError, match="requires a concrete field"):
        AggregateSpec(func="SUM")


def test_projection_noop_methods_keep_non_projection_mode(
    sales_db: SqliterDB,
) -> None:
    """group_by/annotate/having with no args should be no-ops."""
    query = sales_db.select(Sale)
    assert query.group_by() is query
    assert query.annotate() is query
    assert query.having() is query
    assert query.fetch_all()


def test_annotate_rejects_empty_conflicting_and_duplicate_aliases(
    sales_db: SqliterDB,
) -> None:
    """annotate() should reject invalid aliases."""
    with pytest.raises(InvalidProjectionError, match="cannot be empty"):
        sales_db.select(Sale).annotate(**{"   ": func.count()})

    with pytest.raises(InvalidProjectionError, match="conflicts with model"):
        sales_db.select(Sale).annotate(category=func.count())

    query = sales_db.select(Sale).annotate(total=func.sum("amount"))
    with pytest.raises(InvalidProjectionError, match="already defined"):
        query.annotate(total=func.avg("amount"))

    with pytest.raises(InvalidProjectionError, match="cannot contain"):
        sales_db.select(Sale).annotate(**{'bad"alias': func.count()})


def test_group_by_and_annotate_validate_input(sales_db: SqliterDB) -> None:
    """group_by()/annotate() should validate fields and value types."""
    with pytest.raises(InvalidProjectionError, match="Cannot group by"):
        sales_db.select(Sale).group_by("missing")

    with pytest.raises(TypeError, match="AggregateSpec instances"):
        sales_db.select(Sale).annotate(total="not-an-aggregate")  # type: ignore[arg-type]

    with pytest.raises(InvalidProjectionError, match="is not a field"):
        sales_db.select(Sale).annotate(total=func.sum("missing"))


def test_having_requires_projection_mode(sales_db: SqliterDB) -> None:
    """having() is only valid for projection queries."""
    with pytest.raises(InvalidProjectionError, match="requires projection"):
        sales_db.select(Sale).having(category="books")


def test_having_accepts_grouped_and_aggregate_fields(
    sales_db: SqliterDB,
) -> None:
    """HAVING can target grouped columns and aggregate aliases."""
    rows = (
        sales_db.select(Sale)
        .group_by("category")
        .annotate(total=func.sum("amount"))
        .having(category__like="%oo%")
        .having(total__gt=40)
        .fetch_dicts()
    )

    assert rows == [{"category": "books", "total": 45.0}]

    eq_rows = (
        sales_db.select(Sale)
        .group_by("category")
        .annotate(total=func.sum("amount"))
        .having(category="books")
        .fetch_dicts()
    )
    assert eq_rows == [{"category": "books", "total": 45.0}]

    null_rows = (
        sales_db.select(Sale)
        .group_by("category")
        .annotate(total=func.sum("amount"))
        .having(category=None)
        .fetch_dicts()
    )
    assert null_rows == []


def test_having_rejects_fields_outside_group_or_aggregate(
    sales_db: SqliterDB,
) -> None:
    """HAVING should reject non-grouped, non-aggregate fields."""
    with pytest.raises(InvalidProjectionError, match="must be a grouped field"):
        (
            sales_db.select(Sale)
            .group_by("category")
            .annotate(total=func.sum("amount"))
            .having(amount__gt=10)
        )


def test_having_operator_variants_and_type_validation(
    sales_db: SqliterDB,
) -> None:
    """HAVING should support null/in/like operators and validate types."""
    rows = (
        sales_db.select(Sale)
        .group_by("category")
        .annotate(total=func.sum("amount"))
        .having(category__notnull=True)
        .having(category__in=["books", "music"])
        .having(category__not_in=["music"])
        .having(category__icontains="BO")
        .fetch_dicts()
    )

    assert rows == [{"category": "books", "total": 45.0}]

    with pytest.raises(TypeError, match="requires a list"):
        (
            sales_db.select(Sale)
            .group_by("category")
            .annotate(total=func.sum("amount"))
            .having(category__in="books")
            .fetch_dicts()
        )

    with pytest.raises(TypeError, match="requires a string value"):
        (
            sales_db.select(Sale)
            .group_by("category")
            .annotate(total=func.sum("amount"))
            .having(category__like=1)
            .fetch_dicts()
        )

    with pytest.raises(TypeError, match="requires scalar"):
        (
            sales_db.select(Sale)
            .group_by("category")
            .annotate(total=func.sum("amount"))
            .having(total__gt=[1])
            .fetch_dicts()
        )

    with pytest.raises(TypeError, match="requires scalar"):
        (
            sales_db.select(Sale)
            .group_by("category")
            .annotate(total=func.sum("amount"))
            .having(category=["books"])
            .fetch_dicts()
        )


def test_with_count_validation_errors(relation_db: SqliterDB) -> None:
    """with_count() should validate path shape and relationship type."""
    with pytest.raises(InvalidProjectionError, match="single relationship"):
        relation_db.select(AuthorAgg).with_count("books__author")

    with pytest.raises(InvalidRelationshipError):
        relation_db.select(AuthorAgg).with_count("unknown")

    with pytest.raises(InvalidRelationshipError):
        relation_db.select(AuthorAgg).with_count("name")

    with pytest.raises(InvalidRelationshipError):
        relation_db.select(AuthorAgg).with_count("Meta")

    with pytest.raises(
        InvalidProjectionError, match="Cannot resolve SQL metadata"
    ):
        relation_db.select(UnresolvedOwnerAgg).with_count("pending")


def test_count_distinct_star_is_rejected(sales_db: SqliterDB) -> None:
    """COUNT(DISTINCT *) should raise a projection error."""
    with pytest.raises(InvalidProjectionError, match="DISTINCT with COUNT"):
        sales_db.select(Sale).annotate(
            total=func.count(distinct=True)
        ).fetch_dicts()


def test_projection_order_clause_fallback_and_validation(
    sales_db: SqliterDB,
) -> None:
    """Projection ORDER BY should handle malformed and invalid fields."""
    query = (
        sales_db.select(Sale)
        .group_by("category")
        .annotate(total=func.sum("amount"))
    )

    query._order_by = "rowid DESC"
    assert query._build_projection_order_clause() == ""

    query._order_by = '"unknown" ASC'
    with pytest.raises(InvalidProjectionError, match="ORDER BY field"):
        query._build_projection_order_clause()


def test_projection_query_requires_selected_columns(
    sales_db: SqliterDB,
) -> None:
    """Projection mode with no selected columns should fail fast."""
    query = sales_db.select(Sale)
    query._projection_mode = True
    with pytest.raises(InvalidProjectionError, match="no selected columns"):
        query._build_projection_sql()


def test_projection_sql_includes_joins_filters_and_pagination(
    relation_db: SqliterDB,
) -> None:
    """Projection SQL should support joins, WHERE, LIMIT, and OFFSET."""
    rows = (
        relation_db.select(AuthorAgg)
        .filter(name__not_in=["No Books"])
        .with_count("books", alias="usage")
        .order("name")
        .limit(1)
        .offset(1)
        .fetch_dicts()
    )

    assert len(rows) == 1
    assert rows[0]["name"] == "Bob"
    assert rows[0]["usage"] == 1


def test_projection_query_sqlite_error_raises_record_fetch_error(
    sales_db: SqliterDB, monkeypatch: pytest.MonkeyPatch
) -> None:
    """sqlite3 errors in projection execution should map to RecordFetchError."""
    query = (
        sales_db.select(Sale)
        .group_by("category")
        .annotate(total=func.sum("amount"))
    )

    def raise_sqlite_error(*_args, **_kwargs) -> None:  # noqa: ANN002, ANN003
        err = "broken"
        raise sqlite3.Error(err)

    monkeypatch.setattr(sales_db, "_execute", raise_sqlite_error)

    with pytest.raises(RecordFetchError):
        query.fetch_dicts()


def test_fetch_dicts_requires_projection_mode(sales_db: SqliterDB) -> None:
    """fetch_dicts() is not valid for non-projection queries."""
    with pytest.raises(
        InvalidProjectionError, match="requires projection mode"
    ):
        sales_db.select(Sale).fetch_dicts()


@pytest.mark.parametrize(
    "method_name",
    ["fetch_one", "fetch_first", "fetch_last", "count", "exists"],
)
def test_projection_mode_rejects_other_model_fetch_methods(
    sales_db: SqliterDB, method_name: str
) -> None:
    """Projection mode should reject model-oriented fetch/count methods."""
    query = (
        sales_db.select(Sale)
        .group_by("category")
        .annotate(total=func.sum("amount"))
    )

    expected = escape(f"{method_name}() is unavailable")
    with pytest.raises(InvalidProjectionError, match=expected):
        getattr(query, method_name)()


def test_projection_query_reuses_cached_results(
    sales_db_cached: SqliterDB, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Second fetch_dicts() call should be served from cache."""
    query = (
        sales_db_cached.select(Sale)
        .group_by("category")
        .annotate(total=func.sum("amount"))
    )
    first = query.fetch_dicts()

    def fail_execute_projection() -> list[tuple[object, ...]]:
        err = "Projection query should not execute when cache is warm."
        raise AssertionError(err)

    monkeypatch.setattr(
        query, "_execute_projection_query", fail_execute_projection
    )
    second = query.fetch_dicts()

    assert second == first


def test_projection_cache_key_is_stable_pre_and_post_execution(
    sales_db_cached: SqliterDB,
) -> None:
    """Projection cache key should not change as a side effect of execution."""
    query = (
        sales_db_cached.select(Sale)
        .group_by("category")
        .annotate(total=func.sum("amount"))
    )
    key_before = query._make_cache_key(fetch_one=False)

    _ = query.fetch_dicts()

    key_after = query._make_cache_key(fetch_one=False)
    assert key_after == key_before


def test_projection_cache_hits_across_equivalent_query_builders(
    sales_db_cached: SqliterDB, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Equivalent projection queries should share cached results."""
    first_query = (
        sales_db_cached.select(Sale)
        .group_by("category")
        .annotate(total=func.sum("amount"))
    )
    expected = first_query.fetch_dicts()

    second_query = (
        sales_db_cached.select(Sale)
        .group_by("category")
        .annotate(total=func.sum("amount"))
    )

    def fail_execute_projection() -> list[tuple[object, ...]]:
        err = "Projection query should hit cache across query builders."
        raise AssertionError(err)

    monkeypatch.setattr(
        second_query, "_execute_projection_query", fail_execute_projection
    )
    cached = second_query.fetch_dicts()

    assert cached == expected
