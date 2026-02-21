"""Aggregate specification helpers for grouped projection queries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

AggregateFunction = Literal["COUNT", "SUM", "AVG", "MIN", "MAX"]


@dataclass(frozen=True)
class AggregateSpec:
    """Represents a SQL aggregate function projection."""

    func: AggregateFunction
    field: Optional[str] = None
    distinct: bool = False

    def __post_init__(self) -> None:
        """Validate aggregate configuration."""
        if self.func != "COUNT" and self.field in {None, "*"}:
            msg = f"{self.func} requires a concrete field name."
            raise ValueError(msg)


def count(
    field: Optional[str] = None, *, distinct: bool = False
) -> AggregateSpec:
    """Build a COUNT aggregate specification."""
    return AggregateSpec(func="COUNT", field=field, distinct=distinct)


def sum_(field: str, *, distinct: bool = False) -> AggregateSpec:
    """Build a SUM aggregate specification."""
    return AggregateSpec(func="SUM", field=field, distinct=distinct)


def avg(field: str, *, distinct: bool = False) -> AggregateSpec:
    """Build an AVG aggregate specification."""
    return AggregateSpec(func="AVG", field=field, distinct=distinct)


def min_(field: str, *, distinct: bool = False) -> AggregateSpec:
    """Build a MIN aggregate specification."""
    return AggregateSpec(func="MIN", field=field, distinct=distinct)


def max_(field: str, *, distinct: bool = False) -> AggregateSpec:
    """Build a MAX aggregate specification."""
    return AggregateSpec(func="MAX", field=field, distinct=distinct)
