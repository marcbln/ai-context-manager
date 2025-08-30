"""CLI interface for AI Context Manager."""

import typer
from typing import Optional
from pathlib import Path

from ai_context_manager.commands import add_cmd, list_cmd, remove_cmd, export_cmd, profile_cmd

app = typer.Typer(
    name="aicontext",
    help="Manage and export file selections as AI context",
    no_args_is_help=True,
)

# Add subcommands
app.add_typer(add_cmd.app, name="add", help="Add files to context")
app.add_typer(list_cmd.app, name="list", help="List files in context")
app.add_typer(remove_cmd.app, name="remove", help="Remove files from context")
app.add_typer(export_cmd.app, name="export", help="Export context to various formats")
app.add_typer(profile_cmd.app, name="profile", help="Manage export profiles")


@app.command()
def init(
    config_dir: Optional[Path] = typer.Option(
        None,
        "--config-dir",
        help="Directory to store configuration files",
    )
):
    """Initialize the AI context manager configuration."""
    from ai_context_manager.config import Config
    
    config = Config(config_dir)
    config.init()
    typer.echo(f"Initialized AI context manager in {config.config_dir}")


if __name__ == "__main__":
    app()