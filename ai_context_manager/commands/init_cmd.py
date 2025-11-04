"""Initialize session context command."""
import typer
import yaml
from rich.console import Console

from ..config import get_config_dir, CLI_CONTEXT_SETTINGS

app = typer.Typer(help="Initialize or reset the session context.", context_settings=CLI_CONTEXT_SETTINGS)
console = Console()

@app.command(name="init")
def init_command():
    """
    Initialize the session context.

    This command creates an empty context.yaml file in the configuration directory.
    This file is used to store the list of files for the current session.
    If the file already exists, it will prompt for confirmation before overwriting.
    """
    config_dir = get_config_dir()
    context_file = config_dir / "context.yaml"

    if context_file.exists():
        overwrite = typer.confirm(
            f"Session context file already exists at {context_file}.\n"
            "Overwrite and start a new session?"
        )
        if not overwrite:
            console.print("[yellow]Initialization cancelled.[/yellow]")
            raise typer.Abort()

    context = {"files": []}
    try:
        with open(context_file, "w") as f:
            yaml.dump(context, f, default_flow_style=False)
        console.print(f"[green]✓ Initialized empty session context at: {context_file}[/green]")
    except Exception as e:
        console.print(f"[red]✗ Failed to initialize session context: {e}[/red]")
        raise typer.Exit(1)