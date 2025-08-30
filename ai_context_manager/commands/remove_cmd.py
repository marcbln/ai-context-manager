"""Remove files from context command."""
import typer
import yaml
from pathlib import Path
from typing import List

from ..config import get_config_dir

app = typer.Typer(help="Remove files from context")

def load_context():
    """Load the current context from YAML file."""
    config_dir = get_config_dir()
    context_file = config_dir / "context.yaml"
    
    if not context_file.exists():
        return {"files": []}
    
    with open(context_file, 'r') as f:
        return yaml.safe_load(f) or {"files": []}

def save_context(context):
    """Save the context to YAML file."""
    config_dir = get_config_dir()
    context_file = config_dir / "context.yaml"
    
    with open(context_file, 'w') as f:
        yaml.dump(context, f, default_flow_style=False)

@app.command()
def files(
    paths: List[str] = typer.Argument(..., help="File or directory paths to remove"),
    all_files: bool = typer.Option(False, "--all", "-a", help="Remove all files from context"),
):
    """Remove files from the current context."""
    context = load_context()
    existing_files = set(context.get("files", []))
    
    if all_files:
        removed_count = len(existing_files)
        context["files"] = []
        save_context(context)
        typer.echo(f"Removed all {removed_count} files from context")
        return
    
    removed_files = []
    
    for path_str in paths:
        path = Path(path_str).resolve()
        path_str = str(path)
        
        # Check for exact match
        if path_str in existing_files:
            existing_files.remove(path_str)
            removed_files.append(path_str)
            continue
            
        # Check for partial matches (substrings)
        matches = [f for f in existing_files if path_str in f]
        for match in matches:
            existing_files.remove(match)
            removed_files.append(match)
    
    if removed_files:
        context["files"] = sorted(list(existing_files))
        save_context(context)
        typer.echo(f"Removed {len(removed_files)} file(s) from context:")
        for file_path in removed_files:
            typer.echo(f"  - {file_path}")
    else:
        typer.echo("No matching files found to remove")