"""Define constants used in the library."""

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

# Mapping of Python types to SQLite types
SQLITE_TYPE_MAPPING = {
    int: "INTEGER",
    float: "REAL",
    str: "TEXT",
    bool: "INTEGER",  # SQLite stores booleans as integers (0 or 1)
    bytes: "BLOB",
}
