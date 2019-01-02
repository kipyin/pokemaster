class ItemUsageError(Exception):
    """Illegal usage of an item."""


class MaxStatExceededError(ValueError):
    """Stat exceeds maximum allowance."""
