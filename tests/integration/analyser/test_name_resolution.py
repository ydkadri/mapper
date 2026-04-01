"""Integration tests for name resolution creating correct relationships in Neo4j."""

from pathlib import Path

from mapper import analyser, graph_loader


class TestNameResolution:
    """Tests for name resolution leading to correct graph relationships."""

    def test_function_calls_resolved(self, neo4j_connection, tmp_path: Path):
        """Test that function calls create CALLS relationships with resolved FQNs."""
        # Module with functions calling each other
        test_module = tmp_path / "test_module.py"
        test_module.write_text(
            """
def caller():
    \"\"\"Caller function.\"\"\"
    return callee()

def callee():
    \"\"\"Callee function.\"\"\"
    return "result"
"""
        )

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="test_calls")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        assert result.success is True

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            # Check CALLS relationship
            calls = session.run(
                """
                MATCH (caller:Function {package: $pkg})-[:CALLS]->(callee:Function)
                WHERE caller.name = 'caller' AND callee.name = 'callee'
                RETURN caller.fqn as caller_fqn, callee.fqn as callee_fqn
                """,
                pkg="test_calls",
            ).data()

            assert len(calls) == 1
            assert calls[0]["caller_fqn"] == "test_module.caller"
            assert calls[0]["callee_fqn"] == "test_module.callee"

        loader.clear_package()

    def test_method_calls_in_class(self, neo4j_connection, tmp_path: Path):
        """Test that method calls within class create correct relationships."""
        test_module = tmp_path / "test_module.py"
        test_module.write_text(
            """
class MyClass:
    \"\"\"Test class.\"\"\"

    def method_a(self):
        \"\"\"Method A.\"\"\"
        return self.method_b()

    def method_b(self):
        \"\"\"Method B.\"\"\"
        return "result"
"""
        )

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="test_methods")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        assert result.success is True

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            # Check method call relationship
            calls = session.run(
                """
                MATCH (method_a:Method {package: $pkg})-[:CALLS]->(method_b:Method)
                WHERE method_a.name = 'method_a' AND method_b.name = 'method_b'
                RETURN method_a.fqn as caller_fqn, method_b.fqn as callee_fqn
                """,
                pkg="test_methods",
            ).data()

            assert len(calls) == 1
            assert calls[0]["caller_fqn"] == "test_module.MyClass.method_a"
            assert calls[0]["callee_fqn"] == "test_module.MyClass.method_b"

        loader.clear_package()

    def test_cross_module_function_calls(self, neo4j_connection, tmp_path: Path):
        """Test that function calls across modules resolve correctly."""
        # Module A defines function
        module_a = tmp_path / "module_a.py"
        module_a.write_text(
            'def target_function():\n    """Target function."""\n    return "result"\n'
        )

        # Module B imports and calls it
        module_b = tmp_path / "module_b.py"
        module_b.write_text(
            'from cross_call import module_a\n\ndef caller():\n    """Caller."""\n    return module_a.target_function()\n'
        )

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="cross_call")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        assert result.success is True

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            # Check cross-module CALLS relationship
            calls = session.run(
                """
                MATCH (caller:Function {package: $pkg})-[:CALLS]->(target:Function)
                WHERE caller.name = 'caller' AND target.name = 'target_function'
                RETURN caller.fqn as caller_fqn, target.fqn as target_fqn
                """,
                pkg="cross_call",
            ).data()

            assert len(calls) == 1
            assert calls[0]["caller_fqn"] == "module_b.caller"
            assert calls[0]["target_fqn"] == "module_a.target_function"

        loader.clear_package()

    def test_inheritance_resolved(self, neo4j_connection, tmp_path: Path):
        """Test that class inheritance creates INHERITS relationships."""
        # Module with inheritance
        test_module = tmp_path / "test_module.py"
        test_module.write_text(
            """
class BaseClass:
    \"\"\"Base class.\"\"\"
    pass

class DerivedClass(BaseClass):
    \"\"\"Derived class.\"\"\"
    pass
"""
        )

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="test_inherit")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        assert result.success is True

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            # Check INHERITS relationship
            inherits = session.run(
                """
                MATCH (derived:Class {package: $pkg})-[:INHERITS]->(base:Class)
                WHERE derived.name = 'DerivedClass' AND base.name = 'BaseClass'
                RETURN derived.fqn as derived_fqn, base.fqn as base_fqn
                """,
                pkg="test_inherit",
            ).data()

            assert len(inherits) == 1
            assert inherits[0]["derived_fqn"] == "test_module.DerivedClass"
            assert inherits[0]["base_fqn"] == "test_module.BaseClass"

        loader.clear_package()

    def test_cross_module_inheritance(self, neo4j_connection, tmp_path: Path):
        """Test that inheritance across modules resolves correctly."""
        # Module with base class
        base_module = tmp_path / "base_module.py"
        base_module.write_text('class Animal:\n    """Animal base class."""\n    pass\n')

        # Module with derived class
        derived_module = tmp_path / "derived_module.py"
        derived_module.write_text(
            'from cross_inherit.base_module import Animal\n\nclass Dog(Animal):\n    """Dog class."""\n    pass\n'
        )

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="cross_inherit")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        assert result.success is True

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            # Check cross-module INHERITS relationship
            inherits = session.run(
                """
                MATCH (derived:Class {package: $pkg})-[:INHERITS]->(base:Class)
                WHERE derived.name = 'Dog' AND base.name = 'Animal'
                RETURN derived.fqn as derived_fqn, base.fqn as base_fqn
                """,
                pkg="cross_inherit",
            ).data()

            assert len(inherits) == 1
            assert inherits[0]["derived_fqn"] == "derived_module.Dog"
            assert inherits[0]["base_fqn"] == "base_module.Animal"

        loader.clear_package()

    def test_aliased_import_calls(self, neo4j_connection, tmp_path: Path):
        """Test that calls using aliased imports resolve correctly."""
        # Module A with function
        module_a = tmp_path / "module_a.py"
        module_a.write_text('def utility():\n    """Utility function."""\n    return "util"\n')

        # Module B imports with alias and calls
        module_b = tmp_path / "module_b.py"
        module_b.write_text(
            'from alias_test import module_a as ma\n\ndef caller():\n    """Caller."""\n    return ma.utility()\n'
        )

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="alias_test")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        assert result.success is True

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            # Check that call resolves despite alias
            calls = session.run(
                """
                MATCH (caller:Function {package: $pkg})-[:CALLS]->(target:Function)
                WHERE caller.name = 'caller' AND target.name = 'utility'
                RETURN caller.fqn as caller_fqn, target.fqn as target_fqn
                """,
                pkg="alias_test",
            ).data()

            assert len(calls) == 1
            assert calls[0]["caller_fqn"] == "module_b.caller"
            assert calls[0]["target_fqn"] == "module_a.utility"

        loader.clear_package()

    def test_chained_function_calls(self, neo4j_connection, tmp_path: Path):
        """Test that chained function calls all create relationships."""
        test_module = tmp_path / "test_module.py"
        test_module.write_text(
            """
def func_a():
    \"\"\"Function A.\"\"\"
    return func_b()

def func_b():
    \"\"\"Function B.\"\"\"
    return func_c()

def func_c():
    \"\"\"Function C.\"\"\"
    return "result"
"""
        )

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="test_chain")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        assert result.success is True

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            # Check all CALLS relationships exist
            calls = session.run(
                """
                MATCH (caller:Function {package: $pkg})-[:CALLS]->(callee:Function)
                RETURN caller.name as caller, callee.name as callee
                ORDER BY caller
                """,
                pkg="test_chain",
            ).data()

            assert len(calls) == 2
            assert calls[0]["caller"] == "func_a"
            assert calls[0]["callee"] == "func_b"
            assert calls[1]["caller"] == "func_b"
            assert calls[1]["callee"] == "func_c"

        loader.clear_package()
