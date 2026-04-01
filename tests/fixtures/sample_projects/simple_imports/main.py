"""Main module demonstrating various import patterns."""

# Simple import
# Import with alias
import json as js

# From import
from pathlib import Path

# Submodule import

# Multiple imports from same module


# From import with alias


def process_data(data: dict | None) -> Path:
    """Process data and return path."""
    if data:
        result = js.dumps(data)
        return Path(result)
    return Path("default")
