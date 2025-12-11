"""Command to generate context via Repomix."""
import shutil
import subprocess
import typer
import yaml
import tempfile
from pathlib import Path
from typing import Optional
from rich.console import Console
from ..config import CLI_CONTEXT_SETTINGS
from ..utils.clipboard import copy_file_uri_to_clipboard

app = typer.Typer(help="Generate context using repomix", context_settings=CLI_CONTEXT_SETTINGS)
console = Console()

@app.command("repomix")
def generate_repomix(
    selection_file: Path = typer.Argument(..., help="Selection YAML file"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file. Defaults to a temp file if not set."),
    style: str = typer.Option("xml", "--style", help="Repomix output style (xml, markdown, plain)"),
    copy: bool = typer.Option(False, "--copy", "-c", help="Copy the output file reference to system clipboard (requires xclip)."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show repomix output"),
):
    """Execute repomix using the paths from selection.yaml."""
    if not selection_file.exists():
        console.print(f"[red]Error: {selection_file} not found.[/red]")
        raise typer.Exit(1)

    repomix_bin = shutil.which("repomix")
    if not repomix_bin:
        console.print("[red]Error: 'repomix' not found. Run: npm install -g repomix[/red]")
        raise typer.Exit(1)

    # 1. Handle Output Path Logic
    if output is None:
        # Generate a temporary filename based on the selection file name to be identifiable
        # e.g., /tmp/acm__my_selection.xml
        sanitized_name = selection_file.stem.replace(" ", "_")
        temp_dir = Path(tempfile.gettempdir())
        ext = "md" if style == "markdown" else "xml" if style == "xml" else "txt"
        output = temp_dir / f"acm__{sanitized_name}.{ext}"
        
        # Ensure we are not silently overwriting something critical (unlikely in tmp but good practice)
        # For this use case, overwriting previous temp context is actually desired behavior.

    try:
        with open(selection_file, "r") as f:
            data = yaml.safe_load(f) or {}
    except Exception as exc:
        console.print(f"[red]Error parsing YAML: {exc}[/red]")
        raise typer.Exit(1)

    base_path = Path(data.get("basePath", ".")).resolve()
    
    # Handle unified list + legacy support
    includes = data.get("include", [])
    includes.extend(data.get("files", []))
    includes.extend(data.get("folders", []))

    if not includes:
        console.print("[yellow]Warning: No paths found in selection.[/yellow]")
        raise typer.Exit(0)

    # Convert paths to repomix patterns
    # Repomix needs "folder/**" to recurse, but just "file.txt" for files.
    final_patterns = []
    for item in includes:
        full_path = base_path / item
        if full_path.is_dir():
            final_patterns.append(f"{item}/**")
        else:
            final_patterns.append(item)

    cmd = [
        repomix_bin,
        "--output", str(output.resolve()),
        "--style", style,
        "--include", ",".join(final_patterns),
    ]

    console.print(f"[blue]Running Repomix in {base_path}...[/blue]")
    if verbose:
        console.print(f"[dim]Command: {' '.join(cmd)}[/dim]")

    try:
        result = subprocess.run(cmd, cwd=base_path, capture_output=not verbose, text=True)
    except Exception as exc:
        console.print(f"[red]Execution error: {exc}[/red]")
        raise typer.Exit(1)

    if result.returncode == 0:
        console.print(f"[green]Success! Context generated at: {output}[/green]")
        
        # 2. Handle Clipboard Logic
        if copy:
            if copy_file_uri_to_clipboard(output):
                console.print(f"[bold green]File URI copied to clipboard![/bold green]")
                console.print(f"[dim](Ready to paste into Claude/ChatGPT upload dialog)[/dim]")
    else:
        console.print("[red]Repomix failed.[/red]")
        if result.stderr:
            console.print(result.stderr)
        raise typer.Exit(result.returncode)
