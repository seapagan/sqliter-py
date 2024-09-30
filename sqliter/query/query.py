"""Implements the query building and execution logic for SQLiter.

This module defines the QueryBuilder class, which provides a fluent
interface for constructing SQL queries. It supports operations such
as filtering, ordering, limiting, and various data retrieval methods,
allowing for flexible and expressive database queries without writing
raw SQL.
"""

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
    """Builds and executes database queries for a specific model.

    This class provides methods to construct SQL queries, apply filters,
    set ordering, and execute the queries against the database.

    Attributes:
        db (SqliterDB): The database connection object.
        model_class (type[BaseDBModel]): The Pydantic model class.
        table_name (str): The name of the database table.
        filters (list): List of applied filter conditions.
        _limit (Optional[int]): The LIMIT clause value, if any.
        _offset (Optional[int]): The OFFSET clause value, if any.
        _order_by (Optional[str]): The ORDER BY clause, if any.
        _fields (Optional[list[str]]): List of fields to select, if specified.
    """

    def __init__(
        self,
        db: SqliterDB,
        model_class: type[BaseDBModel],
        fields: Optional[list[str]] = None,
    ) -> None:
        """Initialize a new QueryBuilder instance.

        Args:
            db: The database connection object.
            model_class: The Pydantic model class for the table.
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
        """Validate that the specified fields exist in the model.

        Raises:
            ValueError: If any specified field is not in the model.
        """
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
        """Apply filter conditions to the query.

        This method allows adding one or more filter conditions to the query.
        Each condition is specified as a keyword argument, where the key is
        the field name and the value is the condition to apply.

        Args:
            **conditions: Arbitrary keyword arguments representing filter
                conditions. The key is the field name, and the value is the
                condition to apply. Supported operators include equality,
                comparison, and special operators like __in, __isnull, etc.

        Returns:
            QueryBuilder: The current QueryBuilder instance for method
            chaining.

        Examples:
            >>> query.filter(name="John", age__gt=30)
            >>> query.filter(status__in=["active", "pending"])
        """
        valid_fields = self.model_class.model_fields

        for field, value in conditions.items():
            field_name, operator = self._parse_field_operator(field)
            self._validate_field(field_name, valid_fields)

            if operator in ["__isnull", "__notnull"]:
                self._handle_null(field_name, value, operator)
            else:
                handler = self._get_operator_handler(operator)
                handler(field_name, value, operator)

        return self

    def fields(self, fields: Optional[list[str]] = None) -> QueryBuilder:
        """Specify which fields to select in the query.

        Args:
            fields: List of field names to select. If None, all fields are
                selected.

        Returns:
            The QueryBuilder instance for method chaining.
        """
        if fields:
            if "pk" not in fields:
                fields.append("pk")
            self._fields = fields
            self._validate_fields()
        return self

    def exclude(self, fields: Optional[list[str]] = None) -> QueryBuilder:
        """Specify which fields to exclude from the query results.

        Args:
            fields: List of field names to exclude. If None, no fields are
                excluded.

        Returns:
            The QueryBuilder instance for method chaining.

        Raises:
            ValueError: If exclusion results in no fields being selected or if
                invalid fields are specified.
        """
        if fields:
            if "pk" in fields:
                err = "The primary key 'pk' cannot be excluded."
                raise ValueError(err)
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
            if self._fields == ["pk"]:
                err = "Exclusion results in no fields being selected."
                raise ValueError(err)

            # Now validate the remaining fields to ensure they are all valid
            self._validate_fields()

        return self

    def only(self, field: str) -> QueryBuilder:
        """Specify a single field to select in the query.

        Args:
            field: The name of the field to select.

        Returns:
            The QueryBuilder instance for method chaining.

        Raises:
            ValueError: If the specified field is invalid.
        """
        all_fields = set(self.model_class.model_fields.keys())

        # Validate that the field exists
        if field not in all_fields:
            err = f"Invalid field specified: {field}"
            raise ValueError(err)

        # Set self._fields to just the single field
        self._fields = [field, "pk"]
        return self

    def _get_operator_handler(
        self, operator: str
    ) -> Callable[[str, Any, str], None]:
        """Get the appropriate handler function for the given operator.

        Args:
            operator: The filter operator string.

        Returns:
            A callable that handles the specific operator type.
        """
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
        """Validate that a field exists in the model.

        Args:
            field_name: The name of the field to validate.
            valid_fields: Dictionary of valid fields from the model.

        Raises:
            InvalidFilterError: If the field is not in the model.
        """
        if field_name not in valid_fields:
            raise InvalidFilterError(field_name)

    def _handle_equality(
        self, field_name: str, value: FilterValue, operator: str
    ) -> None:
        """Handle equality filter conditions.

        Args:
            field_name: The name of the field to filter on.
            value: The value to compare against.
            operator: The operator string (usually '__eq').

        This method adds an equality condition to the filters list, handling
        NULL values separately.
        """
        if value is None:
            self.filters.append((f"{field_name} IS NULL", None, "__isnull"))
        else:
            self.filters.append((field_name, value, operator))

    def _handle_null(
        self, field_name: str, value: Union[str, float, None], operator: str
    ) -> None:
        """Handle IS NULL and IS NOT NULL filter conditions.

        Args:
            field_name: The name of the field to filter on. _: Placeholder for
                unused value parameter.
            operator: The operator string ('__isnull' or '__notnull').
            value: The value to check for.

        This method adds an IS NULL or IS NOT NULL condition to the filters
        list.
        """
        is_null = operator == "__isnull"
        check_null = bool(value) if is_null else not bool(value)
        condition = f"{field_name} IS {'NOT ' if not check_null else ''}NULL"
        self.filters.append((condition, None, operator))

    def _handle_in(
        self, field_name: str, value: FilterValue, operator: str
    ) -> None:
        """Handle IN and NOT IN filter conditions.

        Args:
            field_name: The name of the field to filter on.
            value: A list of values to check against.
            operator: The operator string ('__in' or '__not_in').

        Raises:
            TypeError: If the value is not a list.

        This method adds an IN or NOT IN condition to the filters list.
        """
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
        """Handle LIKE and GLOB filter conditions.

        Args:
            field_name: The name of the field to filter on.
            value: The pattern to match against.
            operator: The operator string (e.g., '__startswith', '__contains').

        Raises:
            TypeError: If the value is not a string.

        This method adds a LIKE or GLOB condition to the filters list, depending
        on whether the operation is case-sensitive or not.
        """
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
        """Handle comparison filter conditions.

        Args:
            field_name: The name of the field to filter on.
            value: The value to compare against.
            operator: The comparison operator string (e.g., '__lt', '__gte').

        This method adds a comparison condition to the filters list.
        """
        sql_operator = OPERATOR_MAPPING[operator]
        self.filters.append((f"{field_name} {sql_operator} ?", value, operator))

    # Helper method for parsing field and operator
    def _parse_field_operator(self, field: str) -> tuple[str, str]:
        """Parse a field string to separate the field name and operator.

        Args:
            field: The field string, potentially including an operator.

        Returns:
            A tuple containing the field name and the operator (or '__eq' if
            no operator was specified).
        """
        for operator in OPERATOR_MAPPING:
            if field.endswith(operator):
                return field[: -len(operator)], operator
        return field, "__eq"  # Default to equality if no operator is found

    # Helper method for formatting string operators (like startswith)
    def _format_string_for_operator(self, operator: str, value: str) -> str:
        """Format a string value based on the specified operator.

        Args:
            operator: The operator string (e.g., '__startswith', '__contains').
            value: The original string value.

        Returns:
            The formatted string value suitable for the given operator.
        """
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
        """Limit the number of results returned by the query.

        Args:
        limit_value: The maximum number of records to return.

        Returns:
            The QueryBuilder instance for method chaining.
        """
        self._limit = limit_value
        return self

    def offset(self, offset_value: int) -> Self:
        """Set an offset value for the query.

        Args:
            offset_value: The number of records to skip.

        Returns:
            The QueryBuilder instance for method chaining.

        Raises:
            InvalidOffsetError: If the offset value is negative.
        """
        if offset_value < 0:
            raise InvalidOffsetError(offset_value)
        self._offset = offset_value

        if self._limit is None:
            self._limit = -1
        return self

    def order(
        self,
        order_by_field: Optional[str] = None,
        direction: Optional[str] = None,
        *,
        reverse: bool = False,
    ) -> Self:
        """Order the query results by the specified field.

        Args:
            order_by_field: The field to order by [optional].
            direction: Deprecated. Use 'reverse' instead.
            reverse: If True, sort in descending order.

        Returns:
            The QueryBuilder instance for method chaining.

        Raises:
            InvalidOrderError: If the field doesn't exist or if both 'direction'
                and 'reverse' are specified.

        Warns:
            DeprecationWarning: If 'direction' is used instead of 'reverse'.
        """
        if direction:
            warnings.warn(
                "'direction' argument is deprecated and will be removed in a "
                "future version. Use 'reverse' instead.",
                DeprecationWarning,
                stacklevel=2,
            )

        if order_by_field is None:
            order_by_field = self.model_class.get_primary_key()

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
        """Execute the constructed SQL query.

        Args:
            fetch_one: If True, fetch only one result.
            count_only: If True, return only the count of results.

        Returns:
            A list of tuples (all results), a single tuple (one result),
            or None if no results are found.

        Raises:
            RecordFetchError: If there's an error executing the query.
        """
        if count_only:
            fields = "COUNT(*)"
        elif self._fields:
            if "pk" not in self._fields:
                self._fields.append("pk")
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

        # Print the raw SQL and values if debug is enabled
        # Log the SQL if debug is enabled
        if self.db.debug:
            self.db._log_sql(sql, values)  # noqa: SLF001

        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, values)
                return cursor.fetchall() if not fetch_one else cursor.fetchone()
        except sqlite3.Error as exc:
            raise RecordFetchError(self.table_name) from exc

    def _parse_filter(self) -> tuple[list[Any], LiteralString]:
        """Parse the filter conditions into SQL clauses and values.

        Returns:
            A tuple containing:
            - A list of values to be used in the SQL query.
            - A string representing the WHERE clause of the SQL query.
        """
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
        """Convert a database row to a model instance.

        Args:
            row: A tuple representing a database row.

        Returns:
            An instance of the model class populated with the row data.
        """
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
        """Fetch and convert query results to model instances.

        Args:
            fetch_one: If True, fetch only one result.

        Returns:
            A list of model instances, a single model instance, or None if no
            results are found.
        """
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
        """Fetch all results of the query.

        Returns:
            A list of model instances representing all query results.
        """
        return self._fetch_result(fetch_one=False)

    def fetch_one(self) -> Optional[BaseDBModel]:
        """Fetch a single result of the query.

        Returns:
            A single model instance or None if no result is found.
        """
        return self._fetch_result(fetch_one=True)

    def fetch_first(self) -> Optional[BaseDBModel]:
        """Fetch the first result of the query.

        Returns:
            The first model instance or None if no result is found.
        """
        self._limit = 1
        return self._fetch_result(fetch_one=True)

    def fetch_last(self) -> Optional[BaseDBModel]:
        """Fetch the last result of the query.

        Returns:
            The last model instance or None if no result is found.
        """
        self._limit = 1
        self._order_by = "rowid DESC"
        return self._fetch_result(fetch_one=True)

    def count(self) -> int:
        """Count the number of results for the current query.

        Returns:
            The number of results that match the current query conditions.
        """
        result = self._execute_query(count_only=True)

        return int(result[0][0]) if result else 0

    def exists(self) -> bool:
        """Check if any results exist for the current query.

        Returns:
            True if at least one result exists, False otherwise.
        """
        return self.count() > 0
