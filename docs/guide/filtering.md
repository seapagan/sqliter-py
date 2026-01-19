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

## Pattern Matching

- `__like`: SQL LIKE pattern matching (SQLite default is case-insensitive for ASCII)
  - Use `%` for any sequence of characters
  - Use `_` for any single character
  - Example: `name__like="A%"` (starts with A)
  - Example: `name__like="%son"` (ends with "son")
  - Example: `name__like="%mid%"` (contains "mid")
  - Example: `name__like="_ob"` (3 characters ending in "ob")

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
