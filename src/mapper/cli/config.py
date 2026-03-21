"""Config management commands for MApper CLI."""

import typer
from rich.console import Console

console = Console()

app = typer.Typer(help="Manage configuration")


@app.command()
def get(key: str) -> None:
    """Get a specific configuration value.

    Examples:
        mapper config get neo4j.endpoint
        mapper config get logging.level
    """
    console.print(f"[yellow]Getting config value:[/yellow] {key}")
    console.print("[red]Not implemented yet[/red]")


@app.command(name="show")
def show_config(
    group: str | None = typer.Argument(None, help="Configuration group (e.g., neo4j, logging)"),
) -> None:
    """Show current configuration.

    Examples:
        mapper config show          # Show all configuration
        mapper config show neo4j    # Show only neo4j settings
    """
    if group:
        console.print(f"[yellow]Configuration for:[/yellow] {group}")
    else:
        console.print("[yellow]Current configuration:[/yellow]")
    console.print("[red]Not implemented yet[/red]")


@app.command()
def edit() -> None:
    """Edit configuration file in $EDITOR."""
    console.print("[yellow]Opening configuration in editor...[/yellow]")
    console.print("[red]Not implemented yet[/red]")
