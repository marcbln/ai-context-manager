"""Manage export profiles command."""
import typer
import yaml
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from ..config import get_config_dir

app = typer.Typer(help="Manage export profiles")

def get_profiles_dir():
    """Get the directory for storing profiles."""
    config_dir = get_config_dir()
    profiles_dir = config_dir / "profiles"
    profiles_dir.mkdir(exist_ok=True)
    return profiles_dir

def load_profile(name: str) -> Optional[Dict[str, Any]]:
    """Load a profile by name."""
    profiles_dir = get_profiles_dir()
    profile_file = profiles_dir / f"{name}.yaml"
    
    if not profile_file.exists():
        return None
    
    with open(profile_file, 'r') as f:
        return yaml.safe_load(f)

def save_profile(name: str, profile: Dict[str, Any]):
    """Save a profile."""
    profiles_dir = get_profiles_dir()
    profile_file = profiles_dir / f"{name}.yaml"
    
    with open(profile_file, 'w') as f:
        yaml.dump(profile, f, default_flow_style=False)

@app.command()
def create(
    name: str = typer.Argument(..., help="Profile name"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Profile description"),
    format_type: str = typer.Option("markdown", "--format", "-f", help="Export format (markdown, xml, json)"),
    include_metadata: bool = typer.Option(True, "--metadata/--no-metadata", help="Include metadata in export"),
    max_file_size: Optional[int] = typer.Option(None, "--max-size", help="Maximum file size in bytes"),
    file_extensions: Optional[str] = typer.Option(None, "--extensions", help="Comma-separated file extensions to include"),
):
    """Create a new export profile."""
    profile = {
        "name": name,
        "description": description or f"Export profile for {format_type} format",
        "format": format_type,
        "include_metadata": include_metadata,
        "max_file_size": max_file_size,
        "file_extensions": [ext.strip() for ext in file_extensions.split(",")] if file_extensions else None,
        "created": datetime.now().isoformat(),
        "updated": datetime.now().isoformat()
    }
    
    save_profile(name, profile)
    typer.echo(f"Created profile: {name}")
    typer.echo(f"Format: {format_type}")
    if description:
        typer.echo(f"Description: {description}")

@app.command()
def list():
    """List all export profiles."""
    profiles_dir = get_profiles_dir()
    profiles = list(profiles_dir.glob("*.yaml"))
    
    if not profiles:
        typer.echo("No profiles found")
        return
    
    typer.echo("Available profiles:")
    for profile_file in sorted(profiles):
        name = profile_file.stem
        profile = load_profile(name)
        if profile:
            description = profile.get("description", "No description")
            format_type = profile.get("format", "unknown")
            typer.echo(f"  {name} ({format_type}): {description}")

@app.command()
def show(
    name: str = typer.Argument(..., help="Profile name to show"),
):
    """Show profile details."""
    profile = load_profile(name)
    
    if not profile:
        typer.echo(f"Profile '{name}' not found")
        return
    
    typer.echo(f"Profile: {name}")
    typer.echo(f"Description: {profile.get('description', 'No description')}")
    typer.echo(f"Format: {profile.get('format', 'unknown')}")
    typer.echo(f"Include metadata: {profile.get('include_metadata', True)}")
    
    if profile.get('max_file_size'):
        typer.echo(f"Max file size: {profile['max_file_size']} bytes")
    
    if profile.get('file_extensions'):
        typer.echo(f"File extensions: {', '.join(profile['file_extensions'])}")
    
    typer.echo(f"Created: {profile.get('created', 'Unknown')}")
    typer.echo(f"Updated: {profile.get('updated', 'Unknown')}")

@app.command()
def delete(
    name: str = typer.Argument(..., help="Profile name to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Force deletion without confirmation"),
):
    """Delete an export profile."""
    profile = load_profile(name)
    
    if not profile:
        typer.echo(f"Profile '{name}' not found")
        return
    
    if not force:
        typer.confirm(f"Are you sure you want to delete profile '{name}'?", abort=True)
    
    profiles_dir = get_profiles_dir()
    profile_file = profiles_dir / f"{name}.yaml"
    profile_file.unlink()
    
    typer.echo(f"Deleted profile: {name}")

@app.command()
def update(
    name: str = typer.Argument(..., help="Profile name to update"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Profile description"),
    format_type: Optional[str] = typer.Option(None, "--format", "-f", help="Export format (markdown, xml, json)"),
    include_metadata: Optional[bool] = typer.Option(None, "--metadata/--no-metadata", help="Include metadata in export"),
    max_file_size: Optional[int] = typer.Option(None, "--max-size", help="Maximum file size in bytes"),
    file_extensions: Optional[str] = typer.Option(None, "--extensions", help="Comma-separated file extensions to include"),
):
    """Update an existing export profile."""
    profile = load_profile(name)
    
    if not profile:
        typer.echo(f"Profile '{name}' not found")
        return
    
    if description is not None:
        profile["description"] = description
    
    if format_type is not None:
        profile["format"] = format_type
    
    if include_metadata is not None:
        profile["include_metadata"] = include_metadata
    
    if max_file_size is not None:
        profile["max_file_size"] = max_file_size
    
    if file_extensions is not None:
        profile["file_extensions"] = [ext.strip() for ext in file_extensions.split(",")] if file_extensions else None
    
    profile["updated"] = datetime.now().isoformat()
    
    save_profile(name, profile)
    typer.echo(f"Updated profile: {name}")