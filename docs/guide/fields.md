# Field Control

## Selecting Specific Fields

By default, all commands query and return all fields in the table. If you want
to select only specific fields, you can pass them using the `fields()`
method:

```python
results = db.select(User).fields(["name", "age"]).fetch_all()
```

This will return only the `name` and `age` fields for each record.

You can also pass this as a parameter to the `select()` method:

```python
results = db.select(User, fields=["name", "age"]).fetch_all()
```

Note that using the `fields()` method will override any fields specified in the
'select()' method.

## Excluding Specific Fields

If you want to exclude specific fields from the results, you can use the
`exclude()` method:

```python
results = db.select(User).exclude(["email"]).fetch_all()
```

This will return all fields except the `email` field.

You can also pass this as a parameter to the `select()` method:

```python
results = db.select(User, exclude=["email"]).fetch_all()
```

## Returning exactly one explicit field only

If you only want to return a single field from the results, you can use the
`only()` method:

```python
result = db.select(User).only("name").fetch_first()
```

This will return only the `name` field for the first record.

This is exactly the same as using the `fields()` method with a single field, but
very specific and obvious. **There is NO equivalent argument to this in the
`select()` method**. An exception **WILL** be raised if you try to use this method
with more than one field.
