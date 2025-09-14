"""Export command for AI Context Manager."""

from pathlib import Path
from typing import Optional, List, Any, Dict
from datetime import datetime

import typer
import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ai_context_manager.core.profile import Profile, PathEntry
from ai_context_manager.core.exporter import ContextExporter
from ai_context_manager.utils.token_counter import check_token_limits, format_token_count
from ai_context_manager.config import CLI_CONTEXT_SETTINGS, get_config_dir

app = typer.Typer(context_settings=CLI_CONTEXT_SETTINGS)
console = Console()


def load_session_context() -> Dict[str, Any]:
    """Load the current session context from a YAML file."""
    config_dir = get_config_dir()
    context_file = config_dir / "context.yaml"
    if not context_file.exists():
        return {"files": []}
    with open(context_file, 'r') as f:
        return yaml.safe_load(f) or {"files": []}


@app.command("export")
def export_context(
    output: Path = typer.Argument(..., help="Output file path"),
    profile_name: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile name to use. If not provided, exports the current session."),
    format: str = typer.Option("markdown", "--format", "-f", help="Export format: markdown, json, xml, yaml"),
    max_size: int = typer.Option(102400, "--max-size", "-s", help="Maximum file size in bytes"),
    include_binary: bool = typer.Option(False, "--include-binary", "-b", help="Include binary files"),
    model: str = typer.Option("gpt-4", "--model", "-m", help="AI model for token limit checking"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be exported without creating file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed information"),
):
    """Export selected files to an AI context format from a profile or the current session."""
    
    profile_obj: Profile
    
    if profile_name:
        try:
            profile_obj = Profile.load(profile_name)
        except FileNotFoundError:
            console.print(f"[red]Error: Profile '{profile_name}' not found.[/red]")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[red]Error loading profile: {e}[/red]")
            raise typer.Exit(1)
    else:
        # Create a temporary profile from the current session
        session_context = load_session_context()
        session_files = session_context.get("files", [])
        if not session_files:
            console.print("[yellow]No files in the current session to export. Use 'aicontext add' to add files.[/yellow]")
            raise typer.Exit()
        
        profile_obj = Profile(
            name="current-session",
            created=datetime.now(),
            modified=datetime.now(),
            base_path=Path.cwd(),
            paths=[PathEntry(path=Path(f), is_directory=False, recursive=False) for f in session_files],
            exclude_patterns=[]
        )
        profile_name = "current session" # For display purposes

    # Validate format
    valid_formats = ["markdown", "json", "xml", "yaml"]
    if format.lower() not in valid_formats:
        console.print(f"[red]Error: Invalid format '{format}'. Valid formats: {', '.join(valid_formats)}[/red]")
        raise typer.Exit(1)
    
    exporter = ContextExporter(profile_obj)
    
    if dry_run:
        console.print(f"\n[bold blue]Dry Run - Using: {profile_name}[/bold blue]")
        selected_files = exporter.selector.select_files(
            max_file_size=max_size,
            include_binary=include_binary,
        )
        if not selected_files:
            console.print("[yellow]No files would be exported.[/yellow]")
            return
            
        summary = exporter.selector.get_summary(selected_files)
        console.print(f"\n[bold]Would export {len(selected_files)} files:[/bold]")
        
        from ai_context_manager.utils.token_counter import count_tokens
        estimated_content = exporter._export_markdown(selected_files, summary)
        tokens = count_tokens(estimated_content)
        formatted_tokens = format_token_count(tokens)
        
        console.print(f"Estimated tokens: {formatted_tokens}")
        limit_check = check_token_limits(tokens, model)
        if limit_check["is_within_limits"]:
            console.print(f"[green]✓ Within {model} limits ({limit_check['percentage']:.1f}%)[/green]")
        else:
            console.print(f"[red]✗ Exceeds {model} limits ({limit_check['percentage']:.1f}%)[/red]")
        return
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Exporting files...", total=None)
        
        result = exporter.export_to_file(
            output_path=output,
            format=format,
            max_file_size=max_size,
            include_binary=include_binary,
        )
    
    if result["success"]:
        console.print(f"\n[green]✓ {result['message']}[/green]")
        console.print(f"\n[bold]Export Summary:[/bold]")
        console.print(f"Files exported: {len(result['files'])}")
        console.print(f"Total size: {result['total_size_human']}")
        console.print(f"Total tokens: {format_token_count(result['total_tokens'])}")
        
        limit_check = check_token_limits(result["total_tokens"], model)
        if limit_check["is_within_limits"]:
            console.print(f"[green]✓ Within {model} limits ({limit_check['percentage']:.1f}%)[/green]")
        else:
            console.print(f"[red]✗ Exceeds {model} limits ({limit_check['percentage']:.1f}%)[/red]")
            console.print(f"[yellow]Consider using a model with higher limits or reducing file selection.[/yellow]")
        
        if verbose:
            console.print(f"\n[dim]Output file: {result['output_path']}[/dim]")
    else:
        console.print(f"\n[red]✗ Export failed: {result['message']}[/red]")
        raise typer.Exit(1)

@app.command("formats")
def list_formats():
    """List available export formats."""
    # This command remains unchanged
    ...

@app.command("models")
def list_models():
    """List AI models with token limits."""
    # This command remains unchanged
    ...

if __name__ == "__main__":
    app()