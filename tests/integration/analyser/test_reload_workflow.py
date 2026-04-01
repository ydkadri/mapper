"""Integration tests for clear and reload workflows in Neo4j."""

from pathlib import Path

from mapper import analyser, graph_loader


class TestReloadWorkflow:
    """Tests for clearing and re-analyzing packages."""

    def test_clear_package_removes_all_nodes(self, neo4j_connection, tmp_path: Path):
        """Test that clear_package removes all nodes for that package."""
        # Create and analyze initial code
        test_file = tmp_path / "test_module.py"
        test_file.write_text(
            """
class MyClass:
    \"\"\"Test class.\"\"\"
    def my_method(self):
        \"\"\"Test method.\"\"\"
        pass

def my_function():
    \"\"\"Test function.\"\"\"
    pass
"""
        )

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="test_clear")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        assert result.success is True
        initial_count = result.nodes_created
        assert initial_count > 0

        # Verify nodes exist
        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            node_count = session.run(
                """
                MATCH (n {package: $pkg})
                RETURN count(n) as count
                """,
                pkg="test_clear",
            ).single()["count"]

            assert node_count == initial_count

        # Clear package
        deleted_count = loader.clear_package()
        assert deleted_count == initial_count

        # Verify all nodes removed
        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            node_count = session.run(
                """
                MATCH (n {package: $pkg})
                RETURN count(n) as count
                """,
                pkg="test_clear",
            ).single()["count"]

            assert node_count == 0

    def test_reload_after_code_change(self, neo4j_connection, tmp_path: Path):
        """Test re-analyzing after code changes updates the graph correctly."""
        test_file = tmp_path / "test_module.py"

        # Initial version
        test_file.write_text(
            """
def old_function():
    \"\"\"Old function.\"\"\"
    pass
"""
        )

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="test_reload")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result1 = code_analyser.analyse()

        assert result1.success is True

        # Verify old function exists
        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            functions = session.run(
                """
                MATCH (f:Function {package: $pkg})
                RETURN f.name as name
                """,
                pkg="test_reload",
            ).data()

            assert len(functions) == 1
            assert functions[0]["name"] == "old_function"

        # Update code
        test_file.write_text(
            """
def new_function():
    \"\"\"New function.\"\"\"
    pass

def another_function():
    \"\"\"Another function.\"\"\"
    pass
"""
        )

        # Clear and re-analyze
        loader.clear_package()
        result2 = code_analyser.analyse()

        assert result2.success is True

        # Verify new functions exist, old one gone
        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            functions = session.run(
                """
                MATCH (f:Function {package: $pkg})
                RETURN f.name as name
                ORDER BY name
                """,
                pkg="test_reload",
            ).data()

            assert len(functions) == 2
            assert functions[0]["name"] == "another_function"
            assert functions[1]["name"] == "new_function"
            # old_function should not exist
            assert not any(f["name"] == "old_function" for f in functions)

        loader.clear_package()

    def test_reload_with_relationships_updates_correctly(self, neo4j_connection, tmp_path: Path):
        """Test that relationships are correctly updated after reload."""
        test_file = tmp_path / "test_module.py"

        # Initial version with function call
        test_file.write_text(
            """
def caller():
    \"\"\"Caller function.\"\"\"
    return target_v1()

def target_v1():
    \"\"\"Target function version 1.\"\"\"
    return "v1"
"""
        )

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="test_rel_reload")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result1 = code_analyser.analyse()

        assert result1.success is True

        # Verify initial relationship
        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            calls = session.run(
                """
                MATCH (caller:Function {package: $pkg})-[:CALLS]->(target:Function)
                WHERE caller.name = 'caller'
                RETURN target.name as target_name
                """,
                pkg="test_rel_reload",
            ).data()

            assert len(calls) == 1
            assert calls[0]["target_name"] == "target_v1"

        # Update code - caller now calls different function
        test_file.write_text(
            """
def caller():
    \"\"\"Caller function.\"\"\"
    return target_v2()

def target_v2():
    \"\"\"Target function version 2.\"\"\"
    return "v2"
"""
        )

        # Clear and re-analyze
        loader.clear_package()
        result2 = code_analyser.analyse()

        assert result2.success is True

        # Verify relationship updated
        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            calls = session.run(
                """
                MATCH (caller:Function {package: $pkg})-[:CALLS]->(target:Function)
                WHERE caller.name = 'caller'
                RETURN target.name as target_name
                """,
                pkg="test_rel_reload",
            ).data()

            assert len(calls) == 1
            assert calls[0]["target_name"] == "target_v2"
            # Old target should not exist
            assert not any(c["target_name"] == "target_v1" for c in calls)

        loader.clear_package()

    def test_reload_multiple_files(self, neo4j_connection, tmp_path: Path):
        """Test reloading project with multiple files."""
        # Create initial files
        file1 = tmp_path / "module1.py"
        file1.write_text('def func1():\n    """Function 1."""\n    pass\n')

        file2 = tmp_path / "module2.py"
        file2.write_text('def func2():\n    """Function 2."""\n    pass\n')

        # Initial analysis
        loader = graph_loader.GraphLoader(neo4j_connection, package_name="test_multi_reload")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result1 = code_analyser.analyse()

        assert result1.success is True
        assert result1.modules_count == 2

        # Update one file, add a new file
        file1.write_text('def func1_updated():\n    """Updated function."""\n    pass\n')

        file3 = tmp_path / "module3.py"
        file3.write_text('def func3():\n    """Function 3."""\n    pass\n')

        # Clear and re-analyze
        loader.clear_package()
        result2 = code_analyser.analyse()

        assert result2.success is True
        assert result2.modules_count == 3  # Now 3 modules

        # Verify correct functions exist
        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            functions = session.run(
                """
                MATCH (f:Function {package: $pkg})
                RETURN f.name as name
                ORDER BY name
                """,
                pkg="test_multi_reload",
            ).data()

            assert len(functions) == 3
            assert functions[0]["name"] == "func1_updated"
            assert functions[1]["name"] == "func2"
            assert functions[2]["name"] == "func3"

        loader.clear_package()

    def test_clear_doesnt_affect_other_packages(self, neo4j_connection, tmp_path: Path):
        """Test that clearing one package doesn't affect other packages."""
        # Create two separate package directories
        pkg1_dir = tmp_path / "package1"
        pkg1_dir.mkdir()
        pkg1_file = pkg1_dir / "module.py"
        pkg1_file.write_text('def pkg1_func():\n    """Package 1 function."""\n    pass\n')

        pkg2_dir = tmp_path / "package2"
        pkg2_dir.mkdir()
        pkg2_file = pkg2_dir / "module.py"
        pkg2_file.write_text('def pkg2_func():\n    """Package 2 function."""\n    pass\n')

        # Analyze both packages
        loader1 = graph_loader.GraphLoader(neo4j_connection, package_name="package1")
        loader1.clear_package()
        analyser1 = analyser.Analyser(pkg1_dir, loader=loader1)
        result1 = analyser1.analyse()

        loader2 = graph_loader.GraphLoader(neo4j_connection, package_name="package2")
        loader2.clear_package()
        analyser2 = analyser.Analyser(pkg2_dir, loader=loader2)
        result2 = analyser2.analyse()

        assert result1.success is True
        assert result2.success is True

        # Clear only package1
        deleted = loader1.clear_package()
        assert deleted > 0

        # Verify package1 nodes gone
        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            pkg1_count = session.run(
                """
                MATCH (n {package: $pkg})
                RETURN count(n) as count
                """,
                pkg="package1",
            ).single()["count"]

            assert pkg1_count == 0

            # Verify package2 nodes still exist
            pkg2_count = session.run(
                """
                MATCH (n {package: $pkg})
                RETURN count(n) as count
                """,
                pkg="package2",
            ).single()["count"]

            assert pkg2_count > 0

        # Cleanup
        loader2.clear_package()

    def test_reload_after_adding_imports(self, neo4j_connection, tmp_path: Path):
        """Test reloading after adding import statements."""
        test_file = tmp_path / "test_module.py"

        # Initial version without imports
        test_file.write_text(
            """
def process():
    \"\"\"Process function.\"\"\"
    return "result"
"""
        )

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="test_import_reload")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result1 = code_analyser.analyse()

        assert result1.success is True

        # Verify no imports
        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            import_count = session.run(
                """
                MATCH (i:Import {package: $pkg})
                RETURN count(i) as count
                """,
                pkg="test_import_reload",
            ).single()["count"]

            assert import_count == 0

        # Update code with imports
        test_file.write_text(
            """
import pandas as pd
from typing import Optional

def process(data: Optional[dict]):
    \"\"\"Process function.\"\"\"
    df = pd.DataFrame(data)
    return df
"""
        )

        # Clear and re-analyze
        loader.clear_package()
        result2 = code_analyser.analyse()

        assert result2.success is True

        # Verify imports now exist
        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            import_count = session.run(
                """
                MATCH (i:Import {package: $pkg})
                RETURN count(i) as count
                """,
                pkg="test_import_reload",
            ).single()["count"]

            assert import_count == 2  # pandas and Optional

        loader.clear_package()
