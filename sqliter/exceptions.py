"""Define custom exceptins for the sqliter package."""


class InvalidOffsetError(ValueError):
    """Raised when an invalid offset value (0 or negative) is used."""

    def __init__(self, offset_value: int) -> None:
        super().__init__(
            f"Invalid offset value: {offset_value}. Offset must be a positive integer."
        )
