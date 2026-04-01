"""Diagnostic test to debug integration test failures."""

from pathlib import Path

from mapper import analyser, graph, graph_loader


class TestDiagnostic:
    """Diagnostic tests to understand why nodes aren't being created."""

    def test_direct_node_creation(self, neo4j_connection):
        """Test creating a node directly without analyser."""
        # Directly create a node
        node_id = neo4j_connection.create_node(
            graph.NodeLabel.MODULE, {"name": "test", "package": "test_pkg"}
        )

        assert node_id, "Node ID should not be empty"

        # Query it back
        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            result = session.run(
                "MATCH (m:Module {package: $pkg}) RETURN m.name as name", pkg="test_pkg"
            ).data()

            assert len(result) == 1
            assert result[0]["name"] == "test"

        # Cleanup
        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            session.run("MATCH (m:Module {package: $pkg}) DELETE m", pkg="test_pkg")

    def test_file_scanner_finds_files(self, tmp_path: Path):
        """Test that FileScanner finds files in tmp_path."""
        # Create test file
        test_file = tmp_path / "test_module.py"
        test_file.write_text("def test(): pass\n")

        # Scan directory
        from mapper.analyser import file_scanner

        scanner = file_scanner.FileScanner(tmp_path)
        files = scanner.scan()

        assert len(files) == 1, f"Expected 1 file, found {len(files)}: {files}"
        assert files[0].name == "test_module.py"

    def test_analyser_with_single_file(self, neo4j_connection, tmp_path: Path):
        """Test analyser with single file and real Neo4j."""
        # Create test file
        test_file = tmp_path / "simple.py"
        test_file.write_text("def hello(): pass\n")

        # Create loader and analyser
        loader = graph_loader.GraphLoader(neo4j_connection, package_name="diagnostic_pkg")
        loader.clear_package()

        code_analyser = analyser.Analyser(tmp_path, loader=loader)

        # Run analysis
        result = code_analyser.analyse()

        # Debug: print result
        print(f"\nAnalysis result: {result}")
        print(f"Success: {result.success}")
        print(f"Modules: {result.modules_count}")
        print(f"Nodes created: {result.nodes_created}")
        print(f"Errors: {result.errors}")

        assert result.success is True
        assert result.modules_count == 1, f"Expected 1 module, got {result.modules_count}"

        # Query Neo4j directly
        with neo4j_connection.driver.session(database=neo4j_connection.database) as session:
            modules = session.run(
                "MATCH (m:Module {package: $pkg}) RETURN m.name as name", pkg="diagnostic_pkg"
            ).data()

            print(f"Modules found in Neo4j: {modules}")
            assert len(modules) == 1, f"Expected 1 module in Neo4j, found {len(modules)}"
            assert modules[0]["name"] == "simple"

        loader.clear_package()
