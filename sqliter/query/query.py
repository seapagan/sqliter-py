"""Define the 'QueryBuilder' class for building SQL queries."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING, Any, Optional

from typing_extensions import Self

from sqliter.exceptions import (
    InvalidFilterError,
    InvalidOffsetError,
    RecordFetchError,
)

if TYPE_CHECKING:  # pragma: no cover
    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel


class QueryBuilder:
    """Functions to build and execute queries for a given model."""

    def __init__(self, db: SqliterDB, model_class: type[BaseDBModel]) -> None:
        """Initialize the query builder with the database, model class, etc."""
        self.db = db
        self.model_class = model_class
        self.table_name = model_class.get_table_name()  # Use model_class method
        self.filters: list[tuple[str, Any]] = []
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None
        self._order_by: Optional[str] = None

    def filter(self, **conditions: str | float | None) -> Self:
        """Add filter conditions to the query."""
        valid_fields = self.model_class.model_fields

        for field, value in conditions.items():
            if field not in valid_fields:
                raise InvalidFilterError(field)
            self.filters.append((field, value))

        return self

    def limit(self, limit_value: int) -> Self:
        """Limit the number of results returned by the query."""
        self._limit = limit_value
        return self

    def offset(self, offset_value: int) -> Self:
        """Set an offset value for the query."""
        if offset_value <= 0:
            raise InvalidOffsetError(offset_value)
        self._offset = offset_value

        if self._limit is None:
            self._limit = -1
        return self

    def order(self, order_by_field: str) -> Self:
        """Order the results by a specific field and optionally direction."""
        self._order_by = order_by_field
        return self

    def _execute_query(
        self,
        *,
        fetch_one: bool = False,
    ) -> list[tuple[Any, ...]] | Optional[tuple[Any, ...]]:
        """Helper function to execute the query with filters."""
        fields = ", ".join(self.model_class.model_fields)

        # Build the WHERE clause with special handling for None (NULL in SQL)
        where_clause = " AND ".join(
            [
                f"{field} IS NULL" if value is None else f"{field} = ?"
                for field, value in self.filters
            ]
        )

        sql = f"SELECT {fields} FROM {self.table_name}"  # noqa: S608

        if self.filters:
            sql += f" WHERE {where_clause}"

        if self._order_by:
            sql += f" ORDER BY {self._order_by}"

        if self._limit is not None:
            sql += f" LIMIT {self._limit}"

        if self._offset is not None:
            sql += f" OFFSET {self._offset}"

        # Only include non-None values in the values list
        values = [value for _, value in self.filters if value is not None]

        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, values)
                return cursor.fetchall() if not fetch_one else cursor.fetchone()
        except sqlite3.Error as exc:
            raise RecordFetchError(self.table_name) from exc

    def fetch_all(self) -> list[BaseDBModel]:
        """Fetch all results matching the filters."""
        results = self._execute_query()

        if not results:
            return []

        return [
            self.model_class(
                **{
                    field: row[idx]
                    for idx, field in enumerate(self.model_class.model_fields)
                }
            )
            for row in results
        ]

    def fetch_one(self) -> BaseDBModel | None:
        """Fetch exactly one result."""
        result = self._execute_query(fetch_one=True)
        if not result:
            return None
        return self.model_class(
            **{
                field: result[idx]
                for idx, field in enumerate(self.model_class.model_fields)
            }
        )

    def fetch_first(self) -> BaseDBModel | None:
        """Fetch the first result of the query."""
        self._limit = 1
        result = self._execute_query()
        if not result:
            return None
        return self.model_class(
            **{
                field: result[0][idx]
                for idx, field in enumerate(self.model_class.model_fields)
            }
        )

    def fetch_last(self) -> BaseDBModel | None:
        """Fetch the last result of the query (based on the insertion order)."""
        self._limit = 1
        self._order_by = "rowid DESC"
        result = self._execute_query()
        if not result:
            return None
        return self.model_class(
            **{
                field: result[0][idx]
                for idx, field in enumerate(self.model_class.model_fields)
            }
        )

    def count(self) -> int:
        """Return the count of records matching the filters."""
        where_clause = " AND ".join(
            [f"{field} = ?" for field, _ in self.filters]
        )
        sql = f"SELECT COUNT(*) FROM {self.table_name}"  # noqa: S608

        if self.filters:
            sql += f" WHERE {where_clause}"

        values = [value for _, value in self.filters]

        with self.db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, values)
            result = cursor.fetchone()

        return int(result[0]) if result else 0

    def exists(self) -> bool:
        """Return True if any record matches the filters."""
        return self.count() > 0
