# Models

Each individual table in your database should be represented by a model. This
model should inherit from `BaseDBModel` and define the fields that should be
stored in the table. Under the hood, the model is a Pydantic model, so you can
use all the features of Pydantic models, such as default values, type hints, and
validation.

## Defining Models

Models are defined like this:

```python
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    name: str
    age: int
    email: str
```

You can create as many Models as you need, each representing a different table
in your database. The fields in the model will be used to create the columns in
the table.

> [!IMPORTANT]
>
> - Type-hints are **REQUIRED** for each field in the model.
> - The Model **automatically** creates an **auto-incrementing integer primary
> key** for each table called `pk`, you do not need to define it yourself.
> - The Model **automatically** creates a `created_at` and `updated_at` field
> which is an integer Unix timestamp **IN UTC** when the record was created or
> last updated. You can convert this timestamp to any format and timezone that
> you need.

### Field Types

The following field types are currently supported:

Basic Types:

- `str`
- `int`
- `float`
- `bool`
- `date`
- `datetime`
- `bytes`

Complex Types:

- `list[T]` - Lists of any type T
- `dict[K, V]` - Dictionaries with keys of type K and values of type V
- `set[T]` - Sets of any type T
- `tuple[T, ...]` - Tuples of any type T

Complex types are automatically serialized and stored as BLOBs in the database. For more details on using complex types, see the [Fields Guide](fields.md#complex-data-types).

### Adding Indexes

You can add indexes to your table by specifying the `indexes` attribute in the
`Meta` class. This should be a list of strings, each string being the name of an
existing field in the model that should be indexed.

```python
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    name: str
    age: int
    email: str

    class Meta:
        indexes = ["name", "email"]
```

This is in addition to the primary key index (`pk`) that is automatically
created.

### Adding Unique Indexes

You can add unique indexes to your table by specifying the `unique_indexes`
attribute in the `Meta` class. This should be a list of strings, each string
being the name of an existing field in the model that should be indexed.

```python
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    name: str
    age: int
    email: str

    class Meta:
        unique_indexes = ["email"]
```

These will ensure that all values in this field are unique. This is in addition
to the primary key index (`pk`) that is automatically created.

> [!TIP]
>
> You can specify both `indexes` and `unique_indexes` in the `Meta` class if you
> need to.

### Unique Fields

You can also specify that a field should be all unique values by using the
`unique()` method from the `sqliter.model` module. This will ensure that all
values in this field are unique.

```python
from typing import Annotated
from sqliter.model import BaseDBModel, unique

class User(BaseDBModel):
    name: str
    age: int
    email: Annotated[str, unique()]
```

This will raise either a `RecordInsertionError` or `RecordUpdateError` if you
try to insert or update a record with a duplicate value in the chosen field.

> [!TIP]
>
> Using `Annotated` is optional, but without it your code wil not pass
> type-checking with `mypy`. It will work fine at runtime but is not recommended:
>
> ```python
>     email: str = unique()
>
>```
>
> This will give the following Mypy error:
>
> ```pre
> error: Incompatible types in assignment (expression has type "unique", variable has type "str")  [assignment]
>```
>
> If you DONT use a static type checker (`mypy`, `ty` or similar) then you can
> leave off the `Annotated`.

> [!CAUTION]
>
> In version 0.9.1 and below, this flag was `Unique()` with a capital 'U'. This
> has now been deprecated to the current `unique()` with a lower case 'u'.
>
> The old functionality still works but will raise a deprecation warning and
> will probably be removed in future versions.

### Custom Table Name

By default, the table name will be the same as the model name, converted to
'snake_case' and pluralized (e.g., `User` -> `users`). Also, any 'Model' suffix
will be removed (e.g., `UserModel` -> `users`). To override this behavior, you
can specify the `table_name` in the `Meta` class manually as below:

```python
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    name: str
    age: int
    email: str

    class Meta:
        table_name = "people"
```

> [!NOTE]
>
> The pluralization is pretty basic by default, and just consists of adding an
> 's' if not already there. This will fail on words like 'person' or 'child'. If
> you need more advanced pluralization, you can install the `extras` package as
> mentioned in the [installation](../installation.md#optional-dependencies). Of
> course, you can always specify the `table_name` manually in this case!

## Model Classmethods

There are 2 useful methods you can call on your models. Note that they are
**Class Methods** so should be called on the Model class itself, not an
instance of the model:

### `get_table_name()`

This method returns the actual table name for the model either specified or
automatically generated. This is useful if you need to do any raw SQL queries.

```python
table_name = User.get_table_name()
```

### `get_primary_key()`

This simply returns the name of the primary key for that table. At the moment,
this will always return the string `pk` but this may change in the future.

```python
primary_key = User.get_primary_key()
```
