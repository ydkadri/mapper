"""Built-in risk detection queries."""

from mapper.query_system.queries import critical_functions, dead_code, module_centrality

# All built-in queries
BUILTIN_QUERIES = [
    dead_code.QUERY,
    module_centrality.QUERY,
    critical_functions.QUERY,
]

__all__ = ["BUILTIN_QUERIES", "dead_code", "module_centrality", "critical_functions"]
