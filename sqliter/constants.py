"""Constant values and mappings used throughout SQLiter.

This module defines constant dictionaries that map SQLiter-specific
concepts to their SQLite equivalents. It includes mappings for query
operators and data types, which are crucial for translating between
Pydantic models and SQLite database operations.
"""

import datetime

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
    "__like": "LIKE",
    "__startswith": "GLOB",
    "__endswith": "GLOB",
    "__contains": "GLOB",
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
    datetime.datetime: "INTEGER",  # Store as Unix timestamp
    datetime.date: "INTEGER",  # Store as Unix timestamp
    list: "BLOB",
    dict: "BLOB",
    set: "BLOB",
    tuple: "BLOB",
}
