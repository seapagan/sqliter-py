"""This module provides the base model class for SQLiter database models.

It exports the BaseDBModel class, which is used to define database
models in SQLiter applications, and the unique function, which is used to
define unique constraints on model fields.
"""

import warnings
from typing import Any

from typing_extensions import deprecated

from .model import BaseDBModel, SerializableField
from .unique import unique


@deprecated("Use 'unique' instead. Will be removed in a future version.")
def Unique(default: Any = ..., **kwargs: Any) -> Any:  # noqa: ANN401, N802
    """Deprecated: Use 'unique' instead. Will be removed in a future version.

    Args:
        default: The default value for the field.
        **kwargs: Additional keyword arguments to pass to Field.

    Returns:
        A Field with unique metadata attached.
    """
    warnings.warn(
        "Unique is deprecated and will be removed in a future version. "
        "Use 'unique' instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return unique(default=default, **kwargs)


__all__ = ["BaseDBModel", "SerializableField", "Unique", "unique"]
