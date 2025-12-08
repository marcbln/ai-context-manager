"""Main CLI entry point."""
import typer
from rich.console import Console
from ai_context_manager.commands import select_cmd, export_cmd, generate_cmd
from ai_context_manager.config import CLI_CONTEXT_SETTINGS

app = typer.Typer(
    name="aicontext",
    help="Visual Context Manager - Select files visually and export for AI.",
    add_completion=False,
    context_settings=CLI_CONTEXT_SETTINGS,
)
console = Console()

app.add_typer(select_cmd.app, name="select", help="Open visual file selector")
app.add_typer(export_cmd.app, name="export", help="Native: Generate context from selection.yaml")
app.add_typer(generate_cmd.app, name="generate", help="Repomix: Generate context using external tool")

@app.command()
def version():
    """Show version information."""
    console.print("AI Context Manager v0.2.0 (Visual Edition)")

if __name__ == "__main__":
    app()

# Backwards compatibility
cli = app