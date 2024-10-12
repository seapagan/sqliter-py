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
