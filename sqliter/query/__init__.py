"""This module provides the query building functionality for SQLiter.

It exports the QueryBuilder class, which is used to construct and
execute database queries in SQLiter.
"""

from .aggregates import AggregateSpec, func
from .query import QueryBuilder

__all__ = [
    "AggregateSpec",
    "QueryBuilder",
    "func",
]
