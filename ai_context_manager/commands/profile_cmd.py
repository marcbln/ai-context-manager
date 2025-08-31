"""Profile management commands for AI Context Manager."""
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

import click
from datetime import datetime

from ai_context_manager.core.profile import Profile, PathEntry, ProfileManager
from ai_context_manager.config import get_config_dir


def get_profile_manager() -> ProfileManager:
    """Get the profile manager instance."""
    config_dir = get_config_dir()
    profiles_dir = config_dir / "profiles"
    return ProfileManager(profiles_dir)


def load_session_context() -> Dict[str, Any]:
    """Load the current session context from YAML file."""
    config_dir = get_config_dir()
    context_file = config_dir / "context.yaml"
    
    if not context_file.exists():
        return {"files": []}
    
    try:
        import yaml
        with context_file.open('r') as f:
            return yaml.safe_load(f) or {"files": []}
    except Exception:
        return {"files": []}


def save_session_context(context: Dict[str, Any]) -> None:
    """Save the session context to YAML file."""
    config_dir = get_config_dir()
    context_file = config_dir / "context.yaml"
    
    try:
        import yaml
        with context_file.open('w') as f:
            yaml.dump(context, f, default_flow_style=False)
    except Exception as e:
        raise click.ClickException(f"Failed to save session context: {e}")


@click.group()
def profile():
    """Manage AI Context Manager selection profiles."""
    pass


@profile.command()
@click.argument('name')
@click.option('--description', prompt='Description', help='Description of the profile')
@click.option('--base-path', type=click.Path(path_type=Path), help='Base path for the profile')
def create(name: str, description: str, base_path: Optional[Path]):
    """Create a new selection profile from current session."""
    profile_manager = get_profile_manager()
    
    if profile_manager.profile_exists(name):
        click.echo(f"Profile '{name}' already exists.")
        return
    
    # Load current session context
    session_context = load_session_context()
    files = session_context.get("files", [])
    
    if not files:
        click.echo("No files in current session to create profile from.")
        return
    
    # Create new profile
    new_profile = Profile(
        name=name,
        description=description,
        created=datetime.now(),
        modified=datetime.now(),
        base_path=base_path or Path.cwd(),
        paths=[],
        exclude_patterns=[]
    )
    
    # Add files as PathEntry objects
    for file_path in files:
        path = Path(file_path)
        new_profile.add_path(path, is_directory=False, recursive=False)
    
    profile_manager.save_profile(new_profile)
    click.echo(f"Profile '{name}' created successfully with {len(files)} files!")


@profile.command()
def list():
    """List all selection profiles."""
    profile_manager = get_profile_manager()
    profiles = profile_manager.list_profiles()
    
    if not profiles:
        click.echo("No profiles found.")
        return
    
    click.echo("Available profiles:")
    for profile_name in profiles:
        profile = profile_manager.get_profile(profile_name)
        if profile:
            click.echo(f"  {profile.name}: {profile.description}")


@profile.command()
@click.argument('name')
def show(name: str):
    """Show details of a specific profile."""
    profile_manager = get_profile_manager()
    profile = profile_manager.get_profile(name)
    
    if not profile:
        click.echo(f"Profile '{name}' not found.")
        return
    
    click.echo(f"Profile: {profile.name}")
    click.echo(f"Description: {profile.description}")
    click.echo(f"Created: {profile.created}")
    click.echo(f"Modified: {profile.modified}")
    click.echo(f"Base path: {profile.base_path}")
    click.echo(f"Files ({len(profile.paths)}):")
    
    for entry in profile.paths:
        click.echo(f"  - {entry.path}")


@profile.command()
@click.argument('name')
def load(name: str):
    """Load a selection profile into current session."""
    profile_manager = get_profile_manager()
    profile = profile_manager.get_profile(name)
    
    if not profile:
        click.echo(f"Profile '{name}' not found.")
        return
    
    # Get all files from profile paths
    files = []
    for entry in profile.paths:
        if entry.is_directory:
            if entry.recursive:
                files.extend(str(p) for p in entry.path.rglob('*') if p.is_file())
            else:
                files.extend(str(p) for p in entry.path.iterdir() if p.is_file())
        else:
            if entry.path.exists():
                files.append(str(entry.path))
    
    # Save to session context
    session_context = {"files": files}
    save_session_context(session_context)
    
    click.echo(f"Profile '{name}' loaded successfully with {len(files)} files!")


@profile.command()
@click.argument('name')
def delete(name: str):
    """Delete a selection profile."""
    profile_manager = get_profile_manager()
    
    if not profile_manager.profile_exists(name):
        click.echo(f"Profile '{name}' not found.")
        return
    
    if click.confirm(f"Are you sure you want to delete profile '{name}'?"):
        if profile_manager.delete_profile(name):
            click.echo(f"Profile '{name}' deleted successfully!")
        else:
            click.echo(f"Failed to delete profile '{name}'.")


@profile.command()
@click.argument('name')
@click.option('--description', help='New description')
@click.option('--base-path', type=click.Path(path_type=Path), help='New base path')
def update(name: str, description: Optional[str], base_path: Optional[Path]):
    """Update an existing profile with current session."""
    profile_manager = get_profile_manager()
    profile = profile_manager.get_profile(name)
    
    if not profile:
        click.echo(f"Profile '{name}' not found.")
        return
    
    # Load current session context
    session_context = load_session_context()
    files = session_context.get("files", [])
    
    if not files:
        click.echo("No files in current session to update profile with.")
        return
    
    # Update profile with current session files
    profile.paths = []
    for file_path in files:
        path = Path(file_path)
        profile.add_path(path, is_directory=False, recursive=False)
    
    profile.modified = datetime.now()
    
    if description:
        profile.description = description
    if base_path:
        profile.base_path = base_path
    
    profile_manager.save_profile(profile)
    click.echo(f"Profile '{name}' updated successfully with {len(files)} files!")


@profile.command()
@click.option('--output', type=click.Path(path_type=Path), help='Output file path')
@click.argument('name')
def export(name: str, output: Optional[Path]):
    """Export a selection profile to JSON file."""
    profile_manager = get_profile_manager()
    profile = profile_manager.get_profile(name)
    
    if not profile:
        click.echo(f"Profile '{name}' not found.")
        return
    
    if output is None:
        output = Path(f"{profile.name}_profile.json")
    
    try:
        with output.open('w') as f:
            json.dump(profile.to_dict(), f, indent=2, default=str)
        click.echo(f"Profile exported to {output}")
    except Exception as e:
        click.echo(f"Failed to export profile: {e}", err=True)


@profile.command()
@click.argument('file_path', type=click.Path(exists=True, path_type=Path))
def import_profile(file_path: Path):
    """Import a selection profile from JSON file."""
    try:
        with file_path.open('r') as f:
            data = json.load(f)
        
        # Convert JSON data to Profile
        profile = Profile.from_dict(data)
        
        profile_manager = get_profile_manager()
        profile_manager.save_profile(profile)
        
        click.echo(f"Profile '{profile.name}' imported successfully!")
    except Exception as e:
        click.echo(f"Failed to import profile: {e}", err=True)


@profile.command()
@click.option('--backup-dir', type=click.Path(path_type=Path), help='Directory to backup old profiles')
def migrate(backup_dir: Optional[Path]):
    """Migrate old JSON export profiles to new YAML selection profiles."""
    config_dir = get_config_dir()
    old_profile_path = config_dir / "profile.json"
    
    if not old_profile_path.exists():
        click.echo("No old profile.json found to migrate.")
        return
    
    if backup_dir is None:
        backup_dir = config_dir / "backups"
    
    try:
        # Load old profile
        with old_profile_path.open('r') as f:
            old_data = json.load(f)
        
        # Create backup
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / f"profile_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        old_profile_path.rename(backup_path)
        
        click.echo(f"Old profile backed up to {backup_path}")
        click.echo("Migration completed. Old profiles are now in YAML format in profiles/ directory.")
        
    except Exception as e:
        click.echo(f"Migration failed: {e}", err=True)