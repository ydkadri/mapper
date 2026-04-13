"""Tests for quality CLI commands."""

from unittest import mock

import pytest
import typer
from typer.testing import CliRunner

from mapper.cli.quality import app
from mapper.quality import models

runner = CliRunner()


@pytest.fixture
def mock_connection():
    """Create mock Neo4j connection."""
    conn = mock.MagicMock()
    conn.test_connection.return_value = (True, "Connected")
    return conn


@pytest.fixture
def sample_passing_result():
    """Sample passing quality result."""
    return models.CoverageQualityResult(
        rule="type-coverage",
        threshold=80,
        actual=85.0,
        overall=models.OverallResult(total=20, compliant=17, percentage=85.0),
        by_file=[],
    )


@pytest.fixture
def sample_failing_result():
    """Sample failing quality result."""
    return models.CoverageQualityResult(
        rule="type-coverage",
        threshold=80,
        actual=75.0,
        overall=models.OverallResult(total=20, compliant=15, percentage=75.0),
        by_file=[],
    )


class TestQualityList:
    """Test 'mapper quality list' command."""

    @mock.patch("mapper.cli.quality.registry.get_registry")
    def test_list_shows_all_rules(self, mock_get_registry):
        """Should list all available quality rules."""
        # Mock registry
        mock_registry = mock.MagicMock()
        mock_rule1 = mock.MagicMock()
        mock_rule1.name = "type-coverage"
        mock_rule1.description = "Check type hint coverage"

        mock_rule2 = mock.MagicMock()
        mock_rule2.name = "docstring-coverage"
        mock_rule2.description = "Check docstring coverage"

        mock_registry.list_all.return_value = [mock_rule1, mock_rule2]
        mock_get_registry.return_value = mock_registry

        result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "type-coverage" in result.stdout
        assert "docstring-coverage" in result.stdout
        assert "Check type hint coverage" in result.stdout
        assert "Check docstring coverage" in result.stdout


class TestQualityCheck:
    """Test 'mapper quality check' command."""

    @mock.patch("mapper.cli.quality.graph.Neo4jConnection")
    @mock.patch("mapper.cli.quality.config_manager.load_config")
    @mock.patch("mapper.cli.quality.config_manager.get_neo4j_credentials")
    @mock.patch("mapper.cli.quality.config.load_quality_config")
    @mock.patch("mapper.cli.quality.executor.QualityExecutor")
    @mock.patch("mapper.cli.quality.formatters.get_formatter")
    def test_check_all_passing(
        self,
        mock_get_formatter,
        mock_executor_class,
        mock_load_quality,
        mock_get_creds,
        mock_load_config,
        mock_connection_class,
        mock_connection,
        sample_passing_result,
    ):
        """Should exit 0 when all checks pass."""
        # Setup mocks
        mock_get_creds.return_value = ("user", "password")
        mock_config = mock.MagicMock()
        mock_config.neo4j.uri = "bolt://localhost:7687"
        mock_config.neo4j.database = "neo4j"
        mock_load_config.return_value = mock_config

        mock_connection_class.return_value = mock_connection

        mock_quality_config = models.QualityConfig()
        mock_load_quality.return_value = mock_quality_config

        mock_executor = mock.MagicMock()
        mock_executor.execute_all.return_value = [sample_passing_result]
        mock_executor_class.return_value = mock_executor

        mock_formatter = mock.MagicMock()
        mock_formatter.format_results.return_value = "✓ All checks passed"
        mock_get_formatter.return_value = mock_formatter

        result = runner.invoke(app, ["check", "testpackage"])

        assert result.exit_code == 0
        mock_executor.execute_all.assert_called_once_with("testpackage", mock_quality_config)

    @mock.patch("mapper.cli.quality.graph.Neo4jConnection")
    @mock.patch("mapper.cli.quality.config_manager.load_config")
    @mock.patch("mapper.cli.quality.config_manager.get_neo4j_credentials")
    @mock.patch("mapper.cli.quality.config.load_quality_config")
    @mock.patch("mapper.cli.quality.executor.QualityExecutor")
    @mock.patch("mapper.cli.quality.formatters.get_formatter")
    def test_check_some_failing(
        self,
        mock_get_formatter,
        mock_executor_class,
        mock_load_quality,
        mock_get_creds,
        mock_load_config,
        mock_connection_class,
        mock_connection,
        sample_failing_result,
    ):
        """Should exit 1 when any check fails."""
        # Setup mocks
        mock_get_creds.return_value = ("user", "password")
        mock_config = mock.MagicMock()
        mock_config.neo4j.uri = "bolt://localhost:7687"
        mock_config.neo4j.database = "neo4j"
        mock_load_config.return_value = mock_config

        mock_connection_class.return_value = mock_connection

        mock_quality_config = models.QualityConfig()
        mock_load_quality.return_value = mock_quality_config

        mock_executor = mock.MagicMock()
        mock_executor.execute_all.return_value = [sample_failing_result]
        mock_executor_class.return_value = mock_executor

        mock_formatter = mock.MagicMock()
        mock_formatter.format_results.return_value = "✗ Some checks failed"
        mock_get_formatter.return_value = mock_formatter

        result = runner.invoke(app, ["check", "testpackage"])

        assert result.exit_code == 1

    @mock.patch("mapper.cli.quality.graph.Neo4jConnection")
    @mock.patch("mapper.cli.quality.config_manager.load_config")
    @mock.patch("mapper.cli.quality.config_manager.get_neo4j_credentials")
    def test_check_connection_failed(
        self, mock_get_creds, mock_load_config, mock_connection_class
    ):
        """Should exit 1 when Neo4j connection fails."""
        mock_get_creds.return_value = ("user", "password")
        mock_config = mock.MagicMock()
        mock_config.neo4j.uri = "bolt://localhost:7687"
        mock_config.neo4j.database = "neo4j"
        mock_load_config.return_value = mock_config

        mock_connection = mock.MagicMock()
        mock_connection.test_connection.return_value = (False, "Connection refused")
        mock_connection_class.return_value = mock_connection

        result = runner.invoke(app, ["check", "testpackage"])

        assert result.exit_code == 1
        assert "Connection refused" in result.stdout

    @mock.patch("mapper.cli.quality.graph.Neo4jConnection")
    @mock.patch("mapper.cli.quality.config_manager.load_config")
    @mock.patch("mapper.cli.quality.config_manager.get_neo4j_credentials")
    @mock.patch("mapper.cli.quality.config.load_quality_config")
    @mock.patch("mapper.cli.quality.executor.QualityExecutor")
    def test_check_value_error(
        self,
        mock_executor_class,
        mock_load_quality,
        mock_get_creds,
        mock_load_config,
        mock_connection_class,
        mock_connection,
    ):
        """Should exit 1 on ValueError."""
        mock_get_creds.return_value = ("user", "password")
        mock_config = mock.MagicMock()
        mock_config.neo4j.uri = "bolt://localhost:7687"
        mock_config.neo4j.database = "neo4j"
        mock_load_config.return_value = mock_config

        mock_connection_class.return_value = mock_connection

        mock_quality_config = models.QualityConfig()
        mock_load_quality.return_value = mock_quality_config

        mock_executor = mock.MagicMock()
        mock_executor.execute_all.side_effect = ValueError("No rules enabled")
        mock_executor_class.return_value = mock_executor

        result = runner.invoke(app, ["check", "testpackage"])

        assert result.exit_code == 1
        assert "No rules enabled" in result.stdout


class TestQualitySingleRule:
    """Test single rule commands."""

    @mock.patch("mapper.cli.quality.graph.Neo4jConnection")
    @mock.patch("mapper.cli.quality.config_manager.load_config")
    @mock.patch("mapper.cli.quality.config_manager.get_neo4j_credentials")
    @mock.patch("mapper.cli.quality.config.load_quality_config")
    @mock.patch("mapper.cli.quality.executor.QualityExecutor")
    @mock.patch("mapper.cli.quality.formatters.get_formatter")
    def test_type_coverage_passing(
        self,
        mock_get_formatter,
        mock_executor_class,
        mock_load_quality,
        mock_get_creds,
        mock_load_config,
        mock_connection_class,
        mock_connection,
        sample_passing_result,
    ):
        """Should exit 0 when type-coverage passes."""
        # Setup mocks
        mock_get_creds.return_value = ("user", "password")
        mock_config = mock.MagicMock()
        mock_config.neo4j.uri = "bolt://localhost:7687"
        mock_config.neo4j.database = "neo4j"
        mock_load_config.return_value = mock_config

        mock_connection_class.return_value = mock_connection

        mock_quality_config = models.QualityConfig()
        mock_load_quality.return_value = mock_quality_config

        mock_executor = mock.MagicMock()
        mock_executor.execute.return_value = sample_passing_result
        mock_executor_class.return_value = mock_executor

        mock_formatter = mock.MagicMock()
        mock_formatter.format_results.return_value = "✓ Type coverage passed"
        mock_get_formatter.return_value = mock_formatter

        result = runner.invoke(app, ["type-coverage", "testpackage"])

        assert result.exit_code == 0
        mock_executor.execute.assert_called_once_with(
            "type-coverage", "testpackage", mock_quality_config
        )

    @mock.patch("mapper.cli.quality.graph.Neo4jConnection")
    @mock.patch("mapper.cli.quality.config_manager.load_config")
    @mock.patch("mapper.cli.quality.config_manager.get_neo4j_credentials")
    @mock.patch("mapper.cli.quality.config.load_quality_config")
    @mock.patch("mapper.cli.quality.executor.QualityExecutor")
    @mock.patch("mapper.cli.quality.formatters.get_formatter")
    def test_docstring_coverage_failing(
        self,
        mock_get_formatter,
        mock_executor_class,
        mock_load_quality,
        mock_get_creds,
        mock_load_config,
        mock_connection_class,
        mock_connection,
        sample_failing_result,
    ):
        """Should exit 1 when docstring-coverage fails."""
        # Setup mocks
        mock_get_creds.return_value = ("user", "password")
        mock_config = mock.MagicMock()
        mock_config.neo4j.uri = "bolt://localhost:7687"
        mock_config.neo4j.database = "neo4j"
        mock_load_config.return_value = mock_config

        mock_connection_class.return_value = mock_connection

        mock_quality_config = models.QualityConfig()
        mock_load_quality.return_value = mock_quality_config

        # Make result have rule name matching docstring-coverage
        failing_result = models.CoverageQualityResult(
            rule="docstring-coverage",
            threshold=90,
            actual=75.0,
            overall=models.OverallResult(total=20, compliant=15, percentage=75.0),
            by_file=[],
        )

        mock_executor = mock.MagicMock()
        mock_executor.execute.return_value = failing_result
        mock_executor_class.return_value = mock_executor

        mock_formatter = mock.MagicMock()
        mock_formatter.format_results.return_value = "✗ Docstring coverage failed"
        mock_get_formatter.return_value = mock_formatter

        result = runner.invoke(app, ["docstring-coverage", "testpackage"])

        assert result.exit_code == 1
        mock_executor.execute.assert_called_once_with(
            "docstring-coverage", "testpackage", mock_quality_config
        )

    @mock.patch("mapper.cli.quality.graph.Neo4jConnection")
    @mock.patch("mapper.cli.quality.config_manager.load_config")
    @mock.patch("mapper.cli.quality.config_manager.get_neo4j_credentials")
    @mock.patch("mapper.cli.quality.config.load_quality_config")
    @mock.patch("mapper.cli.quality.executor.QualityExecutor")
    @mock.patch("mapper.cli.quality.formatters.get_formatter")
    def test_param_complexity_with_json(
        self,
        mock_get_formatter,
        mock_executor_class,
        mock_load_quality,
        mock_get_creds,
        mock_load_config,
        mock_connection_class,
        mock_connection,
    ):
        """Should output JSON when --json flag provided."""
        # Setup mocks
        mock_get_creds.return_value = ("user", "password")
        mock_config = mock.MagicMock()
        mock_config.neo4j.uri = "bolt://localhost:7687"
        mock_config.neo4j.database = "neo4j"
        mock_load_config.return_value = mock_config

        mock_connection_class.return_value = mock_connection

        mock_quality_config = models.QualityConfig()
        mock_load_quality.return_value = mock_quality_config

        passing_result = models.ComplexityQualityResult(
            rule="param-complexity",
            threshold=5,
            total_violations=0,
            by_file=[],
        )

        mock_executor = mock.MagicMock()
        mock_executor.execute.return_value = passing_result
        mock_executor_class.return_value = mock_executor

        mock_formatter = mock.MagicMock()
        mock_formatter.format_results.return_value = '{"rule": "param-complexity"}'
        mock_get_formatter.return_value = mock_formatter

        result = runner.invoke(app, ["param-complexity", "testpackage", "--json"])

        assert result.exit_code == 0
        # Should call get_formatter with JSON format
        from mapper.quality.formatters import OutputFormat

        mock_get_formatter.assert_called_once_with(OutputFormat.JSON)
