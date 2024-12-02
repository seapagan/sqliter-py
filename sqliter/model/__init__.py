"""This module provides the base model class for SQLiter database models.

It exports the BaseDBModel class, which is used to define database
models in SQLiter applications, and the Unique class, which is used to
define unique constraints on model fields.
"""

from .model import BaseDBModel, SerializableField
from .unique import Unique

__all__ = ["BaseDBModel", "SerializableField", "Unique"]
