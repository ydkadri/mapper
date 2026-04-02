"""Query group enumeration."""

import enum


class QueryGroup(str, enum.Enum):
    """Query group with CLI identifier and display name.

    The enum value is the CLI identifier (used for --group filtering).
    The display_name property provides the human-readable name.

    Example:
        group = QueryGroup.RISK
        cli_name = group.value  # "risk"
        display = group.display_name  # "Risk Detection"
    """

    RISK = "risk"
    CRITICAL = "critical"

    @property
    def display_name(self) -> str:
        """Get human-readable display name for this group.

        Returns:
            Display name for the group
        """
        display_names = {
            QueryGroup.RISK: "Risk Detection",
            QueryGroup.CRITICAL: "Critical Components",
        }
        return display_names[self]
