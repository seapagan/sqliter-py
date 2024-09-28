# Ordering

For now we only support ordering by the single field. You can specify the
field to order by and whether to reverse the order:

```python
results = db.select(User).order("age", reverse=True).fetch_all()
```

This will order the results by the `age` field in descending order.

If you do not specify a field, the default is to order by the primary key field:

```python
results = db.select(User).order().fetch_all()
```

This will order the results by the primary key field in ascending order.

> [!WARNING]
>
> Previously ordering was done using the `direction` parameter with `asc` or
> `desc`, but this has been deprecated in favor of using the `reverse`
> parameter. The `direction` parameter still works, but will raise a
> `DeprecationWarning` and will be removed in a future release.
