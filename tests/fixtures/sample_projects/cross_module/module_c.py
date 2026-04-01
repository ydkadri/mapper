"""Module C - leaf module, only imports external packages."""


def validate(data: list) -> list:
    """Validate data."""
    return [x for x in data if x is not None]


def check(value):
    """Check value."""
    return value is not None
