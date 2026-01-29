"""Implements the query building and execution logic for SQLiter.

This module defines the QueryBuilder class, which provides a fluent
interface for constructing SQL queries. It supports operations such
as filtering, ordering, limiting, and various data retrieval methods,
allowing for flexible and expressive database queries without writing
raw SQL.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import warnings
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
    Literal,
    Optional,
    TypeVar,
    Union,
    cast,
    overload,
)

from typing_extensions import Self

from sqliter.constants import OPERATOR_MAPPING
from sqliter.exceptions import (
    InvalidFilterError,
    InvalidOffsetError,
    InvalidOrderError,
    InvalidRelationshipError,
    RecordDeletionError,
    RecordFetchError,
)

if TYPE_CHECKING:  # pragma: no cover
    from pydantic.fields import FieldInfo

    from sqliter import SqliterDB
    from sqliter.model import BaseDBModel, SerializableField

# TypeVar for generic QueryBuilder
T = TypeVar("T", bound="BaseDBModel")

# Define a type alias for the possible value types
FilterValue = Union[
    str, int, float, bool, None, list[Union[str, int, float, bool]]
]


@dataclass
class JoinInfo:
    """Metadata for a JOIN clause.

    Attributes:
        alias: Table alias for the JOIN (e.g., "t1", "t2").
        table_name: Actual table name in the database.
        model_class: The model class for the joined table.
        fk_field: FK field name on the parent model.
        parent_alias: Alias of the parent table in the JOIN chain.
        fk_column: The FK column name (e.g., "author_id").
        join_type: Type of JOIN ("LEFT" or "INNER").
        path: Full relationship path (e.g., "post__author").
        is_nullable: Whether the FK is nullable.
    """

    alias: str
    table_name: str
    model_class: type[BaseDBModel]
    fk_field: str
    parent_alias: str
    fk_column: str
    join_type: str
    path: str
    is_nullable: bool


class QueryBuilder(Generic[T]):
    """Builds and executes database queries for a specific model.

    This class provides methods to construct SQL queries, apply filters,
    set ordering, and execute the queries against the database.

    Attributes:
        db (SqliterDB): The database connection object.
        model_class (type[T]): The Pydantic model class.
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
        model_class: type[T],
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
        self.model_class: type[T] = model_class
        self.table_name = model_class.get_table_name()  # Use model_class method
        self.filters: list[tuple[str, Any, str]] = []
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None
        self._order_by: Optional[str] = None
        self._fields: Optional[list[str]] = fields
        self._bypass_cache: bool = False
        self._query_cache_ttl: Optional[int] = None
        # Eager loading support
        self._select_related_paths: list[str] = []
        self._join_info: list[JoinInfo] = []

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

    def filter(self, **conditions: FilterValue) -> Self:
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

            # Check for relationship traversal (e.g., author__name)
            if "__" in field_name and operator not in {
                "__isnull",
                "__notnull",
            }:
                # Handle relationship filter traversal
                self._handle_relationship_filter(field_name, value, operator)
            else:
                # Normal field filter
                self._validate_field(field_name, valid_fields)
                if operator in ["__isnull", "__notnull"]:
                    self._handle_null(field_name, value, operator)
                else:
                    handler = self._get_operator_handler(operator)
                    handler(field_name, value, operator)

        return self

    def _handle_relationship_filter(
        self, field_name: str, value: FilterValue, operator: str
    ) -> None:
        """Handle filter conditions across relationships.

        Args:
            field_name: The field name with relationship path
                (e.g., "author__name").
            value: The filter value.
            operator: The filter operator.

        Raises:
            InvalidRelationshipError: If the relationship path is invalid.
        """
        # Split into relationship path and target field
        parts = field_name.split("__")
        relationship_path = "__".join(parts[:-1])
        target_field = parts[-1]

        # Build JOIN info for the relationship path
        # This validates the path and populates _join_info
        self._validate_and_build_join_info(relationship_path)

        # Find the join info for this relationship path
        join_info = next(
            j for j in self._join_info if j.path == relationship_path
        )

        # Validate target field exists on the related model
        if target_field not in join_info.model_class.model_fields:
            error_msg = (
                f"{field_name} - field '{target_field}' not found in "
                f"{join_info.model_class.__name__}"
            )
            raise InvalidFilterError(error_msg)

        # Apply filter with table alias
        qualified_field = f'{join_info.alias}."{target_field}"'

        # Use the appropriate handler
        # Note: __isnull/__notnull operators don't reach here due to
        # filter() method check at line 176-179
        handler = self._get_operator_handler(operator)
        handler(qualified_field, value, operator)

    def fields(self, fields: Optional[list[str]] = None) -> Self:
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

    def exclude(self, fields: Optional[list[str]] = None) -> Self:
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

    def only(self, field: str) -> Self:
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

    def select_related(self, *paths: str) -> Self:
        """Specify foreign key relationships to eager load via JOIN.

        This method reduces the N+1 query problem by fetching related objects
        in a single query using JOINs instead of lazy loading.

        Args:
            *paths: One or more relationship paths to eager load.
                Single level: "author"
                Nested levels: "post__author"
                Multiple: "author", "publisher"

        Returns:
            The QueryBuilder instance for method chaining.

        Raises:
            InvalidRelationshipError: If a path contains invalid fields.

        Examples:
            >>> # Single level eager load
            >>> db.select(Book).select_related("author").fetch_all()
            >>> # Nested eager load
            >>> db.select(Comment).select_related(
            ...     "post__author"
            ... ).fetch_all()
            >>> # Multiple paths
            >>> db.select(Book).select_related(
            ...     "author", "publisher"
            ... ).fetch_all()
        """
        # Store the paths
        self._select_related_paths.extend(paths)

        # Validate and build join info for each path
        for path in paths:
            self._validate_and_build_join_info(path)

        return self

    def _validate_and_build_join_info(self, path: str) -> None:
        """Validate a relationship path and build JoinInfo entries.

        Args:
            path: Relationship path (e.g., "author" or "post__author").

        Raises:
            InvalidRelationshipError: If path contains invalid fields.
        """
        # Split path into segments
        segments = path.split("__")

        # Start with current model as parent
        current_model: type[BaseDBModel] = self.model_class
        parent_alias = "t0"  # Main table alias

        # Get next available alias number based on existing joins
        next_alias_num = len(self._join_info) + 1

        # Track progressive path for nested relationships
        progressive_path = []

        for segment in segments:
            # Check if segment is a valid FK field on current model
            fk_descriptors = getattr(current_model, "fk_descriptors", {})

            if segment not in fk_descriptors:
                # Not an ORM-style FK - select_related() only supports ORM FKs
                model_name = current_model.__name__
                raise InvalidRelationshipError(path, segment, model_name)

            # ORM FK descriptor
            fk_descriptor = fk_descriptors[segment]
            to_model = fk_descriptor.to_model
            fk_column = f"{segment}_id"
            is_nullable = fk_descriptor.fk_info.null

            # Create alias for this join using global counter
            alias = f"t{next_alias_num}"
            next_alias_num += 1

            # Build progressive path for this level
            progressive_path.append(segment)
            current_path = "__".join(progressive_path)

            # Check if this path segment already exists to avoid duplicate JOINs
            if any(j.path == current_path for j in self._join_info):
                # Path exists - find existing JoinInfo to continue chain
                existing_join = next(
                    j for j in self._join_info if j.path == current_path
                )
                current_model = existing_join.model_class
                parent_alias = existing_join.alias
                continue

            # Build JoinInfo
            join_info = JoinInfo(
                alias=alias,
                table_name=to_model.get_table_name(),
                model_class=to_model,
                fk_field=segment,
                parent_alias=parent_alias,
                fk_column=fk_column,
                join_type="LEFT" if is_nullable else "INNER",
                path=current_path,
                is_nullable=is_nullable,
            )
            self._join_info.append(join_info)

            # Move to next level
            current_model = to_model
            parent_alias = alias

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
            "__like": self._handle_like,
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

        Raises:
            TypeError: If the value is a list (lists only valid with __in).

        This method adds an equality condition to the filters list, handling
        NULL values separately.
        """
        if isinstance(value, list):
            msg = f"{field_name} requires scalar for '{operator}', not list"
            raise TypeError(msg)
        if value is None:
            self.filters.append((f"{field_name} IS NULL", None, "__isnull"))
        else:
            self.filters.append((field_name, value, operator))

    def _handle_null(
        self, field_name: str, value: FilterValue, operator: str
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
            operator: The operator string (e.g., '__like', '__startswith').

        Raises:
            TypeError: If the value is not a string.

        This method adds a LIKE or GLOB condition to the filters list, depending
        on whether the operation is case-sensitive or not.
        """
        if not isinstance(value, str):
            err = f"{field_name} requires a string value for '{operator}'"
            raise TypeError(err)
        if operator == "__like":
            # Raw LIKE - user provides the full pattern with % wildcards
            self.filters.append(
                (
                    f"{field_name} LIKE ?",
                    [value],
                    operator,
                )
            )
        elif operator in [
            "__startswith",
            "__endswith",
            "__contains",
            "__istartswith",
            "__iendswith",
            "__icontains",
        ]:
            formatted_value = self._format_string_for_operator(operator, value)
            sql_operator = OPERATOR_MAPPING[operator]
            field_expr = (
                f"{field_name} COLLATE NOCASE"
                if operator in {"__istartswith", "__iendswith", "__icontains"}
                else field_name
            )
            self.filters.append(
                (
                    f"{field_expr} {sql_operator} ?",
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

        Raises:
            TypeError: If the value is a list (lists only valid with __in).

        This method adds a comparison condition to the filters list.
        """
        if isinstance(value, list):
            msg = f"{field_name} requires scalar for '{operator}', not list"
            raise TypeError(msg)
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

    def _build_join_sql(
        self,
    ) -> tuple[
        str,
        str,
        list[tuple[str, str, type[BaseDBModel]]],
    ]:
        """Build JOIN clauses and aliased column SELECT statements.

        Returns:
            A tuple containing:
            - join_clause: SQL JOIN clauses
                (e.g., "LEFT JOIN authors AS t1 ON ...")
            - select_clause: SELECT clause with aliased columns
            - column_names: List of (alias, field_name, model_class) tuples
        """
        # Note: Only called when _join_info is not empty (line 840)
        select_parts: list[str] = []
        column_names: list[tuple[str, str, type[BaseDBModel]]] = []
        join_parts: list[str] = []

        # Main table columns (t0)
        for field in self.model_class.model_fields:
            alias = f"t0__{field}"
            select_parts.append(f't0."{field}" AS "{alias}"')
            column_names.append(("t0", field, self.model_class))

        # Add JOINed table columns
        for join in self._join_info:
            # Build JOIN clause
            join_clause = (
                f"{join.join_type} JOIN "
                f'"{join.table_name}" AS {join.alias} '
                f'ON {join.parent_alias}."{join.fk_column}" = {join.alias}."pk"'
            )
            join_parts.append(join_clause)

            # Add columns from joined table
            for field in join.model_class.model_fields:
                alias = f"{join.alias}__{field}"
                select_parts.append(f'{join.alias}."{field}" AS "{alias}"')
                column_names.append((join.alias, field, join.model_class))

        select_clause = ", ".join(select_parts)
        join_clause = " ".join(join_parts)

        return join_clause, select_clause, column_names

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

    def _execute_query(  # noqa: C901, PLR0912, PLR0915
        self,
        *,
        fetch_one: bool = False,
        count_only: bool = False,
    ) -> tuple[
        list[tuple[Any, ...]] | tuple[Any, ...],
        list[tuple[str, str, type[BaseDBModel]]],
    ]:
        """Execute the constructed SQL query.

        Args:
            fetch_one: If True, fetch only one result.
            count_only: If True, return only the count of results.

        Returns:
            A tuple containing:
            - Query results (list of tuples or single tuple)
            - Column metadata (list of (alias, field_name, model_class) tuples)
              Empty list for non-JOIN queries (backward compatible).

        Raises:
            RecordFetchError: If there's an error executing the query.
        """
        # Check if we need JOINs for eager loading or relationship filters
        # Need JOIN if: we have join_info AND (not count/fields OR filters
        # use joins)
        needs_join_for_filters = False
        if self._join_info and (count_only or self._fields):
            # Parse filter to check if it references joined tables
            values, where_clause = self._parse_filter()
            # Check for table aliases like t1., t2., etc.
            if re.search(r"\bt\d+\.", where_clause):
                needs_join_for_filters = True

        if self._join_info and (
            not (count_only or self._fields) or needs_join_for_filters
        ):
            # Use JOIN-based query
            join_clause, select_clause, column_names = self._build_join_sql()

            # For count_only with JOINs, we don't need all the columns
            if count_only and needs_join_for_filters:
                # table_name validated - safe from SQL injection
                sql = (
                    f'SELECT COUNT(*) FROM "{self.table_name}" AS t0 '  # noqa: S608
                    f"{join_clause}"
                )
            elif self._fields:
                # Build custom field selection with JOINs
                field_list = ", ".join(f't0."{f}"' for f in self._fields)
                # table_name and fields validated - safe from SQL injection
                sql = (
                    f"SELECT {field_list} FROM "  # noqa: S608
                    f'"{self.table_name}" AS t0 {join_clause}'
                )
                # Rebuild column_names to match selected fields only
                column_names = [
                    ("t0", field, self.model_class) for field in self._fields
                ]
            else:
                # table_name validated - safe from SQL injection
                sql = (
                    f"SELECT {select_clause} FROM "  # noqa: S608
                    f'"{self.table_name}" AS t0 {join_clause}'
                )

            # Build WHERE clause with special handling for NULL
            values, where_clause = self._parse_filter()

            if self.filters:
                sql += f" WHERE {where_clause}"

            if self._order_by:
                # Qualify ORDER BY column with t0 alias to avoid ambiguity
                # Extract field name and direction from _order_by
                # _order_by format: '"field" ASC' or '"field" DESC'
                match = re.match(r'"([^"]+)"\s+(.*)', self._order_by)
                if match:
                    field_name = match.group(1)
                    direction = match.group(2)
                    sql += f' ORDER BY t0."{field_name}" {direction}'
                elif self._order_by.lower().startswith("rowid"):
                    # Fallback for non-quoted patterns such as "rowid DESC"
                    sql += f" ORDER BY t0.{self._order_by}"

            if self._limit is not None:
                sql += " LIMIT ?"
                values.append(self._limit)

            if self._offset is not None:
                sql += " OFFSET ?"
                values.append(self._offset)

            # Log the SQL if debug is enabled
            if self.db.debug:
                self.db._log_sql(sql, values)  # noqa: SLF001

            try:
                conn = self.db.connect()
                cursor = conn.cursor()
                cursor.execute(sql, values)
                results = (
                    cursor.fetchall() if not fetch_one else cursor.fetchone()
                )
            except sqlite3.Error as exc:
                raise RecordFetchError(self.table_name) from exc
            else:
                return (results, column_names)

        # Non-JOIN query path (original behavior)
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

        sql = f'SELECT {fields} FROM "{self.table_name}"'  # noqa: S608

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

        # Log the SQL if debug is enabled
        if self.db.debug:
            self.db._log_sql(sql, values)  # noqa: SLF001

        try:
            conn = self.db.connect()
            cursor = conn.cursor()
            cursor.execute(sql, values)
            results = cursor.fetchall() if not fetch_one else cursor.fetchone()
        except sqlite3.Error as exc:
            raise RecordFetchError(self.table_name) from exc
        else:
            return (results, [])  # Empty column_names for backward compat

    def _parse_filter(self) -> tuple[list[Any], str]:
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

    def _convert_row_to_model(self, row: tuple[Any, ...]) -> T:
        """Convert a database row to a model instance.

        Args:
            row: A tuple representing a database row.

        Returns:
            An instance of the model class populated with the row data.
        """
        if self._fields:
            data = {
                field: self._deserialize(field, row[idx])
                for idx, field in enumerate(self._fields)
            }
            instance = self.model_class.model_validate_partial(data)
        else:
            data = {
                field: self._deserialize(field, row[idx])
                for idx, field in enumerate(self.model_class.model_fields)
            }
            # For ORM mode, exclude FK descriptor fields from data
            for fk_field in getattr(self.model_class, "fk_descriptors", {}):
                data.pop(fk_field, None)
            instance = self.model_class(**data)

        # Set db_context for ORM lazy loading and reverse relationships
        if hasattr(instance, "db_context"):
            instance.db_context = self.db
        return instance

    def _convert_joined_row_to_model(
        self,
        row: tuple[Any, ...],
        column_names: list[tuple[str, str, type[BaseDBModel]]],
    ) -> T:
        """Convert a JOINed database row to model instances with relationships.

        This method parses aliased columns from JOIN queries, creates the main
        model instance, and populates related objects in the _fk_cache to avoid
        lazy loading.

        Args:
            row: A tuple representing a database row from a JOIN query.
            column_names: List of (alias, field_name, model_class) tuples
                describing each column in the result.

        Returns:
            An instance of the main model class with populated relationships.
        """
        # Group columns by table alias
        tables_data: dict[str, dict[str, Any]] = {}
        tables_models: dict[str, type[BaseDBModel]] = {}

        for idx, (alias, field_name, model_class) in enumerate(column_names):
            if alias not in tables_data:
                tables_data[alias] = {}
                tables_models[alias] = model_class
            tables_data[alias][field_name] = row[idx]

        # Build main model (t0)
        main_data = tables_data["t0"]

        # Deserialize and create main instance
        main_instance_data = {
            field: self._deserialize(field, main_data[field])
            for field in self.model_class.model_fields
            if field in main_data
        }

        # For ORM mode, exclude FK descriptor fields from data
        for fk_field in getattr(self.model_class, "fk_descriptors", {}):
            main_instance_data.pop(fk_field, None)

        if self._fields:
            # Partial field selection: use model_validate_partial to
            # avoid validation errors for missing required fields
            main_instance = self.model_class.model_validate_partial(
                main_instance_data
            )
        else:
            main_instance = self.model_class(**main_instance_data)
        main_instance.db_context = self.db  # type: ignore[attr-defined]

        # Process JOINed tables and populate _fk_cache
        # Track instances per alias for nested cache wiring
        instances_by_alias: dict[str, BaseDBModel] = {"t0": main_instance}

        for join_info in self._join_info:
            alias = join_info.alias
            related_data = tables_data.get(alias)
            if related_data is None:
                continue

            # Check if all fields are NULL (LEFT JOIN with no match)
            if all(v is None for v in related_data.values()):
                # No related object, skip
                continue

            # Deserialize related object
            related_instance_data = {
                field: self._deserialize(field, related_data[field])
                for field in join_info.model_class.model_fields
                if field in related_data
            }

            # Exclude FK descriptors from related data
            for fk_field in getattr(
                join_info.model_class, "fk_descriptors", {}
            ):
                related_instance_data.pop(fk_field, None)

            related_instance = join_info.model_class(**related_instance_data)
            related_instance.db_context = self.db  # type: ignore[attr-defined]

            instances_by_alias[alias] = related_instance

            # Attach to parent instance cache (supports nesting)
            parent_instance = instances_by_alias.get(join_info.parent_alias)
            if parent_instance is not None:
                parent_fk_cache = getattr(parent_instance, "_fk_cache", {})
                parent_fk_cache[join_info.fk_field] = related_instance
                object.__setattr__(
                    parent_instance, "_fk_cache", parent_fk_cache
                )

        return main_instance

    def _deserialize(
        self, field_name: str, value: SerializableField
    ) -> SerializableField:
        """Deserialize a field value if needed.

        Args:
            field_name: Name of the field being deserialized.
            value: Value from the database.

        Returns:
            The deserialized value.
        """
        return self.model_class.deserialize_field(
            field_name, value, return_local_time=self.db.return_local_time
        )

    def bypass_cache(self) -> Self:
        """Bypass the cache for this specific query.

        When called, the query will always hit the database regardless of
        the global cache setting. This is useful for queries that require
        fresh data.

        Returns:
            The QueryBuilder instance for method chaining.

        Example:
            >>> db.select(User).filter(name="Alice").bypass_cache().fetch_one()
        """
        self._bypass_cache = True
        return self

    def cache_ttl(self, ttl: int) -> Self:
        """Set a custom TTL (time-to-live) for this specific query.

        When called, the cached result of this query will expire after the
        specified number of seconds, overriding the global cache_ttl setting.

        Args:
            ttl: Time-to-live in seconds for the cached result.

        Returns:
            The QueryBuilder instance for method chaining.

        Raises:
            ValueError: If ttl is negative.

        Example:
            >>> db.select(User).cache_ttl(60).fetch_all()
        """
        if ttl < 0:
            msg = "TTL must be non-negative"
            raise ValueError(msg)
        self._query_cache_ttl = ttl
        return self

    def _make_cache_key(self, *, fetch_one: bool) -> str:
        """Generate a cache key from the current query state.

        Args:
            fetch_one: Whether this is a fetch_one or fetch_all query.

        Returns:
            A SHA256 hash representing the current query state.

        Raises:
            ValueError: If filters contain incomparable types that prevent
                cache key generation (e.g., filtering the same field with
                both string and numeric values).
        """
        # Sort filters for consistent cache keys
        # Note: This requires filter values to be comparable. Avoid filtering
        # the same field with incompatible types (e.g., name="Alice" and
        # name=42 in the same query).
        try:
            sorted_filters = sorted(self.filters)
        except TypeError as exc:
            msg = (
                "Cannot generate cache key: filters contain incomparable "
                "types. Avoid filtering the same field with incompatible "
                "value types (e.g., strings and numbers)."
            )
            raise ValueError(msg) from exc

        # Create a deterministic representation of the query
        key_parts = {
            "table": self.table_name,
            "filters": sorted_filters,
            "limit": self._limit,
            "offset": self._offset,
            "order_by": self._order_by,
            "fields": tuple(sorted(self._fields)) if self._fields else None,
            "fetch_one": fetch_one,
            "select_related": tuple(sorted(self._select_related_paths)),
        }

        # Hash the key parts
        key_json = json.dumps(key_parts, sort_keys=True, default=str)
        return hashlib.sha256(key_json.encode()).hexdigest()

    @overload
    def _fetch_result(self, *, fetch_one: Literal[True]) -> Optional[T]: ...

    @overload
    def _fetch_result(self, *, fetch_one: Literal[False]) -> list[T]: ...

    def _fetch_result(  # noqa: C901, PLR0911
        self, *, fetch_one: bool = False
    ) -> Union[list[T], Optional[T]]:
        """Fetch and convert query results to model instances.

        Args:
            fetch_one: If True, fetch only one result.

        Returns:
            A list of model instances, a single model instance, or None if no
            results are found.
        """
        # Check cache first (unless bypass is enabled)
        if not self._bypass_cache:
            cache_key = self._make_cache_key(fetch_one=fetch_one)
            hit, cached = self.db._cache_get(self.table_name, cache_key)  # noqa: SLF001
            if hit:
                # Cache stores correctly typed data, cast from Any
                return cast("Union[list[T], Optional[T]]", cached)

        result, column_names = self._execute_query(fetch_one=fetch_one)

        if not result:
            if not self._bypass_cache:
                # Generate cache key for empty result
                cache_key = self._make_cache_key(fetch_one=fetch_one)
                if fetch_one:
                    # Cache empty result
                    self.db._cache_set(  # noqa: SLF001
                        self.table_name,
                        cache_key,
                        None,
                        ttl=self._query_cache_ttl,
                    )
                    return None
                # Cache empty list
                self.db._cache_set(  # noqa: SLF001
                    self.table_name, cache_key, [], ttl=self._query_cache_ttl
                )
                return []
            return None if fetch_one else []

        # Convert results based on whether we have JOIN data
        if column_names:
            # JOIN-aware converter - needs column_names
            if fetch_one:
                # When fetch_one=True, result is a single tuple
                # Narrow the type from the union
                single_row: tuple[Any, ...] = (
                    result if isinstance(result, tuple) else result[0]
                )
                single_result = self._convert_joined_row_to_model(
                    single_row, column_names
                )
                if not self._bypass_cache:
                    cache_key = self._make_cache_key(fetch_one=True)
                    self.db._cache_set(  # noqa: SLF001
                        self.table_name,
                        cache_key,
                        single_result,
                        ttl=self._query_cache_ttl,
                    )
                return single_result

            # When fetch_one=False, result is a list of tuples
            # Narrow the type from the union
            row_list: list[tuple[Any, ...]] = (
                result if isinstance(result, list) else [result]
            )
            list_results = [
                self._convert_joined_row_to_model(row, column_names)
                for row in row_list
            ]
            if not self._bypass_cache:
                cache_key = self._make_cache_key(fetch_one=False)
                self.db._cache_set(  # noqa: SLF001
                    self.table_name,
                    cache_key,
                    list_results,
                    ttl=self._query_cache_ttl,
                )
            return list_results

        # Standard converter
        if fetch_one:
            std_single_row: tuple[Any, ...] = (
                result if isinstance(result, tuple) else result[0]
            )
            single_result = self._convert_row_to_model(std_single_row)
            if not self._bypass_cache:
                cache_key = self._make_cache_key(fetch_one=True)
                self.db._cache_set(  # noqa: SLF001
                    self.table_name,
                    cache_key,
                    single_result,
                    ttl=self._query_cache_ttl,
                )
            return single_result

        std_row_list: list[tuple[Any, ...]] = (
            result if isinstance(result, list) else [result]
        )
        list_results = [self._convert_row_to_model(row) for row in std_row_list]
        if not self._bypass_cache:
            cache_key = self._make_cache_key(fetch_one=False)
            self.db._cache_set(  # noqa: SLF001
                self.table_name,
                cache_key,
                list_results,
                ttl=self._query_cache_ttl,
            )
        return list_results

    def fetch_all(self) -> list[T]:
        """Fetch all results of the query.

        Returns:
            A list of model instances representing all query results.
        """
        return self._fetch_result(fetch_one=False)

    def fetch_one(self) -> Optional[T]:
        """Fetch a single result of the query.

        Returns:
            A single model instance or None if no result is found.
        """
        return self._fetch_result(fetch_one=True)

    def fetch_first(self) -> Optional[T]:
        """Fetch the first result of the query.

        Returns:
            The first model instance or None if no result is found.
        """
        self._limit = 1
        return self._fetch_result(fetch_one=True)

    def fetch_last(self) -> Optional[T]:
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
        result, _column_names = self._execute_query(count_only=True)

        return int(result[0][0]) if result else 0

    def exists(self) -> bool:
        """Check if any results exist for the current query.

        Returns:
            True if at least one result exists, False otherwise.
        """
        return self.count() > 0

    def delete(self) -> int:
        """Delete records that match the current query conditions.

        Returns:
            The number of records deleted.

        Raises:
            RecordDeletionError: If there's an error deleting the records.
        """
        sql = f'DELETE FROM "{self.table_name}"'  # nosec  # noqa: S608

        # Build the WHERE clause with special handling for None (NULL in SQL)
        values, where_clause = self._parse_filter()

        if self.filters:
            sql += f" WHERE {where_clause}"

        # Print the raw SQL and values if debug is enabled
        if self.db.debug:
            self.db._log_sql(sql, values)  # noqa: SLF001

        try:
            conn = self.db.connect()
            cursor = conn.cursor()
            cursor.execute(sql, values)
            deleted_count = cursor.rowcount
            self.db._maybe_commit()  # noqa: SLF001
            self.db._cache_invalidate_table(self.table_name)  # noqa: SLF001
        except sqlite3.Error as exc:
            # Rollback implicit transaction if not in user-managed transaction
            if not self.db._in_transaction and self.db.conn:  # noqa: SLF001
                self.db.conn.rollback()
            raise RecordDeletionError(self.table_name) from exc
        else:
            return deleted_count
