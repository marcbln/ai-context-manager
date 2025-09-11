"""Profile management commands for AI Context Manager."""
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

import typer
from datetime import datetime
from rich.console import Console

from ai_context_manager.core.profile import Profile, PathEntry, ProfileManager
from ai_context_manager.config import get_config_dir

app = typer.Typer(help="Manage AI Context Manager selection profiles.")
console = Console()


def get_profile_manager() -> ProfileManager:
    """Get the profile manager instance."""
    config_dir = get_config_dir()
    profiles_dir = config_dir / "profiles"
    profiles_dir.mkdir(exist_ok=True, parents=True)
    return ProfileManager(profiles_dir)


def load_session_context() -> Dict[str, Any]:
    """Load the current session context from YAML file."""
    config_dir = get_config_dir()
    context_file = config_dir / "context.yaml"

    if not context_file.exists():
        return {"files": []}

    try:
        import yaml

        with context_file.open("r") as f:
            return yaml.safe_load(f) or {"files": []}
    except Exception:
        return {"files": []}


def save_session_context(context: Dict[str, Any]) -> None:
    """Save the session context to YAML file."""
    config_dir = get_config_dir()
    context_file = config_dir / "context.yaml"

    try:
        import yaml

        with context_file.open("w") as f:
            yaml.dump(context, f, default_flow_style=False)
    except Exception as e:
        console.print(f"[red]Failed to save session context: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def create(
    name: str = typer.Argument(..., help="Name for the new profile."),
    description: str = typer.Option(..., prompt=True, help="Description of the profile."),
    base_path: Optional[Path] = typer.Option(
        None, help="Base path for the profile's relative paths."
    ),
):
    """Create a new selection profile from the current session."""
    profile_manager = get_profile_manager()

    if profile_manager.profile_exists(name):
        console.print(f"[yellow]Profile '{name}' already exists.[/yellow]")
        raise typer.Exit(1)

    session_context = load_session_context()
    files = session_context.get("files", [])

    if not files:
        console.print("[yellow]No files in current session to create a profile from.[/yellow]")
        raise typer.Exit(1)

    new_profile = Profile(
        name=name,
        description=description,
        created=datetime.now(),
        modified=datetime.now(),
        base_path=base_path or Path.cwd(),
        paths=[],
        exclude_patterns=[],
    )

    for file_path in files:
        path = Path(file_path)
        new_profile.paths.append(PathEntry(path=path, is_directory=False, recursive=False))

    profile_manager.save_profile(new_profile)
    console.print(f"[green]Profile '{name}' created successfully with {len(files)} files![/green]")


@app.command(name="list")
def list_profiles():
    """List all available selection profiles."""
    profile_manager = get_profile_manager()
    profiles = profile_manager.list_profiles()

    if not profiles:
        console.print("[yellow]No profiles found.[/yellow]")
        return

    console.print("[bold]Available profiles:[/bold]")
    for profile_name in profiles:
        profile = profile_manager.get_profile(profile_name)
        if profile:
            console.print(f"  [cyan]{profile.name}[/cyan]: {profile.description}")


@app.command()
def show(name: str = typer.Argument(..., help="The name of the profile to show.")):
    """Show details of a specific profile."""
    profile_manager = get_profile_manager()
    profile = profile_manager.get_profile(name)

    if not profile:
        console.print(f"[red]Profile '{name}' not found.[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]Profile:[/bold] [cyan]{profile.name}[/cyan]")
    console.print(f"  Description: {profile.description}")
    console.print(f"  Created:     {profile.created.isoformat()}")
    console.print(f"  Modified:    {profile.modified.isoformat()}")
    console.print(f"  Base path:   {profile.base_path}")
    console.print(f"  Paths ({len(profile.paths)}):")
    for entry in profile.paths:
        console.print(f"    - {entry.path} (dir: {entry.is_directory}, recursive: {entry.recursive})")


@app.command()
def load(name: str = typer.Argument(..., help="The name of the profile to load.")):
    """Load a selection profile into the current session."""
    profile_manager = get_profile_manager()
    profile = profile_manager.get_profile(name)

    if not profile:
        console.print(f"[red]Profile '{name}' not found.[/red]")
        raise typer.Exit(1)

    files = []
    base_path = profile.base_path or Path.cwd()
    for entry in profile.paths:
        entry_path = entry.path if entry.path.is_absolute() else base_path / entry.path
        if entry.is_directory:
            if entry.recursive:
                files.extend(str(p.resolve()) for p in entry_path.rglob("*") if p.is_file())
            else:
                files.extend(str(p.resolve()) for p in entry_path.iterdir() if p.is_file())
        elif entry_path.exists():
            files.append(str(entry_path.resolve()))

    session_context = {"files": sorted(list(set(files)))}
    save_session_context(session_context)
    console.print(f"[green]Profile '{name}' loaded successfully with {len(session_context['files'])} files![/green]")


@app.command()
def delete(name: str = typer.Argument(..., help="The name of the profile to delete.")):
    """Delete a selection profile."""
    profile_manager = get_profile_manager()

    if not profile_manager.profile_exists(name):
        console.print(f"[red]Profile '{name}' not found.[/red]")
        raise typer.Exit(1)

    if typer.confirm(f"Are you sure you want to delete profile '{name}'?"):
        if profile_manager.delete_profile(name):
            console.print(f"[green]Profile '{name}' deleted successfully![/green]")
        else:
            console.print(f"[red]Failed to delete profile '{name}'.[/red]")
            raise typer.Exit(1)


@app.command()
def update(
    name: str = typer.Argument(..., help="The profile to update."),
    description: Optional[str] = typer.Option(None, help="New description."),
    base_path: Optional[Path] = typer.Option(None, help="New base path."),
):
    """Update an existing profile with the current session."""
    profile_manager = get_profile_manager()
    profile = profile_manager.get_profile(name)

    if not profile:
        console.print(f"[red]Profile '{name}' not found.[/red]")
        raise typer.Exit(1)

    session_context = load_session_context()
    files = session_context.get("files", [])

    if not files:
        console.print("[yellow]No files in current session to update profile with.[/yellow]")
        raise typer.Exit(1)

    profile.paths = [PathEntry(path=Path(fp), is_directory=False, recursive=False) for fp in files]
    profile.modified = datetime.now()

    if description is not None:
        profile.description = description
    if base_path is not None:
        profile.base_path = base_path

    profile_manager.save_profile(profile)
    console.print(f"[green]Profile '{name}' updated successfully with {len(files)} files![/green]")


@app.command()
def export(
    name: str = typer.Argument(..., help="The name of the profile to export."),
    output: Optional[Path] = typer.Option(None, "-o", "--output", help="Output file path."),
):
    """Export a selection profile to a YAML file."""
    profile_manager = get_profile_manager()
    profile = profile_manager.get_profile(name)

    if not profile:
        console.print(f"[red]Profile '{name}' not found.[/red]")
        raise typer.Exit(1)

    if output is None:
        output = Path.cwd() / f"{profile.name}_profile.yaml"

    try:
        profile.save(output)
        console.print(f"[green]Profile exported to {output}[/green]")
    except Exception as e:
        console.print(f"[red]Failed to export profile: {e}[/red]")
        raise typer.Exit(1)


@app.command(name="import")
def import_profile(
    file_path: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to profile YAML file.",
    )
):
    """Import a selection profile from a YAML file."""
    try:
        profile = Profile.load(file_path)
        profile_manager = get_profile_manager()

        if profile_manager.profile_exists(profile.name):
            if not typer.confirm(f"Profile '{profile.name}' already exists. Overwrite?"):
                console.print("[yellow]Import cancelled.[/yellow]")
                raise typer.Exit()

        profile_manager.save_profile(profile)
        console.print(f"[green]Profile '{profile.name}' imported successfully![/green]")
    except Exception as e:
        console.print(f"[red]Failed to import profile: {e}[/red]")
        raise typer.Exit(1)