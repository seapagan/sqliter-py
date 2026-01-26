# Filtering Results

The `filter()` method in SQLiter supports various filter options to query
records, and can be combined with other methods like `order()`, `limit()`, and
`offset()` to build more complex queries:

```python
result = db.select(User).filter(age__lte=30).limit(10).fetch_all()
```

It is possible to both add multiple filters in the same call, and to chain
multiple filter calls together:

```python
result = db.select(User).filter(age__gte=20, age__lte=30).fetch_all()
```

```python
result = db.select(User).filter(age__gte=20).filter(age__lte=30).fetch_all()
```

## Basic Filters

- `__eq`: Equal to (default if no operator is specified)
  - Example: `name="John"` or `name__eq="John"`

## Null Checks

- `__isnull`: Is NULL
  - Example: `email__isnull=True`
- `__notnull`: Is NOT NULL
  - Example: `email__notnull=True`

## Comparison Operators

- `__lt`: Less than
  - Example: `age__lt=30`
- `__lte`: Less than or equal to
  - Example: `age__lte=30`
- `__gt`: Greater than
  - Example: `age__gt=30`
- `__gte`: Greater than or equal to
  - Example: `age__gte=30`
- `__ne`: Not equal to
  - Example: `status__ne="inactive"`

## List Operations

- `__in`: In a list of values
  - Example: `status__in=["active", "pending"]`
- `__not_in`: Not in a list of values
  - Example: `category__not_in=["archived", "deleted"]`

> **Note:** List values are only valid with `__in` and `__not_in` operators.
> Using lists with equality or comparison operators (`__eq`, `__lt`, `__gt`, etc.)
> will raise a `TypeError`. These operators require scalar values.

## Pattern Matching

### LIKE Operator

The `__like` operator provides SQL LIKE pattern matching with wildcards:

- `%` matches any sequence of characters (including zero characters)
- `_` matches any single character

```python
# Starts with 'A'
users = db.select(User).filter(name__like="A%").fetch_all()

# Ends with 'son'
users = db.select(User).filter(name__like="%son").fetch_all()

# Contains 'mid' anywhere
users = db.select(User).filter(description__like="%mid%").fetch_all()

# Exactly 3 characters ending in 'ob'
users = db.select(User).filter(name__like="_ob").fetch_all()
```

#### Case Sensitivity Limitations

SQLite's `LIKE` operator is **case-insensitive only for ASCII characters (A-Z)**:

```python
# ✅ Case-insensitive for ASCII
users = db.select(User).filter(name__like="alice").fetch_all()
# Matches: "Alice", "ALICE", "alice"

# ❌ Case-SENSITIVE for non-ASCII Unicode characters
users = db.select(User).filter(name__like="café").fetch_all()
# Does NOT match: "CAFÉ" or "Café"
# Only matches: "café"
```

**For Unicode-aware case-insensitive matching**, use the `__icontains`,
`__istartswith`, or `__iendswith` operators instead:

```python
# ✅ Case-insensitive for all Unicode characters
users = db.select(User).filter(name__icontains="café").fetch_all()
# Matches: "café", "CAFÉ", "Café", "Grand Café"

users = db.select(User).filter(name__istartswith="café").fetch_all()
# Matches: "café", "CAFÉ", "Café Noir"
```

> [!WARNING]
>
> The `LIKE` operator in SQLite is only case-insensitive for ASCII letters.
> If your data includes accented characters, non-Latin scripts, or any
> non-ASCII text, use `__icontains`, `__istartswith`, or `__iendswith` for
> reliable case-insensitive matching

## String Operations (Case-Sensitive)

- `__startswith`: Starts with
  - Example: `name__startswith="A"`
- `__endswith`: Ends with
  - Example: `email__endswith=".com"`
- `__contains`: Contains
  - Example: `description__contains="important"`

## String Operations (Case-Insensitive)

- `__istartswith`: Starts with (case-insensitive)
  - Example: `name__istartswith="a"`
- `__iendswith`: Ends with (case-insensitive)
  - Example: `email__iendswith=".COM"`
- `__icontains`: Contains (case-insensitive)
  - Example: `description__icontains="IMPORTANT"`
