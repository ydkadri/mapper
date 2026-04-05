"""Quality rule registry."""

from typing import Optional

from mapper.quality import models
from mapper.quality.rules import docstring_coverage, param_complexity, type_coverage


# Registry of all built-in quality rules
_RULES: dict[str, models.QualityRule] = {
    "type_coverage": type_coverage.TypeCoverageRule(),
    "docstring_coverage": docstring_coverage.DocstringCoverageRule(),
    "param_complexity": param_complexity.ParamComplexityRule(),
}


def get_rule(name: str) -> Optional[models.QualityRule]:
    """Get quality rule by name.

    Args:
        name: Machine-readable rule name (e.g., 'type_coverage')

    Returns:
        QualityRule instance or None if not found
    """
    return _RULES.get(name)


def get_all_rules() -> list[models.QualityRule]:
    """Get all registered quality rules.

    Returns:
        List of all QualityRule instances
    """
    return list(_RULES.values())


def get_rule_names() -> list[str]:
    """Get names of all registered quality rules.

    Returns:
        List of rule names
    """
    return list(_RULES.keys())
