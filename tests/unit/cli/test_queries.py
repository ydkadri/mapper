"""Tests for query management commands."""

from typer.testing import CliRunner

from mapper.cli import app

runner = CliRunner()


class TestQueryListCommand:
    """Tests for query list command."""

    def test_query_help(self):
        """Test query subcommand help."""
        result = runner.invoke(app, ["query", "--help"])
        assert result.exit_code == 0
        assert "risk detection" in result.stdout.lower()
        assert "list" in result.stdout
        assert "run" in result.stdout

    def test_list_queries(self):
        """Test query list command."""
        result = runner.invoke(app, ["query", "list"])
        assert result.exit_code == 0
        assert "Available queries" in result.stdout
        assert "find-dead-code" in result.stdout
        assert "analyze-module-centrality" in result.stdout
        assert "find-critical-functions" in result.stdout

    def test_list_queries_with_group_filter(self):
        """Test query list command with group filter."""
        result = runner.invoke(app, ["query", "list", "--group", "risk"])
        assert result.exit_code == 0
        assert "Risk" in result.stdout
        assert "find-dead-code" in result.stdout
        # Should not show critical-components queries
        assert "find-critical-functions" not in result.stdout


class TestQueryRunCommand:
    """Tests for query run command."""

    def test_missing_package(self):
        """Test query run command fails without --package."""
        result = runner.invoke(app, ["query", "run", "find-dead-code"])
        assert result.exit_code != 0
        output = result.stdout + result.stderr
        assert "--package" in output or "package" in output.lower()
