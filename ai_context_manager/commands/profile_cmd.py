"""Profile management commands for AI Context Manager."""
import json
from pathlib import Path
from typing import Dict, Any, Optional

import click

from ai_context_manager.core.profile import Profile
from ai_context_manager.config import DEFAULT_PROFILE_PATH


def load_profile(profile_path: Optional[Path] = None) -> Profile:
    """Load a profile from file."""
    if profile_path is None:
        profile_path = DEFAULT_PROFILE_PATH
    
    if not profile_path.exists():
        return Profile()
    
    try:
        with profile_path.open('r') as f:
            data = json.load(f)
        return Profile.from_dict(data)
    except (json.JSONDecodeError, IOError, OSError):
        return Profile()


def save_profile(profile: Profile, profile_path: Optional[Path] = None) -> None:
    """Save a profile to file."""
    if profile_path is None:
        profile_path = DEFAULT_PROFILE_PATH
    
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with profile_path.open('w') as f:
            json.dump(profile.to_dict(), f, indent=2)
    except (IOError, OSError) as e:
        raise click.ClickException(f"Failed to save profile: {e}")


@click.group()
def profile():
    """Manage AI Context Manager profiles."""
    pass


@profile.command()
@click.option('--name', prompt='Profile name', help='Name of the profile')
@click.option('--description', prompt='Description', help='Description of the profile')
@click.option('--include-patterns', help='Comma-separated include patterns')
@click.option('--exclude-patterns', help='Comma-separated exclude patterns')
@click.option('--max-file-size', type=int, help='Maximum file size in bytes')
@click.option('--include-binary/--no-include-binary', default=False, help='Include binary files')
@click.option('--output-format', type=click.Choice(['markdown', 'json', 'xml']), default='markdown')
@click.option('--languages', help='Comma-separated list of languages to include')
@click.option('--profile-path', type=click.Path(path_type=Path), help='Custom profile path')
def create(name: str, description: str, include_patterns: str, exclude_patterns: str,
           max_file_size: int, include_binary: bool, output_format: str, languages: str,
           profile_path: Optional[Path]):
    """Create a new profile."""
    profile_obj = load_profile(profile_path)
    
    new_profile = Profile(
        name=name,
        description=description,
        include_patterns=include_patterns.split(',') if include_patterns else None,
        exclude_patterns=exclude_patterns.split(',') if exclude_patterns else None,
        max_file_size=max_file_size,
        include_binary=include_binary,
        output_format=output_format,
        languages=languages.split(',') if languages else None
    )
    
    profile_obj = new_profile
    save_profile(profile_obj, profile_path)
    
    click.echo(f"Profile '{name}' created successfully!")


@profile.command()
@click.option('--profile-path', type=click.Path(path_type=Path), help='Custom profile path')
def list(profile_path: Optional[Path]):
    """List all profiles."""
    profile_obj = load_profile(profile_path)
    
    if not profile_obj.name:
        click.echo("No profiles found.")
        return
    
    click.echo(f"Profile: {profile_obj.name}")
    click.echo(f"Description: {profile_obj.description}")
    click.echo(f"Include patterns: {', '.join(profile_obj.include_patterns or ['*'])}")
    click.echo(f"Exclude patterns: {', '.join(profile_obj.exclude_patterns or [])}")
    click.echo(f"Max file size: {profile_obj.max_file_size}")
    click.echo(f"Include binary: {profile_obj.include_binary}")
    click.echo(f"Output format: {profile_obj.output_format}")
    click.echo(f"Languages: {', '.join(profile_obj.languages or [])}")


@profile.command()
@click.argument('name')
@click.option('--profile-path', type=click.Path(path_type=Path), help='Custom profile path')
def show(name: str, profile_path: Optional[Path]):
    """Show details of a specific profile."""
    profile_obj = load_profile(profile_path)
    
    if profile_obj.name != name:
        click.echo(f"Profile '{name}' not found.")
        return
    
    click.echo(json.dumps(profile_obj.to_dict(), indent=2))


@profile.command()
@click.argument('name')
@click.option('--profile-path', type=click.Path(path_type=Path), help='Custom profile path')
def delete(name: str, profile_path: Optional[Path]):
    """Delete a profile."""
    profile_obj = load_profile(profile_path)
    
    if profile_obj.name != name:
        click.echo(f"Profile '{name}' not found.")
        return
    
    if click.confirm(f"Are you sure you want to delete profile '{name}'?"):
        profile_obj = Profile()  # Reset to default
        save_profile(profile_obj, profile_path)
        click.echo(f"Profile '{name}' deleted successfully!")


@profile.command()
@click.argument('name')
@click.option('--include-patterns', help='Comma-separated include patterns')
@click.option('--exclude-patterns', help='Comma-separated exclude patterns')
@click.option('--max-file-size', type=int, help='Maximum file size in bytes')
@click.option('--include-binary/--no-include-binary', default=None, help='Include binary files')
@click.option('--output-format', type=click.Choice(['markdown', 'json', 'xml']), help='Output format')
@click.option('--languages', help='Comma-separated list of languages to include')
@click.option('--profile-path', type=click.Path(path_type=Path), help='Custom profile path')
def update(name: str, include_patterns: str, exclude_patterns: str, max_file_size: int,
           include_binary: bool, output_format: str, languages: str, profile_path: Optional[Path]):
    """Update an existing profile."""
    profile_obj = load_profile(profile_path)
    
    if profile_obj.name != name:
        click.echo(f"Profile '{name}' not found.")
        return
    
    if include_patterns is not None:
        profile_obj.include_patterns = include_patterns.split(',') if include_patterns else []
    if exclude_patterns is not None:
        profile_obj.exclude_patterns = exclude_patterns.split(',') if exclude_patterns else []
    if max_file_size is not None:
        profile_obj.max_file_size = max_file_size
    if include_binary is not None:
        profile_obj.include_binary = include_binary
    if output_format is not None:
        profile_obj.output_format = output_format
    if languages is not None:
        profile_obj.languages = languages.split(',') if languages else []
    
    save_profile(profile_obj, profile_path)
    click.echo(f"Profile '{name}' updated successfully!")


@profile.command()
@click.option('--profile-path', type=click.Path(path_type=Path), help='Custom profile path')
@click.option('--output', type=click.Path(path_type=Path), help='Output file path')
def export(profile_path: Optional[Path], output: Optional[Path]):
    """Export profile configuration to a file."""
    profile_obj = load_profile(profile_path)
    
    if not profile_obj.name:
        click.echo("No profile to export.")
        return
    
    if output is None:
        output = Path(f"{profile_obj.name}_profile.json")
    
    try:
        with output.open('w') as f:
            json.dump(profile_obj.to_dict(), f, indent=2)
        click.echo(f"Profile exported to {output}")
    except (IOError, OSError) as e:
        click.echo(f"Failed to export profile: {e}", err=True)


@profile.command()
@click.argument('file_path', type=click.Path(exists=True, path_type=Path))
@click.option('--profile-path', type=click.Path(path_type=Path), help='Custom profile path')
def import_profile(file_path: Path, profile_path: Optional[Path]):
    """Import profile configuration from a file."""
    try:
        with file_path.open('r') as f:
            data = json.load(f)
        
        profile_obj = Profile.from_dict(data)
        save_profile(profile_obj, profile_path)
        click.echo(f"Profile '{profile_obj.name}' imported successfully!")
    except (json.JSONDecodeError, IOError, OSError) as e:
        click.echo(f"Failed to import profile: {e}", err=True)