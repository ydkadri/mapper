"""Setup commands for MApper CLI."""

import typer
from rich.console import Console

console = Console()

app = typer.Typer(help="Setup commands")


@app.command()
def init() -> None:
    """Initialize mapper.yml configuration file in the current directory."""
    console.print("[yellow]Initializing mapper.yml...[/yellow]")
    console.print("[red]Not implemented yet[/red]")
