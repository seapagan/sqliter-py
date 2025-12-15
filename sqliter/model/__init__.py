"""This module provides the base model class for SQLiter database models.

It exports the BaseDBModel class, which is used to define database
models in SQLiter applications, and the unique function, which is used to
define unique constraints on model fields.
"""

from .model import BaseDBModel, SerializableField
from .unique import unique

# Backward compatibility alias (deprecated, will be removed in v1.0.0)
Unique = unique

__all__ = ["BaseDBModel", "SerializableField", "unique", "Unique"]
