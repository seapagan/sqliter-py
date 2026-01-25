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

### Demo

The `demo` extra installs the **Textual** TUI framework, which is used for the
interactive demo application:

```bash
uv add sqliter-py[demo]
```

This enables the `sqliter-demo` command and the `python -m sqliter.tui` interface
for exploring SQLiter features interactively. See the [Interactive Demo](tui-demo/index.md)
documentation for more details.

### Extras

The `extras` extra installs **Inflect**, which is used for grammatically correct
pluralization:

1. **Table names**: When auto-generating table names from model classes
   (e.g., `Person` → `people` instead of `persons`)
2. **Reverse relationships**: When auto-generating `related_name` for ORM
   foreign keys (e.g., `Category` → `categories` instead of `categorys`)

Without `inflect`, a simple "s" suffix is added (unless the name already ends
in "s"). In most cases, the default works fine, but `inflect` handles irregular
plurals correctly.

Install with:

```bash
uv add 'sqliter-py[extras]'
```

### Full

The `full` extra installs **all** optional dependencies (both Textual and Inflect):

```bash
uv add sqliter-py[full]
```

This is recommended if you want access to all SQLiter features, including the
interactive demo and proper pluralization.

### Installation Summary

| Extra | Includes | Purpose |
|-------|----------|---------|
| *(none)* | Pydantic only | Basic ORM functionality |
| `demo` | + Textual | Interactive TUI demo |
| `extras` | + Inflect | Better pluralization |
| `full` | + Textual + Inflect | All features |
