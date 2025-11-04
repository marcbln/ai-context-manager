"""Profile management commands for AI Context Manager."""
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

import typer
from datetime import datetime
from rich.console import Console

from ai_context_manager.core.profile import Profile, PathEntry, ProfileManager
from ai_context_manager.config import get_config_dir, CLI_CONTEXT_SETTINGS

app = typer.Typer(help="Manage AI Context Manager selection profiles.", context_settings=CLI_CONTEXT_SETTINGS)

__all__ = ['app', 'create_profile', 'list_profiles', 'show', 'load', 'delete_profile', 'update', 'export', 'import_profile']
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
def create_profile(
    name: str = typer.Argument(..., help="Name for the new profile."),
    paths: List[Path] = typer.Argument(..., help="File or directory paths to include in the profile."),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Description of the profile."),
    base_path: Optional[Path] = typer.Option(
        None, "--base-path", "-b", help="Base path for the profile's relative paths. Defaults to the current directory."
    ),
    exclude: Optional[List[str]] = typer.Option(
        None, "--exclude", "-e", help="Pattern to exclude files. Can be used multiple times."
    ),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON to stdout"),
):
    """Create a new selection profile directly from paths and patterns."""
    profile_manager = get_profile_manager()

    if profile_manager.profile_exists(name):
        if json_output:
            typer.echo(json.dumps({"success": False, "error": f"Profile '{name}' already exists."}))
            raise typer.Exit(1)
        console.print(f"[yellow]Profile '{name}' already exists. Use 'aicontext profile update' to modify.[/yellow]")
        raise typer.Exit(1)

    path_entries = []
    for p in paths:
        if not p.exists():
            if json_output:
                console.print(f"[yellow]Warning: Path does not exist and will be skipped: {p}[/yellow]", stderr=True)
            else:
                console.print(f"[yellow]Warning: Path does not exist and will be skipped: {p}[/yellow]")
            continue
        is_dir = p.is_dir()
        # Assume recursion is desired for directories, which is a sensible default.
        path_entries.append(PathEntry(path=p, is_directory=is_dir, recursive=is_dir))

    if not path_entries:
        if json_output:
            typer.echo(json.dumps({"success": False, "error": "No valid paths were provided to create the profile."}))
            raise typer.Exit(1)
        console.print("[red]Error: No valid paths were provided to create the profile.[/red]")
        raise typer.Exit(1)

    final_description = description
    if not final_description:
        final_description = f"Profile for '{name}' created on {datetime.now().strftime('%Y-%m-%d')}."

    new_profile = Profile(
        name=name,
        description=final_description,
        created=datetime.now(),
        modified=datetime.now(),
        base_path=base_path or Path.cwd(),
        paths=path_entries,
        exclude_patterns=exclude or [],
    )

    profile_manager.save_profile(new_profile)
    if json_output:
        typer.echo(json.dumps(new_profile.to_dict()))
        raise typer.Exit()
    console.print(f"[green]Profile '{name}' created successfully with {len(path_entries)} path entries![/green]")


@app.command(name="list")
def list_profiles(json_output: bool = typer.Option(False, "--json", help="Output results as JSON to stdout")):
    """List all available selection profiles."""
    profile_manager = get_profile_manager()
    profiles = profile_manager.list_profiles()

    if not profiles:
        if json_output:
            typer.echo(json.dumps({"profile_count": 0, "profiles": []}))
            raise typer.Exit()
        console.print("[yellow]No profiles found.[/yellow]")
        return

    if json_output:
        profile_objects = []
        for profile_name in profiles:
            profile = profile_manager.get_profile(profile_name)
            if profile:
                profile_objects.append(profile.to_dict())
        result = {"profile_count": len(profile_objects), "profiles": profile_objects}
        typer.echo(json.dumps(result))
        raise typer.Exit()
    
    console.print("[bold]Available profiles:[/bold]")
    for profile_name in profiles:
        profile = profile_manager.get_profile(profile_name)
        if profile:
            console.print(f"  [cyan]{profile.name}[/cyan]: {profile.description}")


@app.command()
def show(
    name: str = typer.Argument(..., help="The name of the profile to show."),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON to stdout"),
):
    """Show details of a specific profile."""
    profile_manager = get_profile_manager()
    profile = profile_manager.get_profile(name)

    if not profile:
        if json_output:
            typer.echo(json.dumps({"success": False, "error": f"Profile '{name}' not found."}))
            raise typer.Exit(1)
        console.print(f"[red]Profile '{name}' not found.[/red]")
        raise typer.Exit(1)

    if json_output:
        typer.echo(json.dumps(profile.to_dict()))
        raise typer.Exit()
    
    console.print(f"[bold]Profile:[/bold] [cyan]{profile.name}[/cyan]")
    console.print(f"  Description: {profile.description}")
    console.print(f"  Created:     {profile.created.isoformat()}")
    console.print(f"  Modified:    {profile.modified.isoformat()}")
    console.print(f"  Base path:   {profile.base_path}")
    console.print(f"  Paths ({len(profile.paths)}):")
    for entry in profile.paths:
        console.print(f"    - {entry.path} (dir: {entry.is_directory}, recursive: {entry.recursive})")


@app.command()
def load(
    name: str = typer.Argument(..., help="The name of the profile to load."),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON to stdout"),
):
    """Load a selection profile into the current session."""
    profile_manager = get_profile_manager()
    profile = profile_manager.get_profile(name)

    if not profile:
        if json_output:
            typer.echo(json.dumps({"success": False, "error": f"Profile '{name}' not found."}))
            raise typer.Exit(1)
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
    if json_output:
        typer.echo(json.dumps({
            "success": True,
            "loaded_profile": name,
            "context": {"file_count": len(session_context["files"]), "files": session_context["files"]},
        }))
        raise typer.Exit()
    console.print(f"[green]Profile '{name}' loaded successfully with {len(session_context['files'])} files![/green]")


@app.command()
def delete(
    name: str = typer.Argument(..., help="The name of the profile to delete."),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON to stdout"),
):
    """Delete a selection profile."""
    profile_manager = get_profile_manager()

    if not profile_manager.profile_exists(name):
        if json_output:
            typer.echo(json.dumps({"success": False, "error": f"Profile '{name}' not found."}))
            raise typer.Exit(1)
        console.print(f"[red]Profile '{name}' not found.[/red]")
        raise typer.Exit(1)

    if json_output:
        # Non-interactive deletion in JSON mode
        if profile_manager.delete_profile(name):
            typer.echo(json.dumps({"success": True, "message": f"Profile '{name}' deleted successfully!"}))
            raise typer.Exit()
        else:
            typer.echo(json.dumps({"success": False, "error": f"Failed to delete profile '{name}'."}))
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
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON to stdout"),
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
        if json_output:
            typer.echo(json.dumps({"success": False, "error": "No files in current session to update profile with."}))
            raise typer.Exit(1)
        console.print("[yellow]No files in current session to update profile with.[/yellow]")
        raise typer.Exit(1)

    profile.paths = [PathEntry(path=Path(fp), is_directory=False, recursive=False) for fp in files]
    profile.modified = datetime.now()

    if description is not None:
        profile.description = description
    if base_path is not None:
        profile.base_path = base_path

    profile_manager.save_profile(profile)
    if json_output:
        typer.echo(json.dumps(profile.to_dict()))
        raise typer.Exit()
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



