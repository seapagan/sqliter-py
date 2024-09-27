"""Constant values and mappings used throughout SQLiter.

This module defines constant dictionaries that map SQLiter-specific
concepts to their SQLite equivalents. It includes mappings for query
operators and data types, which are crucial for translating between
Pydantic models and SQLite database operations.
"""

# A dictionary mapping SQLiter filter operators to their corresponding SQL
# operators.
OPERATOR_MAPPING = {
    "__lt": "<",
    "__lte": "<=",
    "__gt": ">",
    "__gte": ">=",
    "__eq": "=",
    "__ne": "!=",
    "__in": "IN",
    "__not_in": "NOT IN",
    "__isnull": "IS NULL",
    "__notnull": "IS NOT NULL",
    "__startswith": "LIKE",
    "__endswith": "LIKE",
    "__contains": "LIKE",
    "__istartswith": "LIKE",
    "__iendswith": "LIKE",
    "__icontains": "LIKE",
}

# A dictionary mapping Python types to their corresponding SQLite column types.
SQLITE_TYPE_MAPPING = {
    int: "INTEGER",
    float: "REAL",
    str: "TEXT",
    bool: "INTEGER",  # SQLite stores booleans as integers (0 or 1)
    bytes: "BLOB",
}
