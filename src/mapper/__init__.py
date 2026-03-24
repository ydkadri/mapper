"""Mapper (Application Mapper) - AST-based Python code analyzer."""

# Public modules
from mapper import (
    analyser,
    ast_parser,
    config_manager,
    graph,
    graph_loader,
    parser,
    status_checker,
    type_inference,
)

# Public classes from modules
from mapper.graph import Neo4jConnection
from mapper.graph_loader import GraphLoader
from mapper.parser import ASTParser

__version__ = "0.5.0"

__all__ = [
    # Version
    "__version__",
    # Modules
    "analyser",
    "ast_parser",
    "config_manager",
    "graph",
    "graph_loader",
    "parser",
    "status_checker",
    "type_inference",
    # Classes
    "ASTParser",
    "GraphLoader",
    "Neo4jConnection",
]
