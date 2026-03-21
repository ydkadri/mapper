"""Tests for config management commands."""

from typer.testing import CliRunner

from mapper.cli import app

runner = CliRunner()


class TestConfigGetCommand:
    """Tests for config get command."""

    def test_get_config_value(self):
        """Test config get command."""
        result = runner.invoke(app, ["config", "get", "neo4j.endpoint"])
        assert result.exit_code == 0
        assert "Getting config value: neo4j.endpoint" in result.stdout
        assert "Not implemented yet" in result.stdout


class TestConfigShowCommand:
    """Tests for config show command."""

    def test_config_help(self):
        """Test config subcommand help."""
        result = runner.invoke(app, ["config", "--help"])
        assert result.exit_code == 0
        assert "Manage configuration" in result.stdout
        assert "get" in result.stdout
        assert "show" in result.stdout
        assert "edit" in result.stdout

    def test_show_all_config(self):
        """Test config show command without group."""
        result = runner.invoke(app, ["config", "show"])
        assert result.exit_code == 0
        assert "Current configuration" in result.stdout
        assert "Not implemented yet" in result.stdout

    def test_show_config_group(self):
        """Test config show command with group."""
        result = runner.invoke(app, ["config", "show", "neo4j"])
        assert result.exit_code == 0
        assert "Configuration for: neo4j" in result.stdout
        assert "Not implemented yet" in result.stdout


class TestConfigEditCommand:
    """Tests for config edit command."""

    def test_edit_config(self):
        """Test config edit command."""
        result = runner.invoke(app, ["config", "edit"])
        assert result.exit_code == 0
        assert "Opening configuration in editor" in result.stdout
        assert "Not implemented yet" in result.stdout
