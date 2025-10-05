"""List files in context command."""
import json
import typer
import yaml
from pathlib import Path

from ..config import get_config_dir, CLI_CONTEXT_SETTINGS

app = typer.Typer(help="List files in context", context_settings=CLI_CONTEXT_SETTINGS)

@app.command()
def files(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed file information"),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON to stdout"),
):
    """List all files in the current context."""
    config_dir = get_config_dir()
    context_file = config_dir / "context.yaml"
    
    if not context_file.exists():
        if json_output:
            result = {"file_count": 0, "files": []}
            typer.echo(json.dumps(result))
            raise typer.Exit()
        typer.echo("No context file found. Run 'aicontext init' first.")
        return
    
    with open(context_file, 'r') as f:
        context = yaml.safe_load(f) or {"files": []}
    
    files = context.get("files", [])
    
    if not files:
        if json_output:
            result = {"file_count": 0, "files": []}
            typer.echo(json.dumps(result))
            raise typer.Exit()
        typer.echo("No files in context.")
        return
    
    if json_output:
        result = {
            "file_count": len(files),
            "files": files,
        }
        typer.echo(json.dumps(result))
        raise typer.Exit()
    
    typer.echo(f"Files in context ({len(files)} total):")
    for file_path in files:
        if verbose:
            file_size = Path(file_path).stat().st_size
            typer.echo(f"  {file_path} ({file_size} bytes)")
        else:
            typer.echo(f"  {file_path}")