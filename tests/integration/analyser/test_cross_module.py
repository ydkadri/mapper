"""Integration tests for cross-module dependencies in Neo4j."""

from pathlib import Path

from mapper import analyser, graph_loader


class TestCrossModuleDependencies:
    """Tests for module dependency tracking."""

    def test_depends_on_relationship_created(self, neo4j_connection, tmp_path: Path):
        """Test that DEPENDS_ON relationship is created between modules."""
        # Create module_a that imports module_b
        module_a = tmp_path / "module_a.py"
        module_a.write_text(
            "from test_pkg import module_b\n\ndef func():\n    return module_b.helper()\n"
        )

        module_b = tmp_path / "module_b.py"
        module_b.write_text('def helper():\n    return "help"\n')

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="test_pkg")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        assert result.success is True

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            # Check DEPENDS_ON relationship
            depends_on = session.run(
                """
                MATCH (m1:Module {package: $pkg})-[:DEPENDS_ON]->(m2:Module)
                WHERE m1.name = 'module_a'
                RETURN m2.name as target_module
                """,
                pkg="test_pkg",
            ).data()

            # module_a should depend on test_pkg (from the import statement)
            # Note: depends on test_pkg, not module_b specifically
            assert len(depends_on) == 1
            assert depends_on[0]["target_module"] == "test_pkg"

        loader.clear_package()

    def test_depends_on_deduplication(self, neo4j_connection, tmp_path: Path):
        """Test that multiple imports from same module create only one DEPENDS_ON."""
        # Module with multiple imports from same source
        test_module = tmp_path / "test_module.py"
        test_module.write_text(
            "from typing import Optional, List, Dict\n\ndef func(x: Optional[List[Dict]]):\n    pass\n"
        )

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="test_dedup")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        assert result.success is True

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            # Count DEPENDS_ON relationships to typing
            depends_count = session.run(
                """
                MATCH (m:Module {package: $pkg})-[r:DEPENDS_ON]->(target:Module)
                WHERE target.name = 'typing'
                RETURN count(r) as count
                """,
                pkg="test_dedup",
            ).data()

            # Should be exactly 1 DEPENDS_ON despite 3 imports
            assert depends_count[0]["count"] == 1

        loader.clear_package()

    def test_dependency_chain(self, neo4j_connection, tmp_path: Path):
        """Test A -> B -> C dependency chain."""
        # Create dependency chain
        module_c = tmp_path / "module_c.py"
        module_c.write_text("def validate(data):\n    return data\n")

        module_b = tmp_path / "module_b.py"
        module_b.write_text(
            "from dep_chain import module_c\n\ndef transform(data):\n    return module_c.validate(data)\n"
        )

        module_a = tmp_path / "module_a.py"
        module_a.write_text(
            "from dep_chain import module_b\n\ndef process(data):\n    return module_b.transform(data)\n"
        )

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="dep_chain")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        assert result.success is True

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            # Find all dependencies
            all_deps = session.run(
                """
                MATCH (m1:Module {package: $pkg})-[:DEPENDS_ON]->(m2:Module)
                RETURN m1.name as source, m2.name as target
                ORDER BY source
                """,
                pkg="dep_chain",
            ).data()

            # Each module depends on dep_chain (the package)
            source_modules = {dep["source"] for dep in all_deps}
            assert "module_a" in source_modules
            assert "module_b" in source_modules

        loader.clear_package()

    def test_multiple_modules_same_dependency(self, neo4j_connection, tmp_path: Path):
        """Test that multiple modules can depend on same external package."""
        # Two modules both importing pandas
        module_a = tmp_path / "module_a.py"
        module_a.write_text("import pandas as pd\n\ndef func_a():\n    return pd.DataFrame()\n")

        module_b = tmp_path / "module_b.py"
        module_b.write_text("import pandas as pd\n\ndef func_b():\n    return pd.Series()\n")

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="multi_dep")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        assert result.success is True

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            # Count modules depending on pandas
            pandas_deps = session.run(
                """
                MATCH (m:Module {package: $pkg})-[:DEPENDS_ON]->(target:Module)
                WHERE target.name = 'pandas'
                RETURN count(m) as module_count
                """,
                pkg="multi_dep",
            ).data()

            # Both modules should have DEPENDS_ON to pandas
            assert pandas_deps[0]["module_count"] == 2

        loader.clear_package()

    def test_internal_and_external_dependencies(self, neo4j_connection, tmp_path: Path):
        """Test module with both internal and external dependencies."""
        # Module depending on both internal module and external package
        internal = tmp_path / "internal.py"
        internal.write_text('def helper():\n    return "help"\n')

        mixed = tmp_path / "mixed.py"
        mixed.write_text(
            "from mixed_deps import internal\nimport pandas\n\ndef func():\n    internal.helper()\n    return pandas.DataFrame()\n"
        )

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="mixed_deps")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        assert result.success is True

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            # Get all dependencies for mixed module
            deps = session.run(
                """
                MATCH (m:Module {package: $pkg, name: 'mixed'})-[:DEPENDS_ON]->(target:Module)
                RETURN target.name as dep_name, target.is_external as is_external
                ORDER BY dep_name
                """,
                pkg="mixed_deps",
            ).data()

            dep_names = [d["dep_name"] for d in deps]
            # Should depend on mixed_deps (internal) and pandas (external)
            assert "mixed_deps" in dep_names
            assert "pandas" in dep_names

            # Check external flag
            pandas_dep = next(d for d in deps if d["dep_name"] == "pandas")
            assert pandas_dep["is_external"] is True

        loader.clear_package()

    def test_circular_dependencies(self, neo4j_connection, tmp_path: Path):
        """Test that circular dependencies are handled correctly."""
        # Module A imports B, B imports A (circular)
        module_a = tmp_path / "module_a.py"
        module_a.write_text(
            "from circular import module_b\n\ndef func_a():\n    return module_b.func_b()\n"
        )

        module_b = tmp_path / "module_b.py"
        module_b.write_text('from circular import module_a\n\ndef func_b():\n    return "b"\n')

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="circular")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        # Analysis should succeed even with circular imports
        assert result.success is True

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            # Both modules should have DEPENDS_ON relationships
            deps = session.run(
                """
                MATCH (m:Module {package: $pkg})-[:DEPENDS_ON]->(target:Module)
                RETURN m.name as source, target.name as target
                ORDER BY source
                """,
                pkg="circular",
            ).data()

            # Both modules depend on the circular package
            sources = {d["source"] for d in deps}
            assert "module_a" in sources
            assert "module_b" in sources

        loader.clear_package()
