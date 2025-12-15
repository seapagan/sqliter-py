"""Define a custom field type for unique constraints in SQLiter."""

from typing import Any

from pydantic import Field


def unique(default: Any = ..., **kwargs: Any) -> Any:  # noqa: ANN401
    """A custom field type for unique constraints in SQLiter.

    Args:
        default: The default value for the field.
        **kwargs: Additional keyword arguments to pass to Field.

    Returns:
        A Field with unique metadata attached.
    """
    # Extract any existing json_schema_extra from kwargs
    existing_extra = kwargs.pop("json_schema_extra", {})

    # Ensure it's a dict
    if not isinstance(existing_extra, dict):
        existing_extra = {}

    # Add our unique marker to json_schema_extra
    existing_extra["unique"] = True

    return Field(default=default, json_schema_extra=existing_extra, **kwargs)
