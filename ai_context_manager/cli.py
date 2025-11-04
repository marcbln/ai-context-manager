"""Main CLI entry point for AI Context Manager."""

__all__ = ['cli']

import typer
from rich.console import Console

from ai_context_manager.commands.add_cmd import app as add_app
from ai_context_manager.commands.export_cmd import app as export_app
from ai_context_manager.commands.import_cmd import app as import_app
from ai_context_manager.commands.list_cmd import app as list_app
from ai_context_manager.commands.profile_cmd import app as profile_app
from ai_context_manager.commands.remove_cmd import app as remove_app
from ai_context_manager.commands.init_cmd import app as init_app
from ai_context_manager.config import CLI_CONTEXT_SETTINGS

app = typer.Typer(
    name="aicontext",
    help="AI Context Manager - Export codebases for AI analysis",
    add_completion=False,
    context_settings=CLI_CONTEXT_SETTINGS,
)
console = Console()

# Import subcommands after CLI instance creation
from ai_context_manager.commands import (
    add_cmd,
    export_cmd,
    import_cmd,
    list_cmd,
    profile_cmd,
    remove_cmd,
    init_cmd
)

# Add subcommands
cli.add_typer(init_app, name="init")
cli.add_typer(add_app, name="add", help="Add files to the current session context")
cli.add_typer(remove_app, name="remove", help="Remove files from the current session context")
cli.add_typer(list_app, name="list", help="List files in the current session context")
cli.add_typer(export_app, name="export", help="Export files to AI context format")
cli.add_typer(profile_app, name="profile", help="Manage export profiles")
cli.add_typer(import_app, name="import", help="Import files from directory structure")


@cli.command()
def version():
    """Show version information."""
    console.print("AI Context Manager v0.1.0")


@cli.callback()
def main():
    """AI Context Manager - Export codebases for AI analysis."""
    pass


if __name__ == "__main__":
    cli()