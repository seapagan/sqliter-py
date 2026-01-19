"""Model registry for ORM functionality.

Central registry for:
- Model classes by table name
- Foreign key relationships
- Pending reverse relationships
"""

from __future__ import annotations

from typing import Any, ClassVar, Optional


class ModelRegistry:
    """Registry for ORM models and FK relationships.

    Uses automatic setup via descriptor __set_name__ hook - no manual setup
    required.
    """

    _models: ClassVar[dict[str, type]] = {}
    _foreign_keys: ClassVar[dict[str, list[dict[str, Any]]]] = {}
    _pending_reverses: ClassVar[dict[str, list[dict[str, Any]]]] = {}

    @classmethod
    def register_model(cls, model_class: type[Any]) -> None:
        """Register a model class in the global registry.

        Args:
            model_class: The model class to register
        """
        table_name = model_class.get_table_name()
        cls._models[table_name] = model_class

        # Process any pending reverse relationships for this model
        if table_name in cls._pending_reverses:
            for pending in cls._pending_reverses[table_name]:
                cls._add_reverse_relationship_now(**pending)
            del cls._pending_reverses[table_name]

    @classmethod
    def register_foreign_key(
        cls,
        from_model: type[Any],
        to_model: type[Any],
        fk_field: str,
        on_delete: str,
        related_name: Optional[str] = None,
    ) -> None:
        """Register a FK relationship.

        Args:
            from_model: The model with the FK field
            to_model: The model being referenced
            fk_field: Name of the FK field
            on_delete: Action when related object is deleted
            related_name: Name for reverse relationship
        """
        from_table = from_model.get_table_name()

        if from_table not in cls._foreign_keys:
            cls._foreign_keys[from_table] = []

        cls._foreign_keys[from_table].append(
            {
                "to_model": to_model,
                "fk_field": fk_field,
                "on_delete": on_delete,
                "related_name": related_name,
            }
        )

    @classmethod
    def get_model(cls, table_name: str) -> Optional[type[Any]]:
        """Get model by table name.

        Args:
            table_name: The table name to look up

        Returns:
            The model class or None if not found
        """
        return cls._models.get(table_name)

    @classmethod
    def get_foreign_keys(cls, table_name: str) -> list[dict[str, Any]]:
        """Get FK relationships for a model.

        Args:
            table_name: The table name to look up

        Returns:
            List of FK relationship dictionaries
        """
        return cls._foreign_keys.get(table_name, [])

    @classmethod
    def add_reverse_relationship(
        cls,
        from_model: type[Any],
        to_model: type[Any],
        fk_field: str,
        related_name: str,
    ) -> None:
        """Automatically add reverse relationship descriptor during class.

        Called by ForeignKeyDescriptor.__set_name__ during class creation.
        If to_model doesn't exist yet, stores as pending and adds when
        to_model is registered.

        Args:
            from_model: The model with the FK field (e.g., Book)
            to_model: The model being referenced (e.g., Author)
            fk_field: Name of the FK field (e.g., "author")
            related_name: Name for reverse relationship (e.g., "books")
        """
        to_table = to_model.get_table_name()

        # Check if to_model has been registered yet
        if to_table in cls._models:
            # Model exists, add reverse relationship now
            cls._add_reverse_relationship_now(
                from_model, to_model, fk_field, related_name
            )
        else:
            # Model doesn't exist yet, store as pending
            if to_table not in cls._pending_reverses:
                cls._pending_reverses[to_table] = []
            cls._pending_reverses[to_table].append(
                {
                    "from_model": from_model,
                    "to_model": to_model,
                    "fk_field": fk_field,
                    "related_name": related_name,
                }
            )

    @classmethod
    def _add_reverse_relationship_now(
        cls,
        from_model: type[Any],
        to_model: type[Any],
        fk_field: str,
        related_name: str,
    ) -> None:
        """Add reverse relationship descriptor to model.

        Args:
            from_model: The model with the FK field (e.g., Book)
            to_model: The model being referenced (e.g., Author)
            fk_field: Name of the FK field (e.g., "author")
            related_name: Name for reverse relationship (e.g., "books")
        """
        from sqliter.orm.query import ReverseRelationship  # noqa: PLC0415

        # Guard against overwriting existing attributes
        if hasattr(to_model, related_name):
            msg = (
                f"Reverse relationship '{related_name}' already exists on "
                f"{to_model.__name__}"
            )
            raise AttributeError(msg)

        # Add reverse relationship descriptor to to_model
        setattr(
            to_model,
            related_name,
            ReverseRelationship(from_model, fk_field, related_name),
        )
