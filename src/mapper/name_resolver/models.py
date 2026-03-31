"""Data models for name resolution."""

from enum import Enum

import attrs


class ResolutionFailureReason(str, Enum):  # noqa: UP042 - str,Enum for Python 3.10 compatibility
    """Reasons why name resolution can fail."""

    NOT_IN_IMPORTS = "not found in imports"
    EXTERNAL_PACKAGE = "external package"
    DYNAMIC_IMPORT = "dynamic import"
    BUILTIN = "builtin name"
    UNDEFINED = "undefined"


@attrs.define(frozen=True)
class UnresolvedName:
    """Represents a name that could not be resolved to an FQN.

    This typically indicates:
    - External package not in imports
    - Dynamic imports
    - Runtime-defined names
    - Errors in code being analyzed
    """

    original_name: str  # Name as it appears in code
    context: str | None = None  # Where this name was found (function FQN, class FQN, etc.)
    reason: ResolutionFailureReason | None = None  # Why resolution failed

    def __str__(self) -> str:
        """String representation for logging/display."""
        parts = [f"'{self.original_name}'"]
        if self.context:
            parts.append(f"in {self.context}")
        if self.reason:
            parts.append(f"({self.reason})")
        return " ".join(parts)
