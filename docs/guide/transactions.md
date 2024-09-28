# Transactions

SQLiter supports transactions using Python's context manager:

```python
with db:
    db.insert(User(name="Alice", age=30, email="alice@example.com"))
    db.insert(User(name="Bob", age=35, email="bob@example.com"))
    # If an exception occurs, the transaction will be rolled back
```

> [!WARNING]
> Using the context manager will automatically commit the transaction
> at the end (unless an exception occurs), regardless of the `auto_commit`
> setting.
>
> the `close()` method will also be called when the context manager exits, so you
> do not need to call it manually.
