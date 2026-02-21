"""This module provides the query building functionality for SQLiter.

It exports the QueryBuilder class, which is used to construct and
execute database queries in SQLiter.
"""

from .aggregates import AggregateSpec, avg, count, max_, min_, sum_
from .query import QueryBuilder

__all__ = [
    "AggregateSpec",
    "QueryBuilder",
    "avg",
    "count",
    "max_",
    "min_",
    "sum_",
]
