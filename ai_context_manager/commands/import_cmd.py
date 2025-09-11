"""Import files from directory structure command."""
import typer
import fnmatch
from pathlib import Path
from typing import List, Optional
import yaml
import os

from ..config import get_config_dir

app = typer.Typer(help="Import files from directory structure")

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

def should_include_file(file_path: str, pattern: Optional[str], exclude: Optional[str]) -> bool:
    """Check if a file should be included based on pattern and exclude rules."""
    if pattern and not fnmatch.fnmatch(file_path, pattern):
        return False

    if exclude and fnmatch.fnmatch(file_path, exclude):
        return False

    # Skip common ignore patterns
    ignore_patterns = ['.git', '__pycache__', '*.pyc', '.DS_Store']
    for ignore_pattern in ignore_patterns:
        if fnmatch.fnmatch(file_path, f"*{ignore_pattern}*"):
            return False

    return True

@app.command()
def directory(
    path: str = typer.Argument(..., help="Directory path to import"),
    recursive: bool = typer.Option(True, "--recursive", "-r", help="Import directories recursively"),
    pattern: Optional[str] = typer.Option(None, "--pattern", "-p", help="File pattern to match"),
    exclude: Optional[str] = typer.Option(None, "--exclude", "-e", help="Pattern to exclude files"),
    base_path: Optional[str] = typer.Option(None, "--base-path", "-b", help="Base path to strip from file paths"),
):
    """Import files from a directory structure while preserving hierarchy."""
    context = load_context()
    existing_files = set(context.get("files", []))

    new_files = []
    base_dir = Path(path)

    if not base_dir.exists():
        typer.echo(f"Error: Directory does not exist: {path}", err=True)
        raise typer.Exit(1)

    if not base_dir.is_dir():
        typer.echo(f"Error: Path is not a directory: {path}", err=True)
        raise typer.Exit(1)

    # Process files
    if recursive:
        for file_path in base_dir.rglob("*"):
            if file_path.is_file():
                resolved_path = str(file_path.resolve())
                if should_include_file(resolved_path, pattern, exclude):
                    # Preserve hierarchy relative to base_dir
                    relative_path = os.path.relpath(resolved_path, base_dir)
                    if base_path:
                        relative_path = os.path.relpath(resolved_path, base_path)
                    new_files.append(relative_path)
    else:
        for file_path in base_dir.iterdir():
            if file_path.is_file():
                resolved_path = str(file_path.resolve())
                if should_include_file(resolved_path, pattern, exclude):
                    # Preserve hierarchy relative to base_dir
                    relative_path = os.path.relpath(resolved_path, base_dir)
                    if base_path:
                        relative_path = os.path.relpath(resolved_path, base_path)
                    new_files.append(relative_path)

    # Add new files to existing ones
    all_files = list(existing_files.union(set(new_files)))
    all_files.sort()

    context["files"] = all_files
    save_context(context)

    typer.echo(f"Added {len(new_files)} new file(s) to context")
    for file in new_files:
        typer.echo(f"  + {file}")

if __name__ == "__main__":
    app()