"""Main CLI entry point for AI Context Manager."""

import typer
from rich.console import Console

from ai_context_manager.commands.export_cmd import app as export_app
from ai_context_manager.commands.profile_cmd import app as profile_app

app = typer.Typer(
    name="ai-context-manager",
    help="AI Context Manager - Export codebases for AI analysis",
    add_completion=False,
)
console = Console()

# Add subcommands
app.add_typer(export_app, name="export", help="Export files to AI context format")
app.add_typer(profile_app, name="profile", help="Manage export profiles")


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