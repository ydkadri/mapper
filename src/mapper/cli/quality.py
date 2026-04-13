"""Quality check commands for Mapper CLI."""

import sys

import typer
from neo4j.exceptions import DriverError
from rich.console import Console

from mapper import config_manager, graph
from mapper.quality import config, executor, formatters, registry
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
    console.print("[dim]Use 'mapper quality <rule> <package>' to run a specific rule[/dim]")
    console.print("[dim]Use 'mapper quality check <package>' to run all enabled rules[/dim]")
    console.print()


@app.command()
def check(
    package: str,
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
    """Run all enabled quality checks on a package.

    Runs all quality rules that are enabled in configuration.
    Exit code 0 if all checks pass, 1 if any check fails.

    Example:
        mapper quality check mypackage
        mapper quality check mypackage --json
    """
    # Resolve format (flags override --format option)
    output_format = (
        OutputFormat.JSON if json_flag else OutputFormat.CSV if csv_flag else format_type
    )

    try:
        # Get Neo4j credentials and config
        user, password = config_manager.get_neo4j_credentials()
        db_config = config_manager.load_config()

        # Create connection
        connection = graph.Neo4jConnection(
            uri=db_config.neo4j.uri,
            user=user,
            password=password,
            database=db_config.neo4j.database,
        )

        # Test connection
        success, message = connection.test_connection()
        if not success:
            console.print(f"[red]Neo4j connection failed:[/red] {message}")
            console.print("\nEnsure Neo4j is running and credentials are correct.")
            console.print("Run 'mapper status' to check configuration.")
            raise typer.Exit(code=1)

        # Load quality configuration
        quality_config = config.load_quality_config(config_path)

        # Execute all enabled rules
        exec = executor.QualityExecutor(connection)
        results = exec.execute_all(package, quality_config)

        # Format and output
        formatter = formatters.get_formatter(output_format)
        output = formatter.format_results(results)

        # Print output
        match output_format:
            case OutputFormat.CONSOLE:
                # Rich console with colors
                console.print(output, end="")
            case OutputFormat.JSON:
                # JSON - write to stdout with newline
                sys.stdout.write(output)
                sys.stdout.write("\n")
            case OutputFormat.CSV:
                # CSV - write to stdout
                sys.stdout.write(output)

        # Cleanup
        connection.close()

        # Exit with appropriate code
        all_passed = all(result.status == "pass" for result in results)
        raise typer.Exit(code=0 if all_passed else 1)

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1) from None
    except (FileNotFoundError, OSError, DriverError) as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1) from e


@app.command(name="type-coverage")
def type_coverage_command(
    package: str,
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
    """Check type hint coverage on public functions.

    Verifies that public functions have type hints for all parameters.
    Exit code 0 if check passes, 1 if fails.

    Example:
        mapper quality type-coverage mypackage
        mapper quality type-coverage mypackage --json
    """
    _run_single_rule("type-coverage", package, format_type, json_flag, csv_flag, config_path)


@app.command(name="docstring-coverage")
def docstring_coverage_command(
    package: str,
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
    """Check docstring coverage on public functions.

    Verifies that public functions have docstrings.
    Exit code 0 if check passes, 1 if fails.

    Example:
        mapper quality docstring-coverage mypackage
        mapper quality docstring-coverage mypackage --json
    """
    _run_single_rule("docstring-coverage", package, format_type, json_flag, csv_flag, config_path)


@app.command(name="param-complexity")
def param_complexity_command(
    package: str,
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
    """Check parameter count complexity on functions.

    Verifies that functions don't exceed the maximum parameter count.
    Exit code 0 if check passes, 1 if fails.

    Example:
        mapper quality param-complexity mypackage
        mapper quality param-complexity mypackage --json
    """
    _run_single_rule("param-complexity", package, format_type, json_flag, csv_flag, config_path)


def _run_single_rule(
    rule_name: str,
    package: str,
    format_type: OutputFormat,
    json_flag: bool,
    csv_flag: bool,
    config_path: str | None,
) -> None:
    """Run a single quality rule (internal helper).

    Args:
        rule_name: Name of the rule to run
        package: Package name to check
        format_type: Output format type
        json_flag: JSON flag
        csv_flag: CSV flag
        config_path: Path to config file
    """
    # Resolve format (flags override --format option)
    output_format = (
        OutputFormat.JSON if json_flag else OutputFormat.CSV if csv_flag else format_type
    )

    try:
        # Get Neo4j credentials and config
        user, password = config_manager.get_neo4j_credentials()
        db_config = config_manager.load_config()

        # Create connection
        connection = graph.Neo4jConnection(
            uri=db_config.neo4j.uri,
            user=user,
            password=password,
            database=db_config.neo4j.database,
        )

        # Test connection
        success, message = connection.test_connection()
        if not success:
            console.print(f"[red]Neo4j connection failed:[/red] {message}")
            console.print("\nEnsure Neo4j is running and credentials are correct.")
            console.print("Run 'mapper status' to check configuration.")
            raise typer.Exit(code=1)

        # Load quality configuration
        quality_config = config.load_quality_config(config_path)

        # Execute rule
        exec = executor.QualityExecutor(connection)
        result = exec.execute(rule_name, package, quality_config)

        # Format and output
        formatter = formatters.get_formatter(output_format)
        output = formatter.format_results([result])

        # Print output
        match output_format:
            case OutputFormat.CONSOLE:
                # Rich console with colors
                console.print(output, end="")
            case OutputFormat.JSON:
                # JSON - write to stdout with newline
                sys.stdout.write(output)
                sys.stdout.write("\n")
            case OutputFormat.CSV:
                # CSV - write to stdout
                sys.stdout.write(output)

        # Cleanup
        connection.close()

        # Exit with appropriate code
        raise typer.Exit(code=0 if result.status == "pass" else 1)

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1) from None
    except (FileNotFoundError, OSError, DriverError) as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1) from e
