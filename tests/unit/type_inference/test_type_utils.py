"""Tests for type annotation parsing utilities."""

import ast
import textwrap

from mapper.type_inference import type_utils


class TestParseTypeAnnotation:
    """Tests for parse_type_annotation function."""

    def test_simple_builtin_types(self):
        """Test parsing simple built-in type names."""
        # str
        code = "x: str"
        tree = ast.parse(code)
        ann_node = tree.body[0].annotation
        assert type_utils.parse_type_annotation(ann_node) == "str"

        # int
        code = "x: int"
        tree = ast.parse(code)
        ann_node = tree.body[0].annotation
        assert type_utils.parse_type_annotation(ann_node) == "int"

        # bool
        code = "x: bool"
        tree = ast.parse(code)
        ann_node = tree.body[0].annotation
        assert type_utils.parse_type_annotation(ann_node) == "bool"

    def test_custom_class_types(self):
        """Test parsing custom class names."""
        code = "x: CustomClass"
        tree = ast.parse(code)
        ann_node = tree.body[0].annotation
        assert type_utils.parse_type_annotation(ann_node) == "CustomClass"

    def test_list_with_single_type(self):
        """Test parsing list[T] generic types."""
        # list[int]
        code = "x: list[int]"
        tree = ast.parse(code)
        ann_node = tree.body[0].annotation
        assert type_utils.parse_type_annotation(ann_node) == "list[int]"

        # list[str]
        code = "x: list[str]"
        tree = ast.parse(code)
        ann_node = tree.body[0].annotation
        assert type_utils.parse_type_annotation(ann_node) == "list[str]"

        # list[CustomClass]
        code = "x: list[CustomClass]"
        tree = ast.parse(code)
        ann_node = tree.body[0].annotation
        assert type_utils.parse_type_annotation(ann_node) == "list[CustomClass]"

    def test_dict_with_two_types(self):
        """Test parsing dict[K, V] generic types."""
        # dict[str, int]
        code = "x: dict[str, int]"
        tree = ast.parse(code)
        ann_node = tree.body[0].annotation
        assert type_utils.parse_type_annotation(ann_node) == "dict[str, int]"

        # dict[str, Any]
        code = "x: dict[str, Any]"
        tree = ast.parse(code)
        ann_node = tree.body[0].annotation
        assert type_utils.parse_type_annotation(ann_node) == "dict[str, Any]"

        # dict[int, CustomClass]
        code = "x: dict[int, CustomClass]"
        tree = ast.parse(code)
        ann_node = tree.body[0].annotation
        assert type_utils.parse_type_annotation(ann_node) == "dict[int, CustomClass]"

    def test_optional_type(self):
        """Test parsing Optional[T] types."""
        # Optional[str]
        code = "x: Optional[str]"
        tree = ast.parse(code)
        ann_node = tree.body[0].annotation
        assert type_utils.parse_type_annotation(ann_node) == "Optional[str]"

        # Optional[int]
        code = "x: Optional[int]"
        tree = ast.parse(code)
        ann_node = tree.body[0].annotation
        assert type_utils.parse_type_annotation(ann_node) == "Optional[int]"

        # Optional[CustomClass]
        code = "x: Optional[CustomClass]"
        tree = ast.parse(code)
        ann_node = tree.body[0].annotation
        assert type_utils.parse_type_annotation(ann_node) == "Optional[CustomClass]"

    def test_union_type_with_none(self):
        """Test parsing X | None union types."""
        # str | None
        code = "x: str | None"
        tree = ast.parse(code)
        ann_node = tree.body[0].annotation
        assert type_utils.parse_type_annotation(ann_node) == "str | None"

        # int | None
        code = "x: int | None"
        tree = ast.parse(code)
        ann_node = tree.body[0].annotation
        assert type_utils.parse_type_annotation(ann_node) == "int | None"

        # CustomClass | None
        code = "x: CustomClass | None"
        tree = ast.parse(code)
        ann_node = tree.body[0].annotation
        assert type_utils.parse_type_annotation(ann_node) == "CustomClass | None"

    def test_union_type_multiple(self):
        """Test parsing multi-type unions."""
        # int | str
        code = "x: int | str"
        tree = ast.parse(code)
        ann_node = tree.body[0].annotation
        assert type_utils.parse_type_annotation(ann_node) == "int | str"

        # int | str | None (chained unions parse left-to-right)
        code = "x: int | str | None"
        tree = ast.parse(code)
        ann_node = tree.body[0].annotation
        # Union is left-associative: (int | str) | None
        result = type_utils.parse_type_annotation(ann_node)
        assert result == "int | str | None"

    def test_set_type(self):
        """Test parsing set[T] generic types."""
        code = "x: set[int]"
        tree = ast.parse(code)
        ann_node = tree.body[0].annotation
        assert type_utils.parse_type_annotation(ann_node) == "set[int]"

    def test_tuple_type(self):
        """Test parsing tuple[T, ...] generic types."""
        # tuple[int, str]
        code = "x: tuple[int, str]"
        tree = ast.parse(code)
        ann_node = tree.body[0].annotation
        assert type_utils.parse_type_annotation(ann_node) == "tuple[int, str]"

    def test_nested_generic_list_of_dicts(self):
        """Test parsing nested generics like list[dict[str, int]]."""
        code = "x: list[dict[str, int]]"
        tree = ast.parse(code)
        ann_node = tree.body[0].annotation
        assert type_utils.parse_type_annotation(ann_node) == "list[dict[str, int]]"

    def test_nested_generic_dict_of_lists(self):
        """Test parsing nested generics like dict[str, list[int]]."""
        code = "x: dict[str, list[int]]"
        tree = ast.parse(code)
        ann_node = tree.body[0].annotation
        assert type_utils.parse_type_annotation(ann_node) == "dict[str, list[int]]"

    def test_union_of_generics(self):
        """Test parsing unions of generic types."""
        code = "x: list[int] | None"
        tree = ast.parse(code)
        ann_node = tree.body[0].annotation
        assert type_utils.parse_type_annotation(ann_node) == "list[int] | None"

    def test_typing_module_List(self):
        """Test parsing typing.List (capital L) which is ast.Name."""
        # Note: List[int] from typing module is parsed as:
        # Subscript(value=Name('List'), slice=Name('int'))
        # Our function handles this the same as list[int]
        code = "x: List[int]"
        tree = ast.parse(code)
        ann_node = tree.body[0].annotation
        assert type_utils.parse_type_annotation(ann_node) == "List[int]"

    def test_typing_module_Dict(self):
        """Test parsing typing.Dict (capital D)."""
        code = "x: Dict[str, int]"
        tree = ast.parse(code)
        ann_node = tree.body[0].annotation
        assert type_utils.parse_type_annotation(ann_node) == "Dict[str, int]"

    def test_constant_annotation(self):
        """Test parsing constant annotations (edge case)."""
        # This is an edge case - constants can appear in some type contexts
        # Our function should handle it gracefully
        node = ast.Constant(value="SomeType")
        assert type_utils.parse_type_annotation(node) == "SomeType"

    def test_unknown_node_type(self):
        """Test that unknown AST nodes return 'Unknown'."""
        # Pass an unsupported AST node type
        node = ast.Pass()  # Not a valid type annotation node
        assert type_utils.parse_type_annotation(node) == "Unknown"

    def test_function_return_type_annotation(self):
        """Test parsing return type from function definition."""
        code = textwrap.dedent("""
            def process_data() -> dict[str, list[int]]:
                pass
        """)
        tree = ast.parse(code)
        func_node = tree.body[0]
        return_annotation = func_node.returns
        assert type_utils.parse_type_annotation(return_annotation) == "dict[str, list[int]]"

    def test_parameter_type_annotation(self):
        """Test parsing parameter type annotation."""
        code = textwrap.dedent("""
            def process(data: list[str]) -> None:
                pass
        """)
        tree = ast.parse(code)
        func_node = tree.body[0]
        param_annotation = func_node.args.args[0].annotation
        assert type_utils.parse_type_annotation(param_annotation) == "list[str]"
