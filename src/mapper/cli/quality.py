"""Quality check commands for Mapper CLI."""

import typer
from rich.console import Console

from mapper.cli import _quality_helpers
from mapper.quality import registry
from mapper.quality.formatters import OutputFormat

console = Console()

app = typer.Typer(help="Run code quality checks")


@app.command(name="list")
def list_rules() -> None:
    """List all available quality rules.

    Shows quality rules with their descriptions and default thresholds.
    """
    reg = registry.get_registry()
    rules = reg.list_all()

    console.print(f"\n[bold]Available Quality Rules[/bold] ({len(rules)} total)\n")
    console.print(f"{'Rule':<25} {'Description'}")
    console.print(f"{'-' * 25} {'-' * 50}")

    for rule in rules:
        console.print(f"[cyan]{rule.name:<25}[/cyan] {rule.description}")

    console.print()
    console.print("[dim]Use 'mapper quality run <rule> --package <pkg>' to run a check[/dim]")
    console.print(
        "[dim]Use 'mapper quality run all --package <pkg>' to run all enabled checks[/dim]"
    )
    console.print()


@app.command(name="run")
def run(
    check: str = typer.Argument(..., help="Quality check to run (or 'all' for all enabled checks)"),
    package: str = typer.Option(..., help="Package name to check"),
    format_type: OutputFormat = typer.Option(
        OutputFormat.CONSOLE, "--format", help="Output format: console, json, csv"
    ),
    json_flag: bool = typer.Option(
        False, "--json", help="Output as JSON (shorthand for --format json)"
    ),
    csv_flag: bool = typer.Option(
        False, "--csv", help="Output as CSV (shorthand for --format csv)"
    ),
    config_path: str | None = typer.Option(
        None, "--config", help="Path to mapper.toml config file"
    ),
) -> None:
    """Run a quality check against an analyzed package.

    Exit code 0 if all checks pass, 1 if any check fails.

    Examples:
        mapper quality run type-coverage --package mypackage
        mapper quality run all --package mypackage
        mapper quality run docstring-coverage --package mypackage --json
    """
    # Resolve format (flags override --format option)
    output_format = (
        OutputFormat.JSON if json_flag else OutputFormat.CSV if csv_flag else format_type
    )

    # Execute checks and exit with appropriate code
    exit_code = _quality_helpers.run_quality_checks(check, package, output_format, config_path)
    raise typer.Exit(code=exit_code)
