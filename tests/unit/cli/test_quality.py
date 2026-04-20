"""Tests for quality CLI commands."""

from unittest import mock

from typer.testing import CliRunner

from mapper.cli.quality import app

runner = CliRunner()


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


class TestQualityRun:
    """Test 'mapper quality run' command."""

    @mock.patch("mapper.cli._quality_helpers.run_quality_checks")
    def test_run_all_passing(self, mock_run_checks):
        """Should exit 0 when all checks pass."""
        mock_run_checks.return_value = 0

        result = runner.invoke(app, ["run", "all", "--package", "testpackage"])

        assert result.exit_code == 0
        mock_run_checks.assert_called_once_with("all", "testpackage", mock.ANY, None)

    @mock.patch("mapper.cli._quality_helpers.run_quality_checks")
    def test_run_all_failing(self, mock_run_checks):
        """Should exit 1 when any check fails."""
        mock_run_checks.return_value = 1

        result = runner.invoke(app, ["run", "all", "--package", "testpackage"])

        assert result.exit_code == 1

    @mock.patch("mapper.cli._quality_helpers.run_quality_checks")
    def test_run_single_rule(self, mock_run_checks):
        """Should run single rule."""
        mock_run_checks.return_value = 0

        result = runner.invoke(app, ["run", "type-coverage", "--package", "testpackage"])

        assert result.exit_code == 0
        mock_run_checks.assert_called_once_with("type-coverage", "testpackage", mock.ANY, None)

    @mock.patch("mapper.cli._quality_helpers.run_quality_checks")
    def test_run_with_json_flag(self, mock_run_checks):
        """Should pass JSON format to helper."""
        from mapper.quality.formatters import OutputFormat

        mock_run_checks.return_value = 0

        result = runner.invoke(app, ["run", "type-coverage", "--package", "testpackage", "--json"])

        assert result.exit_code == 0
        # Check that OutputFormat.JSON was passed
        call_args = mock_run_checks.call_args
        assert call_args[0][2] == OutputFormat.JSON

    @mock.patch("mapper.cli._quality_helpers.run_quality_checks")
    def test_run_with_config_path(self, mock_run_checks):
        """Should pass config path to helper."""
        mock_run_checks.return_value = 0

        result = runner.invoke(
            app, ["run", "all", "--package", "testpackage", "--config", "/path/to/config.toml"]
        )

        assert result.exit_code == 0
        mock_run_checks.assert_called_once_with(
            "all", "testpackage", mock.ANY, "/path/to/config.toml"
        )

    @mock.patch("mapper.cli._quality_helpers.run_quality_checks")
    def test_run_case_insensitive_all(self, mock_run_checks):
        """Should accept 'ALL' (case insensitive)."""
        mock_run_checks.return_value = 0

        result = runner.invoke(app, ["run", "ALL", "--package", "testpackage"])

        assert result.exit_code == 0
        mock_run_checks.assert_called_once_with("ALL", "testpackage", mock.ANY, None)
