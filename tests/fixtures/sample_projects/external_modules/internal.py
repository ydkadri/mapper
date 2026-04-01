"""Internal module - imports from within project."""

from external_modules import utils


def process():
    """Process using internal utility."""
    return utils.helper()


def transform(data):
    """Transform data."""
    return utils.validate(data)
