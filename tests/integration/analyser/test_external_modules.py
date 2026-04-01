"""Integration tests for external vs internal module handling in Neo4j."""

from pathlib import Path

from mapper import analyser, graph_loader


class TestExternalModules:
    """Tests for distinguishing external and internal modules."""

    def test_external_module_flag(self, neo4j_connection, tmp_path: Path):
        """Test that external modules are marked with is_external=True."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text(
            """
import pandas
import numpy

def analyze():
    \"\"\"Analyze function.\"\"\"
    pass
"""
        )

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="test_external")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        assert result.success is True

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            # Check external modules
            external_modules = session.run(
                """
                MATCH (m:Module)
                WHERE m.is_external = true AND m.name IN ['pandas', 'numpy']
                RETURN m.name as name, elementId(m) as id
                ORDER BY name
                """,
            ).data()

            assert len(external_modules) == 2, (
                f"Expected 2 external modules, found {len(external_modules)}: {external_modules}"
            )
            assert external_modules[0]["name"] == "numpy"
            assert external_modules[1]["name"] == "pandas"

        loader.clear_package()

    def test_internal_module_no_external_flag(self, neo4j_connection, tmp_path: Path):
        """Test that internal modules don't have is_external flag set."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text(
            """
def internal_function():
    \"\"\"Internal function.\"\"\"
    pass
"""
        )

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="test_internal")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        assert result.success is True

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            # Check internal module doesn't have is_external
            internal_modules = session.run(
                """
                MATCH (m:Module {package: $pkg})
                RETURN m.name as name, m.is_external as is_external
                """,
                pkg="test_internal",
            ).data()

            assert len(internal_modules) == 1
            # is_external should be None or False for internal modules
            assert internal_modules[0]["is_external"] in (None, False)

        loader.clear_package()

    def test_mixed_internal_external(self, neo4j_connection, tmp_path: Path):
        """Test project with both internal and external dependencies."""
        # Internal module
        internal_mod = tmp_path / "internal.py"
        internal_mod.write_text(
            """
def helper():
    \"\"\"Helper function.\"\"\"
    return "help"
"""
        )

        # Module importing both internal and external
        mixed_mod = tmp_path / "mixed.py"
        mixed_mod.write_text(
            """
from test_mixed import internal
import pandas

def process():
    \"\"\"Process function.\"\"\"
    result = internal.helper()
    df = pandas.DataFrame([result])
    return df
"""
        )

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="test_mixed")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        assert result.success is True

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            # Check internal modules (part of test_mixed package)
            internal_modules = session.run(
                """
                MATCH (m:Module {package: $pkg})
                WHERE m.is_external IS NULL OR m.is_external = false
                RETURN m.name as name
                ORDER BY name
                """,
                pkg="test_mixed",
            ).data()

            internal_names = [m["name"] for m in internal_modules]
            assert "internal" in internal_names
            assert "mixed" in internal_names

            # Check external modules
            external_modules = session.run(
                """
                MATCH (m:Module)
                WHERE m.is_external = true AND (m.name = 'pandas' OR m.name = 'test_mixed')
                RETURN m.name as name
                ORDER BY name
                """,
            ).data()

            # pandas should be external, test_mixed may appear as external ref
            external_names = [m["name"] for m in external_modules]
            assert "pandas" in external_names

        loader.clear_package()

    def test_stdlib_modules_external(self, neo4j_connection, tmp_path: Path):
        """Test that standard library modules are marked as external."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text(
            """
import os
import json
from pathlib import Path

def process(path: Path):
    \"\"\"Process function.\"\"\"
    if os.path.exists(str(path)):
        with open(path) as f:
            return json.load(f)
"""
        )

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="test_stdlib")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        assert result.success is True

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            # Check stdlib modules are external
            stdlib_modules = session.run(
                """
                MATCH (m:Module)
                WHERE m.is_external = true AND m.name IN ['os', 'json', 'pathlib']
                RETURN m.name as name
                ORDER BY name
                """,
            ).data()

            stdlib_names = [m["name"] for m in stdlib_modules]
            assert "json" in stdlib_names
            assert "os" in stdlib_names
            assert "pathlib" in stdlib_names

        loader.clear_package()

    def test_external_module_properties(self, neo4j_connection, tmp_path: Path):
        """Test that external modules have correct properties."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text(
            """
import requests

def fetch():
    \"\"\"Fetch function.\"\"\"
    return requests.get("https://example.com")
"""
        )

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="test_props")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        assert result.success is True

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            # Check external module properties
            external_props = session.run(
                """
                MATCH (m:Module)
                WHERE m.name = 'requests' AND m.is_external = true
                RETURN m.name as name, m.package as package, m.is_external as is_external
                """,
            ).data()

            assert len(external_props) == 1
            assert external_props[0]["name"] == "requests"
            assert external_props[0]["package"] == "requests"  # Package same as name for external
            assert external_props[0]["is_external"] is True

        loader.clear_package()

    def test_from_module_to_external(self, neo4j_connection, tmp_path: Path):
        """Test FROM_MODULE relationships point to external modules correctly."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text(
            """
from typing import List, Optional

def process(items: List[Optional[str]]):
    \"\"\"Process function.\"\"\"
    return [x for x in items if x]
"""
        )

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="test_from_ext")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        assert result.success is True

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            # Check FROM_MODULE relationships
            from_module_rels = session.run(
                """
                MATCH (i:Import {package: $pkg})-[:FROM_MODULE]->(m:Module)
                RETURN i.local_name as import_name, m.name as module_name, m.is_external as is_external
                ORDER BY import_name
                """,
                pkg="test_from_ext",
            ).data()

            assert len(from_module_rels) == 2

            # Both should point to external typing module
            for rel in from_module_rels:
                assert rel["module_name"] == "typing"
                assert rel["is_external"] is True

        loader.clear_package()

    def test_depends_on_external_modules(self, neo4j_connection, tmp_path: Path):
        """Test DEPENDS_ON relationships to external modules."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text(
            """
import numpy as np
import pandas as pd

def analyze(data):
    \"\"\"Analyze function.\"\"\"
    array = np.array(data)
    df = pd.DataFrame(array)
    return df
"""
        )

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="test_dep_ext")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        assert result.success is True

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            # Check DEPENDS_ON to external modules
            depends_on = session.run(
                """
                MATCH (m:Module {package: $pkg})-[:DEPENDS_ON]->(ext:Module)
                WHERE ext.is_external = true
                RETURN ext.name as external_module
                ORDER BY external_module
                """,
                pkg="test_dep_ext",
            ).data()

            external_deps = [d["external_module"] for d in depends_on]
            assert "numpy" in external_deps
            assert "pandas" in external_deps

        loader.clear_package()
