"""Integration tests for import tracking in Neo4j."""

from pathlib import Path

from mapper import analyser, graph_loader


class TestImportTracking:
    """Tests for import pattern tracking end-to-end."""

    def test_simple_import(self, neo4j_connection, tmp_path: Path):
        """Test that simple 'import os' creates correct Import node."""
        # Create test file
        test_file = tmp_path / "test_module.py"
        test_file.write_text('import os\n\ndef func():\n    return os.path.exists("test")\n')

        # Analyze and load
        loader = graph_loader.GraphLoader(neo4j_connection, package_name="test_import")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        assert result.success is True

        # Query for Import node
        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            imports = session.run(
                """
                MATCH (m:Module {package: $pkg})-[:IMPORTS]->(i:Import)
                RETURN i.from_module as from_module, i.local_name as local_name
                """,
                pkg="test_import",
            ).data()

            assert len(imports) == 1
            assert imports[0]["from_module"] == "os"
            assert imports[0]["local_name"] == "os"

        # Cleanup
        loader.clear_package()

    def test_import_with_alias(self, neo4j_connection, tmp_path: Path):
        """Test that 'import json as js' uses alias as local_name."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("import json as js\n\ndef func():\n    return js.dumps({})\n")

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="test_alias")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        assert result.success is True

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            imports = session.run(
                """
                MATCH (m:Module {package: $pkg})-[:IMPORTS]->(i:Import)
                RETURN i.from_module as from_module, i.local_name as local_name
                """,
                pkg="test_alias",
            ).data()

            assert len(imports) == 1
            assert imports[0]["from_module"] == "json"
            assert imports[0]["local_name"] == "js"  # Alias, not original name

        loader.clear_package()

    def test_from_import(self, neo4j_connection, tmp_path: Path):
        """Test that 'from pathlib import Path' creates correct Import node."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text('from pathlib import Path\n\ndef func():\n    return Path(".")\n')

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="test_from")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        assert result.success is True

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            imports = session.run(
                """
                MATCH (m:Module {package: $pkg})-[:IMPORTS]->(i:Import)
                RETURN i.from_module as from_module, i.local_name as local_name
                """,
                pkg="test_from",
            ).data()

            assert len(imports) == 1
            assert imports[0]["from_module"] == "pathlib"
            assert imports[0]["local_name"] == "Path"

        loader.clear_package()

    def test_from_import_with_alias(self, neo4j_connection, tmp_path: Path):
        """Test that 'from typing import Optional as Opt' uses alias."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text(
            "from typing import Optional as Opt\n\ndef func(x: Opt[int]):\n    return x\n"
        )

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="test_from_alias")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        assert result.success is True

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            imports = session.run(
                """
                MATCH (m:Module {package: $pkg})-[:IMPORTS]->(i:Import)
                RETURN i.from_module as from_module, i.local_name as local_name
                """,
                pkg="test_from_alias",
            ).data()

            assert len(imports) == 1
            assert imports[0]["from_module"] == "typing"
            assert imports[0]["local_name"] == "Opt"

        loader.clear_package()

    def test_submodule_import(self, neo4j_connection, tmp_path: Path):
        """Test that 'from collections.abc import Mapping' has submodule_path."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("from collections.abc import Mapping\n\ndef func():\n    pass\n")

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="test_submodule")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        assert result.success is True

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            imports = session.run(
                """
                MATCH (m:Module {package: $pkg})-[:IMPORTS]->(i:Import)
                RETURN i.from_module as from_module, i.submodule_path as submodule_path, i.local_name as local_name
                """,
                pkg="test_submodule",
            ).data()

            assert len(imports) == 1
            assert imports[0]["from_module"] == "collections"
            assert imports[0]["submodule_path"] == "abc"
            assert imports[0]["local_name"] == "Mapping"

        loader.clear_package()

    def test_multiple_imports_from_same_module(self, neo4j_connection, tmp_path: Path):
        """Test that multiple imports from same module create multiple Import nodes."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text(
            "from dataclasses import dataclass, field\n\n@dataclass\nclass C:\n    x: int = field()\n"
        )

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="test_multiple")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        assert result.success is True

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            imports = session.run(
                """
                MATCH (m:Module {package: $pkg})-[:IMPORTS]->(i:Import)
                RETURN i.from_module as from_module, i.local_name as local_name
                ORDER BY i.local_name
                """,
                pkg="test_multiple",
            ).data()

            assert len(imports) == 2
            assert imports[0]["from_module"] == "dataclasses"
            assert imports[0]["local_name"] == "dataclass"
            assert imports[1]["from_module"] == "dataclasses"
            assert imports[1]["local_name"] == "field"

        loader.clear_package()

    def test_from_module_relationship(self, neo4j_connection, tmp_path: Path):
        """Test that FROM_MODULE relationship connects Import to external Module."""
        test_file = tmp_path / "test_module.py"
        test_file.write_text("import pandas\n\ndef func():\n    pass\n")

        loader = graph_loader.GraphLoader(neo4j_connection, package_name="test_from_rel")
        loader.clear_package()
        code_analyser = analyser.Analyser(tmp_path, loader=loader)
        result = code_analyser.analyse()

        assert result.success is True

        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            # Check FROM_MODULE relationship exists
            from_module_rels = session.run(
                """
                MATCH (i:Import {package: $pkg})-[:FROM_MODULE]->(m:Module)
                RETURN m.name as module_name, m.is_external as is_external
                """,
                pkg="test_from_rel",
            ).data()

            assert len(from_module_rels) == 1
            assert from_module_rels[0]["module_name"] == "pandas"
            assert from_module_rels[0]["is_external"] is True

        loader.clear_package()
