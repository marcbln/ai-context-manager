"""Native Export command."""
from pathlib import Path
import typer
from rich.console import Console
from ai_context_manager.core.selection import Selection
from ai_context_manager.core.exporter import ContextExporter
from ai_context_manager.config import CLI_CONTEXT_SETTINGS

app = typer.Typer(context_settings=CLI_CONTEXT_SETTINGS)
console = Console()

@app.command("export")
def export(
    selection_file: Path = typer.Argument(..., help="Path to selection.yaml", exists=True),
    output: Path = typer.Option("context.md", "--output", "-o", help="Output file path"),
    format: str = typer.Option("markdown", "--format", "-f", help="Format: markdown, json, xml, yaml"),
):
    """Generate context file using the native Python exporter."""
    try:
        selection = Selection.load(selection_file)
    except Exception as e:
        console.print(f"[red]Error loading selection file: {e}[/red]")
        raise typer.Exit(1)

    console.print(f"[blue]Exporting from {selection.base_path}...[/blue]")
    exporter = ContextExporter(selection)
    result = exporter.export_to_file(output_path=output, format=format)

    if result["success"]:
        console.print(f"[green]✓ {result['message']}[/green]")
        console.print(f"  Total Tokens: [bold]{result['total_tokens']}[/bold]")
    else:
        console.print(f"[red]✗ Export failed: {result['message']}[/red]")
        raise typer.Exit(1)