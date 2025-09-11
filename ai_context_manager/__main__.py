"""Main entry point for AI Context Manager CLI."""
import typer

from ai_context_manager.commands.export_cmd import app as export_app
from ai_context_manager.commands.profile_cmd import app as profile_app
from ai_context_manager.commands.import_cmd import app as import_app
from ai_context_manager.config import CLI_CONTEXT_SETTINGS

app = typer.Typer(
    help="AI Context Manager - Export code context for AI analysis",
    context_settings=CLI_CONTEXT_SETTINGS,
)
app.add_typer(export_app, name="export")
app.add_typer(profile_app, name="profile")
app.add_typer(import_app, name="import")

if __name__ == "__main__":
    app()