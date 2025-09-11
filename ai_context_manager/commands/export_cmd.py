"""Export command for AI Context Manager."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ai_context_manager.core.profile import Profile
from ai_context_manager.core.exporter import ContextExporter
from ai_context_manager.utils.token_counter import check_token_limits, format_token_count
from ai_context_manager.config import CLI_CONTEXT_SETTINGS

app = typer.Typer(context_settings=CLI_CONTEXT_SETTINGS)
console = Console()


@app.command("export")
def export_context(
    output: Path = typer.Argument(..., help="Output file path"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile name to use"),
    format: str = typer.Option("markdown", "--format", "-f", help="Export format: markdown, json, xml, yaml"),
    max_size: int = typer.Option(102400, "--max-size", "-s", help="Maximum file size in bytes"),
    include_binary: bool = typer.Option(False, "--include-binary", "-b", help="Include binary files"),
    model: str = typer.Option("gpt-4", "--model", "-m", help="AI model for token limit checking"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be exported without creating file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed information"),
):
    """Export selected files to AI context format."""
    
    if not profile:
        console.print("[red]Error: No profile specified. Use --profile to select a profile.[/red]")
        raise typer.Exit(1)
    
    # Load profile
    try:
        profile_obj = Profile.load(profile)
    except FileNotFoundError:
        console.print(f"[red]Error: Profile '{profile}' not found.[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error loading profile: {e}[/red]")
        raise typer.Exit(1)
    
    # Validate format
    valid_formats = ["markdown", "json", "xml", "yaml"]
    if format.lower() not in valid_formats:
        console.print(f"[red]Error: Invalid format '{format}'. Valid formats: {', '.join(valid_formats)}[/red]")
        raise typer.Exit(1)
    
    # Create exporter
    exporter = ContextExporter(profile_obj)
    
    # Show what would be exported in dry-run mode
    if dry_run:
        console.print(f"\n[bold blue]Dry Run - Profile: {profile}[/bold blue]")
        
        # Get file selection
        selected_files = exporter.selector.select_files(
            max_file_size=max_size,
            include_binary=include_binary,
        )
        
        if not selected_files:
            console.print("[yellow]No files would be exported.[/yellow]")
            return
        
        # Show summary
        summary = exporter.selector.get_summary(selected_files)
        
        console.print(f"\n[bold]Would export {len(selected_files)} files:[/bold]")
        
        # Create file table
        table = Table(title="Files to Export")
        table.add_column("File", style="cyan")
        table.add_column("Size", justify="right", style="green")
        table.add_column("Lines", justify="right", style="blue")
        table.add_column("Language", style="magenta")
        
        for file_path in selected_files[:20]:  # Show first 20 files
            info = exporter.selector.file_utils.get_file_info(file_path)
            language = exporter._get_language_from_extension(file_path)
            table.add_row(
                str(file_path),
                info["size_human"],
                str(info["lines"]),
                language or "text"
            )
        
        if len(selected_files) > 20:
            table.add_row(
                f"... and {len(selected_files) - 20} more files",
                "", "", ""
            )
        
        console.print(table)
        
        # Show summary
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"Total files: {summary['total_files']}")
        console.print(f"Total size: {summary['total_size_human']}")
        console.print(f"Total lines: {summary['total_lines']:,}")
        
        # Check token limits
        from ai_context_manager.utils.token_counter import count_tokens
        estimated_content = exporter._export_markdown(selected_files, summary)
        tokens = count_tokens(estimated_content)
        formatted_tokens = format_token_count(tokens)
        
        console.print(f"Estimated tokens: {formatted_tokens}")
        
        # Check against model limits
        limit_check = check_token_limits(tokens, model)
        if limit_check["is_within_limits"]:
            console.print(f"[green]✓ Within {model} limits ({limit_check['percentage']:.1f}%)[/green]")
        else:
            console.print(f"[red]✗ Exceeds {model} limits ({limit_check['percentage']:.1f}%)[/red]")
        
        return
    
    # Perform actual export
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Exporting files...", total=None)
        
        result = exporter.export_to_file(
            output_path=output,
            format=format,
            max_file_size=max_size,
            include_binary=include_binary,
        )
    
    if result["success"]:
        console.print(f"\n[green]✓ {result['message']}[/green]")
        
        # Show summary
        console.print(f"\n[bold]Export Summary:[/bold]")
        console.print(f"Files exported: {len(result['files'])}")
        console.print(f"Total size: {result['total_size_human']}")
        console.print(f"Total tokens: {format_token_count(result['total_tokens'])}")
        
        # Check token limits
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
    formats = {
        "markdown": "GitHub-flavored markdown with code blocks",
        "json": "Structured JSON format with metadata",
        "xml": "XML format with hierarchical structure",
        "yaml": "YAML format with human-readable structure",
    }
    
    table = Table(title="Available Export Formats")
    table.add_column("Format", style="cyan")
    table.add_column("Description", style="white")
    
    for format_name, description in formats.items():
        table.add_row(format_name, description)
    
    console.print(table)


@app.command("models")
def list_models():
    """List AI models with token limits."""
    from ai_context_manager.utils.token_counter import get_token_limits
    
    table = Table(title="AI Model Token Limits")
    table.add_column("Model", style="cyan")
    table.add_column("Max Input", justify="right", style="green")
    table.add_column("Max Output", justify="right", style="blue")
    
    models = [
        "gpt-3.5-turbo",
        "gpt-4",
        "gpt-4-turbo",
        "gpt-4o",
        "claude-3-haiku",
        "claude-3-sonnet",
        "claude-3-opus",
        "claude-3.5-sonnet",
    ]
    
    for model in models:
        limits = get_token_limits(model)
        table.add_row(
            model,
            f"{limits['max_input']:,}",
            f"{limits['max_output']:,}",
        )
    
    console.print(table)


if __name__ == "__main__":
    app()