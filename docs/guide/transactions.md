# Transactions

SQLiter supports transactions using Python's context manager:

```python
with db:
    db.insert(User(name="Alice", age=30, email="alice@example.com"))
    db.insert(User(name="Bob", age=35, email="bob@example.com"))
    # If an exception occurs, the transaction will be rolled back
```

> [!WARNING]
> **Known Issue:** Transaction rollback is currently broken. Changes made
> inside a transaction are NOT rolled back when an exception occurs.
>
> **Status:** This is being tracked in [issue #104](https://github.com/seapagan/sqliter-py/issues/104).
>
> **Workaround:** Do not rely on transaction rollback for data integrity until
> this is fixed. All changes are committed immediately.
>
> Using the context manager will automatically commit the transaction at the end
> (unless an exception occurs), regardless of the `auto_commit` setting. The
> `close()` method will also be called when the context manager exits, so you
> do not need to call it manually.
