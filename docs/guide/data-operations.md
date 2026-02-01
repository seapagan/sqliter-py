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

## Bulk Inserting Records

Use `bulk_insert()` to insert multiple records of the same model in a single
transaction. This is more efficient than calling `insert()` in a loop because
all records are committed together:

```python
users = [
    User(name="Alice", age=30, email="alice@example.com"),
    User(name="Bob", age=25, email="bob@example.com"),
    User(name="Carol", age=28, email="carol@example.com"),
]
results = db.bulk_insert(users)
```

The returned list contains new model instances with primary keys assigned:

```python
for user in results:
    print(f"Inserted {user.name} with pk={user.pk}")
```

Passing an empty list returns `[]` without touching the database. If any record
in the batch fails (for example, a foreign key constraint violation), the
entire batch is rolled back and no records are inserted.

### Overriding the Timestamps

Like `insert()`, `bulk_insert()` automatically sets `created_at` and
`updated_at` on each record. Pass `timestamp_override=True` to preserve
values you set manually:

```python
results = db.bulk_insert(users, timestamp_override=True)
```

### Using with Transactions

When called inside a `with db:` transaction context, `bulk_insert()` defers
the commit to the context exit, so you can combine it with other operations in
one atomic transaction:

```python
with db:
    authors = db.bulk_insert(author_list)
    books = db.bulk_insert(book_list)
    # Both batches committed together on exit
```

> [!IMPORTANT]
>
> All instances passed to `bulk_insert()` must be of the same model type.
> Mixing different model types raises a `ValueError`.

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

SQLiter provides two ways to delete records:

### Single Record Deletion

To delete a single record from the database by its primary key, use the `delete()` method directly on the database instance:

```python
db.delete(User, user.pk)
```

> [!IMPORTANT]
>
> The single record deletion method will raise:
>
> - `RecordNotFoundError` if the record with the specified primary key is not found
> - `RecordDeletionError` if there's an error during the deletion process

### Query-Based Deletion

You can also use a query to delete records that match specific criteria. The `delete()` method will delete all records returned by the query and return an integer with the count of records deleted:

```python
# Delete all users over 30
deleted_count = db.select(User).filter(age__gt=30).delete()

# Delete inactive users in a specific age range
deleted_count = db.select(User).filter(
    age__gte=25,
    age__lt=40,
    status="inactive"
).delete()

# Delete all records from a table
deleted_count = db.select(User).delete()
```

> [!NOTE]
>
> The query-based delete operation ignores any `limit()`, `offset()`, or `order()`
> clauses that might be in the query chain. It will always delete ALL records
> that match the filter conditions.

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
