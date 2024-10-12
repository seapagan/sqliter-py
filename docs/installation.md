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

- `inflect`: For pluralizing table names (if not specified). This just offers a
  more-advanced pluralization than the default method used. In most cases you
  will not need this.

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
