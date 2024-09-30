# Data Operations

## Inserting Records

The `insert()` method is used to add records to the database. You pass an
instance of your model class to the method, and SQLiter will insert the record
into the correct table:

```python
user = User(name="Jane Doe", age=25, email="jane@example.com")
db.insert(user)
```

> [!IMPORTANT]
>
> The `insert()` method will raise a `RecordInsertionError` if you try to insert
> a record with a primary key that already exists in the table. Also, if the
> table does not exist, a `RecordInsertionError` will be raised.

## Querying Records

`SQLiter` provides a simple and intuitive API for querying records from the
database, Starting with the `select()` method and chaining other methods to
filter, order, limit, and offset the results:

```python
# Fetch all users
all_users = db.select(User).fetch_all()

# Filter users
young_users = db.select(User).filter(age=25).fetch_all()

# Order users
ordered_users = db.select(User).order("age", reverse=True).fetch_all()

# Limit and offset
paginated_users = db.select(User).limit(10).offset(20).fetch_all()
```

> [!IMPORTANT]
>
> The `select()` MUST come first, before any filtering, ordering, or pagination
> etc. This is the starting point for building your query.

See [Filtering Results](filtering.md) for more advanced filtering options.

## Updating Records

```python
user.age = 26
db.update(user)
```

## Deleting Records

```python
db.delete(User, "Jane Doe")
```

## Commit your changes

By default, SQLiter will automatically commit changes to the database after each
operation. If you want to disable this behavior, you can set `auto_commit=False`
when creating the database connection:

```python
db = SqliterDB("your_database.db", auto_commit=False)
```

You can then manually commit changes using the `commit()` method:

```python
db.commit()
```

> [!NOTE]
>
> If you are using the database connection as a context manager (see
> [tansactions](transactions.md)), you do not need to call `commit()`
> explicitly. The connection will be closed automatically when the context
> manager exits, and any changes **will be committed**.

## Close the Connection

When you're done with the database connection, you should close it to release
resources:

```python
db.close()
```

Note that closing the connection will also commit any pending changes, unless
`auto_commit` is set to `False`.

> [!NOTE]
>
> If you are using the database connection as a context manager (see
> [tansactions](transactions.md)), you do not need to call `close()` explicitly.
> The connection will be closed automatically when the context manager exits,
> and any changes **will be committed**.