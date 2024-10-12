"""Define a custom field type for unique constraints in SQLiter."""

from typing import Any

from pydantic.fields import FieldInfo


class Unique(FieldInfo):
    """A custom field type for unique constraints in SQLiter."""

    def __init__(self, default: Any = ..., **kwargs: Any) -> None:  # noqa: ANN401
        """Initialize a Unique field.

        Args:
            default: The default value for the field.
            **kwargs: Additional keyword arguments to pass to FieldInfo.
        """
        super().__init__(default=default, **kwargs)
        self.unique = True
