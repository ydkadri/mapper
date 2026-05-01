"""Utilities for parsing and handling type annotations."""

import ast


def parse_type_annotation(node: ast.expr) -> str:
    """Parse a type annotation AST node into a string representation.

    Handles:
    - Simple types: str, int, CustomClass
    - Generic types: list[int], dict[str, Any]
    - Union types: str | None, int | str
    - Optional types: Optional[str]

    Args:
        node: AST expression node representing a type annotation

    Returns:
        String representation of the type

    Examples:
        >>> # ast.Name(id='str') -> 'str'
        >>> # ast.Subscript(value=Name('list'), slice=Name('int')) -> 'list[int]'
        >>> # ast.BinOp(left=Name('str'), op=BitOr(), right=Name('None')) -> 'str | None'
    """
    # Simple name: str, int, CustomClass
    if isinstance(node, ast.Name):
        return node.id

    # Subscripted generic: list[T], dict[K, V], Optional[T]
    elif isinstance(node, ast.Subscript):
        base = parse_type_annotation(node.value)

        # Handle single subscript: list[int], Optional[str]
        if isinstance(node.slice, ast.Name):
            arg = node.slice.id
            return f"{base}[{arg}]"

        # Handle multiple subscripts: dict[str, int]
        elif isinstance(node.slice, ast.Tuple):
            args = [parse_type_annotation(elt) for elt in node.slice.elts]
            return f"{base}[{', '.join(args)}]"

        # Recursively handle complex subscripts
        else:
            arg = parse_type_annotation(node.slice)
            return f"{base}[{arg}]"

    # Union type with | operator: str | None, int | str | None
    elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        left = parse_type_annotation(node.left)
        right = parse_type_annotation(node.right)
        return f"{left} | {right}"

    # Constant (edge case - might appear in some type contexts)
    elif isinstance(node, ast.Constant):
        return str(node.value)

    # Unknown or unsupported type annotation
    return "Unknown"
