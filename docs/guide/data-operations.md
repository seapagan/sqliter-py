# Data Operations

## Inserting Records

The `insert()` method is used to add records to the database. You pass an
instance of your model class to the method, and SQLiter will insert the record
into the correct table:

```python
user = User(name="Jane Doe", age=25, email="jane@example.com")
result = db.insert(user)
```

The `result` variable will contain a new instance of the model, with the primary
key value set to the newly-created primary key in the database. You should use
this instance to access the primary key value and other fields:

```python
print(f"New record inserted with primary key: {result.pk}")
print(f"Name: {result.name}, Age: {result.age}, Email: {result.email}")
```

### Overriding the Timestamps

By default, SQLiter will automatically set the `created_at` and `updated_at`
fields to the current Unix timestamp in UTC when a record is inserted. If you
want to override this behavior, you can set the `created_at` and `updated_at`
fields manually before calling `insert()`:

```python
import time

user.created_at = int(time.time())
user.updated_at = int(time.time())
```

However, by default **this is disabled**. Any model passed to `insert()` will
have the `created_at` and `updated_at` fields set automatically and ignore any
values passed in these 2 fields.

If you want to enable this feature, you can set the `timestamp_override` flag to `True`
when inserting the record:

```python
result = db.insert(user, timestamp_override=True)
```

> [!IMPORTANT]
>
> The `insert()` method will raise a `RecordInsertionError` if you try to insert
> a record with a primary key that already exists in the table or if the table
> does not exist.

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

You can update records in the database by modifying the fields of the model
instance and then calling the `update()` method. You just pass the model
instance to the method:

```python
user.age = 26
db.update(user)
```

> [!IMPORTANT]
>
> The model you pass must have a primary key value set, otherwise an error will
> be raised. In other words, you use the instance of a model returned by the
> `insert()` method to update the record as it has the primary key value set,
> not the original instance you passed to `insert()`.
>
> You can also set the primary key value on the model instance manually before
> calling `update()` if you have that.

On suffescul update, the `updated_at` field will be set to the current Unix
timestamp in UTC by default.

> [!WARNING]
>
> Unlike with the `insert()` method, you **CANNOT** override the `updated_at`
> field when calling `update()`. It will always be set to the current Unix
> timestamp in UTC. This is to ensure that the `updated_at` field is always
> accurate.

## Deleting Records

To delete a record from the database, you need to pass the model class and the
primary key value of the record you want to delete:

```python
db.delete(User, user.pk)
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
