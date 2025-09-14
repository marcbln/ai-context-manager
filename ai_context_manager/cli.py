"""Main CLI entry point for AI Context Manager."""

import typer
import yaml
from rich.console import Console

from ai_context_manager.commands.add_cmd import app as add_app
from ai_context_manager.commands.export_cmd import app as export_app
from ai_context_manager.commands.import_cmd import app as import_app
from ai_context_manager.commands.list_cmd import app as list_app
from ai_context_manager.commands.profile_cmd import app as profile_app
from ai_context_manager.commands.remove_cmd import app as remove_app
from ai_context_manager.config import CLI_CONTEXT_SETTINGS, get_config_dir

app = typer.Typer(
    name="aicontext",
    help="AI Context Manager - Export codebases for AI analysis",
    add_completion=False,
    context_settings=CLI_CONTEXT_SETTINGS,
)
console = Console()

# Add subcommands
app.add_typer(add_app, name="add", help="Add files to the current session context")
app.add_typer(remove_app, name="remove", help="Remove files from the current session context")
app.add_typer(list_app, name="list", help="List files in the current session context")
app.add_typer(export_app, name="export", help="Export files to AI context format")
app.add_typer(profile_app, name="profile", help="Manage export profiles")
app.add_typer(import_app, name="import", help="Import files from directory structure")


@app.command()
def init():
    """Initialize the current session context by creating an empty context file."""
    config_dir = get_config_dir()
    context_file = config_dir / "context.yaml"

    if context_file.exists():
        if typer.confirm("Session context file already exists. Overwrite and start a new session?"):
            pass
        else:
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


@app.command()
def version():
    """Show version information."""
    console.print("AI Context Manager v0.1.0")


@app.callback()
def main():
    """AI Context Manager - Export codebases for AI analysis."""
    pass


if __name__ == "__main__":
    app()