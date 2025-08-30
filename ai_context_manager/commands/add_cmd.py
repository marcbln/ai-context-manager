"""Add files to context command."""
import typer
import fnmatch
from pathlib import Path
from typing import List, Optional
import yaml
import os

from ..config import get_config_dir

app = typer.Typer(help="Add files to context")

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
    paths: List[str] = typer.Argument(..., help="File or directory paths to add"),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Add directories recursively"),
    pattern: Optional[str] = typer.Option(None, "--pattern", "-p", help="File pattern to match"),
    exclude: Optional[str] = typer.Option(None, "--exclude", "-e", help="Pattern to exclude files"),
):
    """Add files to the current context."""
    context = load_context()
    existing_files = set(context.get("files", []))
    
    new_files = []
    
    for path_str in paths:
        path = Path(path_str)
        
        if not path.exists():
            typer.echo(f"Warning: Path does not exist: {path}", err=True)
            continue
            
        if path.is_file():
            file_path = str(path.resolve())
            if should_include_file(file_path, pattern, exclude):
                new_files.append(file_path)
        elif path.is_dir():
            if recursive:
                for file_path in path.rglob("*"):
                    if file_path.is_file():
                        resolved_path = str(file_path.resolve())
                        if should_include_file(resolved_path, pattern, exclude):
                            new_files.append(resolved_path)
            else:
                for file_path in path.iterdir():
                    if file_path.is_file():
                        resolved_path = str(file_path.resolve())
                        if should_include_file(resolved_path, pattern, exclude):
                            new_files.append(resolved_path)
    
    # Add new files to existing ones
    all_files = list(existing_files.union(set(new_files)))
    all_files.sort()
    
    context["files"] = all_files
    save_context(context)
    
    typer.echo(f"Added {len(new_files)} new file(s) to context")
    for file in new_files:
        typer.echo(f"  + {file}")

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