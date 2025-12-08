"""Command to generate context via Repomix."""
import shutil
import subprocess
import typer
import yaml
from pathlib import Path
from rich.console import Console
from ..config import CLI_CONTEXT_SETTINGS

app = typer.Typer(help="Generate context using repomix", context_settings=CLI_CONTEXT_SETTINGS)
console = Console()

@app.command("repomix")
def generate_repomix(
    selection_file: Path = typer.Argument(..., help="Selection YAML file"),
    output: Path = typer.Option("repomix-output.xml", "--output", "-o", help="Output file"),
    style: str = typer.Option("xml", "--style", help="Repomix output style (xml, markdown, plain)"),
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
    else:
        console.print("[red]Repomix failed.[/red]")
        if result.stderr:
            console.print(result.stderr)
        raise typer.Exit(result.returncode)
