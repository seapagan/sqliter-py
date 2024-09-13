"""Define the 'QueryBuilder' class for building SQL queries."""

from __future__ import annotations

import select
import sqlite3
from typing import TYPE_CHECKING, Any, Optional

from typing_extensions import Self

from sqliter.constants import OPERATOR_MAPPING
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
        self.filters: list[tuple[str, Any, str]] = []
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None
        self._order_by: Optional[str] = None

    def filter(self, **conditions: str | float | None) -> Self:
        """Add filter conditions to the query."""
        valid_fields = self.model_class.model_fields

        for field, value in conditions.items():
            # Split the field into the name and the operator
            field_name, operator = self._parse_field_operator(field)

            # Validate the field
            if field_name not in valid_fields:
                raise InvalidFilterError(field_name)

            # Use the mapped SQL operator, or default to '=' for equality
            sql_operator = OPERATOR_MAPPING.get(operator, "=")

            if value is None:
                # Handle None values as IS NULL
                self.filters.append((f"{field_name} IS NULL", None, "__isnull"))
            elif operator in ["__isnull", "__notnull"]:
                # For IS NULL and IS NOT NULL, no value is needed
                self.filters.append(
                    (f"{field_name} {sql_operator}", None, operator)
                )
            elif operator in ["__in", "__not_in"]:
                # Ensure value is a list for IN/NOT IN clauses
                if not isinstance(value, list):
                    err = f"{field_name} requires a list for '{operator}'"
                    raise ValueError(err)
                # and pass it as multiple values
                placeholder_list = ", ".join(["?"] * len(value))
                self.filters.append(
                    (
                        f"{field_name} {sql_operator} ({placeholder_list})",
                        value,
                        operator,
                    )
                )
            elif operator in ["__startswith", "__endswith", "__contains"]:
                # Ensure the value is a string before formatting it in this case
                if isinstance(value, str):
                    formatted_value = self._format_string_for_operator(
                        operator, value
                    )
                    self.filters.append(
                        (
                            f"{field_name} {sql_operator}",
                            [formatted_value],
                            operator,
                        )
                    )
                else:
                    err = (
                        f"{field_name} requires a string value for '{operator}'"
                    )
                    raise ValueError(err)
            elif operator in ["__lt", "__lte", "__gt", "__gte", "__ne"]:
                # Handle comparison operators specifically
                sql_operator = OPERATOR_MAPPING[operator]
                self.filters.append(
                    (f"{field_name} {sql_operator} ?", value, operator)
                )
            else:
                # Default behavior for equality checks
                self.filters.append((field_name, value, operator))

        return self

    # Helper method for parsing field and operator
    def _parse_field_operator(self, field: str) -> tuple[str, str]:
        for operator in OPERATOR_MAPPING:
            if field.endswith(operator):
                return field[: -len(operator)], operator
        return field, "__eq"  # Default to equality if no operator is found

    # Helper method for formatting string operators (like startswith)
    def _format_string_for_operator(self, operator: str, value: str) -> str:
        # Mapping operators to their corresponding string format
        format_map = {
            "__startswith": f"{value}%",
            "__endswith": f"%{value}",
            "__contains": f"%{value}%",
        }

        # Return the formatted string or the original value if no match
        return format_map.get(operator, value)

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
        count_only: bool = False,
    ) -> list[tuple[Any, ...]] | Optional[tuple[Any, ...]]:
        """Helper function to execute the query with filters."""
        fields = ", ".join(self.model_class.model_fields)

        # Build the WHERE clause with special handling for None (NULL in SQL)
        where_clauses = []
        values = []
        for field, value, operator in self.filters:
            if operator == "__isnull":
                where_clauses.append(f"{field}")
            elif operator == "__notnull":
                where_clauses.append(f"{field} IS NOT NULL")
            elif operator in ["__in", "__not_in"]:
                where_clauses.append(field)
                values.extend(value)
            elif operator in ["__startswith", "__endswith", "__contains"]:
                where_clauses.append(field)
                values.extend(value)
            elif operator in ["__lt", "__lte", "__gt", "__gte", "__ne"]:
                where_clauses.append(field)
                values.append(value)
            else:
                where_clauses.append(f"{field} = ?")
                values.append(value)

        where_clause = " AND ".join(where_clauses)

        select_fields = fields if not count_only else "COUNT(*)"

        sql = f"SELECT {select_fields} FROM {self.table_name}"  # noqa: S608

        if self.filters:
            sql += f" WHERE {where_clause}"

        if self._order_by:
            sql += f" ORDER BY {self._order_by}"

        if self._limit is not None:
            sql += f" LIMIT {self._limit}"

        if self._offset is not None:
            sql += f" OFFSET {self._offset}"

        print(f"Executing SQL: {sql} with values: {values}")  # Debug print

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
        result = self._execute_query(count_only=True)

        return int(result[0][0]) if result else 0

    def exists(self) -> bool:
        """Return True if any record matches the filters."""
        return self.count() > 0
