# Table Operations

All table operations work on a Pydantic Model you have [defined](models.md)
based on `BaseDBModel`. You can have as many tables as you need, but each must
have it's own Model defined.

## Creating Tables

To create a table, you simply pass your Model class to the `create_table()`
method:

```python
db.create_table(User)
```

> [!IMPORTANT]
>
> The Table is created **regardless** of the `auto_commit` setting.

By default, if the table already exists, it will not be created again and no
error will be raised. If you want to raise an exception if the table already
exists, you can set `exists_ok=False`:

```python
db.create_table(User, exists_ok=False)
```

This will raise a `TableCreationError` if the table already exists.

There is a complementary flag `force=True` which will drop the table if it
exists and then recreate it. This may be useful if you are changing the table
structure:

```python
db.create_table(User, force=True)
```

This defaults to `False`.

## Dropping Tables

To drop a table completely from the database use the `drop_table` method

```python
db.drop_table(User)
```

> [!CAUTION]
>
> This is **non-reversible** and will you will lose **all data** in that table.
>
> The Table is dropped **regardless** of the `auto_commit` setting.
