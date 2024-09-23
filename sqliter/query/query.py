"""Define the 'QueryBuilder' class for building SQL queries."""

from __future__ import annotations

import sqlite3
import warnings
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Literal,
    Optional,
    Union,
    overload,
)

from typing_extensions import LiteralString, Self

from sqliter.constants import OPERATOR_MAPPING
from sqliter.exceptions import (
    InvalidFilterError,
    InvalidOffsetError,
    InvalidOrderError,
    RecordFetchError,
)

if TYPE_CHECKING:  # pragma: no cover
    from pydantic.fields import FieldInfo

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel

# Define a type alias for the possible value types
FilterValue = Union[
    str, int, float, bool, None, list[Union[str, int, float, bool]]
]


class QueryBuilder:
    """Functions to build and execute queries for a given model."""

    def __init__(
        self,
        db: SqliterDB,
        model_class: type[BaseDBModel],
        fields: Optional[list[str]] = None,
    ) -> None:
        """Initialize the query builder.

        Pass the database, model class, and optional fields.

        Args:
            db: The SqliterDB instance.
            model_class: The model class to query.
            fields: Optional list of field names to select. If None, all fields
                are selected.
        """
        self.db = db
        self.model_class = model_class
        self.table_name = model_class.get_table_name()  # Use model_class method
        self.filters: list[tuple[str, Any, str]] = []
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None
        self._order_by: Optional[str] = None
        self._fields: Optional[list[str]] = fields

        if self._fields:
            self._validate_fields()

    def _validate_fields(self) -> None:
        """Validate that the specified fields exist in the model."""
        if self._fields is None:
            return
        valid_fields = set(self.model_class.model_fields.keys())
        invalid_fields = set(self._fields) - valid_fields
        if invalid_fields:
            err_message = (
                f"Invalid fields specified: {', '.join(invalid_fields)}"
            )
            raise ValueError(err_message)

    def filter(self, **conditions: str | float | None) -> QueryBuilder:
        """Add filter conditions to the query."""
        valid_fields = self.model_class.model_fields

        for field, value in conditions.items():
            field_name, operator = self._parse_field_operator(field)
            self._validate_field(field_name, valid_fields)

            handler = self._get_operator_handler(operator)
            handler(field_name, value, operator)

        return self

    def fields(self, fields: Optional[list[str]] = None) -> QueryBuilder:
        """Select specific fields to return in the query."""
        if fields:
            self._fields = fields
            self._validate_fields()
        return self

    def exclude(self, fields: Optional[list[str]] = None) -> QueryBuilder:
        """Exclude specific fields from the query output."""
        if fields:
            all_fields = set(self.model_class.model_fields.keys())

            # Check for invalid fields before subtraction
            invalid_fields = set(fields) - all_fields
            if invalid_fields:
                err = (
                    "Invalid fields specified for exclusion: "
                    f"{', '.join(invalid_fields)}"
                )
                raise ValueError(err)

            # Subtract the fields specified for exclusion
            self._fields = list(all_fields - set(fields))

            # Explicit check: raise an error if no fields remain
            if not self._fields:
                err = "Exclusion results in no fields being selected."
                raise ValueError(err)

            # Now validate the remaining fields to ensure they are all valid
            self._validate_fields()

        return self

    def only(self, field: str) -> QueryBuilder:
        """Return only the specified single field."""
        all_fields = set(self.model_class.model_fields.keys())

        # Validate that the field exists
        if field not in all_fields:
            err = f"Invalid field specified: {field}"
            raise ValueError(err)

        # Set self._fields to just the single field
        self._fields = [field]
        return self

    def _get_operator_handler(
        self, operator: str
    ) -> Callable[[str, Any, str], None]:
        handlers = {
            "__isnull": self._handle_null,
            "__notnull": self._handle_null,
            "__in": self._handle_in,
            "__not_in": self._handle_in,
            "__startswith": self._handle_like,
            "__endswith": self._handle_like,
            "__contains": self._handle_like,
            "__istartswith": self._handle_like,
            "__iendswith": self._handle_like,
            "__icontains": self._handle_like,
            "__lt": self._handle_comparison,
            "__lte": self._handle_comparison,
            "__gt": self._handle_comparison,
            "__gte": self._handle_comparison,
            "__ne": self._handle_comparison,
        }
        return handlers.get(operator, self._handle_equality)

    def _validate_field(
        self, field_name: str, valid_fields: dict[str, FieldInfo]
    ) -> None:
        if field_name not in valid_fields:
            raise InvalidFilterError(field_name)

    def _handle_equality(
        self, field_name: str, value: FilterValue, operator: str
    ) -> None:
        if value is None:
            self.filters.append((f"{field_name} IS NULL", None, "__isnull"))
        else:
            self.filters.append((field_name, value, operator))

    def _handle_null(
        self, field_name: str, _: FilterValue, operator: str
    ) -> None:
        condition = (
            f"{field_name} IS NOT NULL"
            if operator == "__notnull"
            else f"{field_name} IS NULL"
        )
        self.filters.append((condition, None, operator))

    def _handle_in(
        self, field_name: str, value: FilterValue, operator: str
    ) -> None:
        if not isinstance(value, list):
            err = f"{field_name} requires a list for '{operator}'"
            raise TypeError(err)
        sql_operator = OPERATOR_MAPPING.get(operator, "IN")
        placeholder_list = ", ".join(["?"] * len(value))
        self.filters.append(
            (
                f"{field_name} {sql_operator} ({placeholder_list})",
                value,
                operator,
            )
        )

    def _handle_like(
        self, field_name: str, value: FilterValue, operator: str
    ) -> None:
        if not isinstance(value, str):
            err = f"{field_name} requires a string value for '{operator}'"
            raise TypeError(err)
        formatted_value = self._format_string_for_operator(operator, value)
        if operator in ["__startswith", "__endswith", "__contains"]:
            self.filters.append(
                (
                    f"{field_name} GLOB ?",
                    [formatted_value],
                    operator,
                )
            )
        elif operator in ["__istartswith", "__iendswith", "__icontains"]:
            self.filters.append(
                (
                    f"{field_name} LIKE ?",
                    [formatted_value],
                    operator,
                )
            )

    def _handle_comparison(
        self, field_name: str, value: FilterValue, operator: str
    ) -> None:
        sql_operator = OPERATOR_MAPPING[operator]
        self.filters.append((f"{field_name} {sql_operator} ?", value, operator))

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
            "__startswith": f"{value}*",
            "__endswith": f"*{value}",
            "__contains": f"*{value}*",
            "__istartswith": f"{value.lower()}%",
            "__iendswith": f"%{value.lower()}",
            "__icontains": f"%{value.lower()}%",
        }

        # Return the formatted string or the original value if no match
        return format_map.get(operator, value)

    def limit(self, limit_value: int) -> Self:
        """Limit the number of results returned by the query."""
        self._limit = limit_value
        return self

    def offset(self, offset_value: int) -> Self:
        """Set an offset value for the query."""
        if offset_value < 0:
            raise InvalidOffsetError(offset_value)
        self._offset = offset_value

        if self._limit is None:
            self._limit = -1
        return self

    def order(
        self,
        order_by_field: str,
        direction: Optional[str] = None,
        *,
        reverse: bool = False,
    ) -> Self:
        """Order the query results by the specified field.

        Args:
            order_by_field (str): The field to order by.
            direction (Optional[str]): The ordering direction ('ASC' or 'DESC').
                This is deprecated in favor of 'reverse'.
            reverse (bool): Whether to reverse the order (True for descending,
                False for ascending).

        Raises:
            InvalidOrderError: If the field doesn't exist in the model fields
                or if both 'direction' and 'reverse' are specified.

        Returns:
            QueryBuilder: The current query builder instance with updated
                ordering.
        """
        if direction:
            warnings.warn(
                "'direction' argument is deprecated and will be removed in a "
                "future version. Use 'reverse' instead.",
                DeprecationWarning,
                stacklevel=2,
            )

        if order_by_field not in self.model_class.model_fields:
            err = f"'{order_by_field}' does not exist in the model fields."
            raise InvalidOrderError(err)
        # Raise an exception if both 'direction' and 'reverse' are specified
        if direction and reverse:
            err = (
                "Cannot specify both 'direction' and 'reverse' as it "
                "is ambiguous."
            )
            raise InvalidOrderError(err)

        # Determine the sorting direction
        if reverse:
            sort_order = "DESC"
        elif direction:
            sort_order = direction.upper()
            if sort_order not in {"ASC", "DESC"}:
                err = f"'{direction}' is not a valid sorting direction."
                raise InvalidOrderError(err)
        else:
            sort_order = "ASC"

        self._order_by = f'"{order_by_field}" {sort_order}'
        return self

    def _execute_query(
        self,
        *,
        fetch_one: bool = False,
        count_only: bool = False,
    ) -> list[tuple[Any, ...]] | Optional[tuple[Any, ...]]:
        """Helper function to execute the query with filters."""
        if count_only:
            fields = "COUNT(*)"
        elif self._fields:
            fields = ", ".join(f'"{field}"' for field in self._fields)
        else:
            fields = ", ".join(
                f'"{field}"' for field in self.model_class.model_fields
            )

        sql = f'SELECT {fields} FROM "{self.table_name}"'  # noqa: S608 # nosec

        # Build the WHERE clause with special handling for None (NULL in SQL)
        values, where_clause = self._parse_filter()

        if self.filters:
            sql += f" WHERE {where_clause}"

        if self._order_by:
            sql += f" ORDER BY {self._order_by}"

        if self._limit is not None:
            sql += " LIMIT ?"
            values.append(self._limit)

        if self._offset is not None:
            sql += " OFFSET ?"
            values.append(self._offset)

        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, values)
                return cursor.fetchall() if not fetch_one else cursor.fetchone()
        except sqlite3.Error as exc:
            raise RecordFetchError(self.table_name) from exc

    def _parse_filter(self) -> tuple[list[Any], LiteralString]:
        """Actually parse the filters."""
        where_clauses = []
        values = []
        for field, value, operator in self.filters:
            if operator == "__eq":
                where_clauses.append(f"{field} = ?")
                values.append(value)
            else:
                where_clauses.append(field)
                if operator not in ["__isnull", "__notnull"]:
                    if isinstance(value, list):
                        values.extend(value)
                    else:
                        values.append(value)

        where_clause = " AND ".join(where_clauses)
        return values, where_clause

    def _convert_row_to_model(self, row: tuple[Any, ...]) -> BaseDBModel:
        """Convert a result row tuple into a Pydantic model."""
        if self._fields:
            return self.model_class.model_validate_partial(
                {field: row[idx] for idx, field in enumerate(self._fields)}
            )
        return self.model_class(
            **{
                field: row[idx]
                for idx, field in enumerate(self.model_class.model_fields)
            }
        )

    @overload
    def _fetch_result(
        self, *, fetch_one: Literal[True]
    ) -> Optional[BaseDBModel]: ...

    @overload
    def _fetch_result(
        self, *, fetch_one: Literal[False]
    ) -> list[BaseDBModel]: ...

    def _fetch_result(
        self, *, fetch_one: bool = False
    ) -> Union[list[BaseDBModel], Optional[BaseDBModel]]:
        """Fetch one or all results and convert them to Pydantic models."""
        result = self._execute_query(fetch_one=fetch_one)

        if not result:
            if fetch_one:
                return None
            return []

        if fetch_one:
            # Ensure we pass a tuple, not a list, to _convert_row_to_model
            if isinstance(result, list):
                result = result[
                    0
                ]  # Get the first (and only) result if it's wrapped in a list.
            return self._convert_row_to_model(result)

        return [self._convert_row_to_model(row) for row in result]

    def fetch_all(self) -> list[BaseDBModel]:
        """Fetch all results matching the filters."""
        return self._fetch_result(fetch_one=False)

    def fetch_one(self) -> Optional[BaseDBModel]:
        """Fetch exactly one result."""
        return self._fetch_result(fetch_one=True)

    def fetch_first(self) -> Optional[BaseDBModel]:
        """Fetch the first result of the query."""
        self._limit = 1
        return self._fetch_result(fetch_one=True)

    def fetch_last(self) -> Optional[BaseDBModel]:
        """Fetch the last result of the query (based on the insertion order)."""
        self._limit = 1
        self._order_by = "rowid DESC"
        return self._fetch_result(fetch_one=True)

    def count(self) -> int:
        """Return the count of records matching the filters."""
        result = self._execute_query(count_only=True)

        return int(result[0][0]) if result else 0

    def exists(self) -> bool:
        """Return True if any record matches the filters."""
        return self.count() > 0
