# Defining Models

Models in SQLiter use Pydantic to encapsulate the logic. All models should
inherit from SQLiter's `BaseDBModel`. You can define your
models like this:

```python
from sqliter.model import BaseDBModel

class User(BaseDBModel):
    name: str
    age: int
    email: str

    class Meta:
        table_name = "users"
        primary_key = "name"  # Default is "id"
        create_pk = False  # disable auto-creating an incrementing primary key - default is True
```

For a standard database with an auto-incrementing integer `id` primary key, you
do not need to specify the `primary_key` or `create_pk` fields. If you want to
specify a different primary key field name, you can do so using the
`primary_key` field in the `Meta` class.

If `table_name` is not specified, the table name will be the same as the model
name, converted to 'snake_case' and pluralized (e.g., `User` -> `users`). Also,
any 'Model' suffix will be removed (e.g., `UserModel` -> `users`). To override
this behavior, you can specify the `table_name` in the `Meta` class manually as
above.

> [!NOTE]
>
> The pluralization is pretty basic by default, and just consists of adding an
> 's' if not already there. This will fail on words like 'person' or 'child'. If
> you need more advanced pluralization, you can install the `extras` package as
> mentioned in the [installation](../installation.md#optional-dependencies). Of
> course, you can always specify the `table_name` manually in this case!
