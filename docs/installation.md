# Installation

You can install SQLiter using whichever method you prefer or is compatible with
your project setup.

With `uv` which is rapidly becoming my favorite tool for managing projects and
virtual environments (`uv` is used for developing this project and in the CI):

```bash
uv add sqliter-py
```

With `Poetry`:

```bash
poetry add sqliter-py
```

Or with `pip`:

```bash
pip install sqliter-py
```

## Optional Dependencies

Currently by default, the only external dependency is Pydantic. However, there
are some optional dependencies that can be installed to enable additional
features:

- `inflect`: For grammatically correct pluralization. This is used in two places:
    1. **Table names**: When auto-generating table names from model classes
       (e.g., `Person` → `people` instead of `persons`)
    2. **Reverse relationships**: When auto-generating `related_name` for ORM
       foreign keys (e.g., `Category` → `categories` instead of `categorys`)

  Without `inflect`, a simple "s" suffix is added (unless the name already ends
  in "s"). In most cases, the default works fine, but `inflect` handles irregular
  plurals correctly.

These can be installed using `uv`:

```bash
uv add 'sqliter-py[extras]'
```

With `Poetry`:

```bash
poetry add 'sqliter-py[extras]'
```

Or with `pip`:

```bash
pip install 'sqliter-py[extras]'
```
