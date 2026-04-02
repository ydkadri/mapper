"""Query system for risk detection and code analysis.

This module provides:
- Built-in risk detection queries
- Query execution against Neo4j
- Multiple output formats (table, JSON, CSV)
- Query registry for managing queries
"""

from mapper.query_system import executor, formatters, registry
from mapper.query_system.query import Severity

__all__ = ["registry", "executor", "formatters", "Severity"]
