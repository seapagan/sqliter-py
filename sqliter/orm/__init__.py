"""ORM submodule for SQLiter.

This module provides ORM functionality including lazy loading and reverse
relationships. It extends the BaseDBModel from sqliter.model without breaking
changes to the existing code.

Users can choose between modes via import:
    - Legacy mode: from sqliter.model import BaseDBModel
    - ORM mode: from sqliter.orm import BaseDBModel
"""

from sqliter.orm.foreign_key import ForeignKey
from sqliter.orm.model import BaseDBModel
from sqliter.orm.registry import ModelRegistry

__all__ = ["BaseDBModel", "ForeignKey", "ModelRegistry"]
