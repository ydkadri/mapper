"""Internal helper functions for quality CLI commands."""

import sys

import typer
from neo4j.exceptions import DriverError
from rich.console import Console

from mapper import config_manager, graph
from mapper.quality import config, executor, formatters
from mapper.quality.formatters import OutputFormat

console = Console()


def run_quality_checks(
    check_name: str,
    package: str,
    output_format: OutputFormat,
    config_path: str | None = None,
) -> int:
    """Execute quality check(s) and return exit code.

    Args:
        check_name: Name of check to run, or "all" for all checks
        package: Package name to check
        output_format: Output format (console, JSON, CSV)
        config_path: Optional path to config file

    Returns:
        Exit code (0 for pass, 1 for fail)

    Raises:
        typer.Exit: On errors
    """
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

        # Execute check(s)
        exec = executor.QualityExecutor(connection)

        if check_name.lower() == "all":
            results = exec.execute_all(package, quality_config)
        else:
            result = exec.execute(check_name, package, quality_config)
            results = [result]

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

        # Return exit code
        all_passed = all(result.status == "pass" for result in results)
        return 0 if all_passed else 1

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1) from None
    except (FileNotFoundError, OSError, DriverError) as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1) from e
