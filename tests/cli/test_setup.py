"""Tests for setup commands."""

from typer.testing import CliRunner

from mapper.cli import app

runner = CliRunner()


class TestInitCommand:
    """Tests for init command."""

    def test_init_command(self):
        """Test init command is accessible."""
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0
        assert "Initializing mapper.yml" in result.stdout
        assert "Not implemented yet" in result.stdout
