"""Command to generate context via repomix using a selection file."""

from pathlib import Path
import shutil
import subprocess

import typer
import yaml
from rich.console import Console

from ..config import CLI_CONTEXT_SETTINGS


app = typer.Typer(help="Generate context using repomix", context_settings=CLI_CONTEXT_SETTINGS)
console = Console()


@app.command("repomix")
def generate_repomix(
    selection_file: Path = typer.Argument(..., help="Selection YAML created by 'select'"),
    output: Path = typer.Option("repomix-output.xml", "--output", "-o", help="Final context output file"),
    style: str = typer.Option("xml", "--style", help="Repomix output style (xml, markdown, plain)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show repomix stdout/stderr"),
):
    """Execute repomix against the selected files/folders."""

    if not selection_file.exists():
        console.print(f"[red]Error: Selection file {selection_file} not found.[/red]")
        raise typer.Exit(1)

    repomix_bin = shutil.which("repomix")
    if not repomix_bin:
        console.print("[red]Error: 'repomix' executable not found in PATH.[/red]")
        console.print("Please install it via: [bold]npm install -g repomix[/bold]")
        raise typer.Exit(1)

    try:
        with open(selection_file, "r") as f:
            data = yaml.safe_load(f) or {}
    except Exception as exc:  # pragma: no cover - defensive
        console.print(f"[red]Error parsing YAML: {exc}[/red]")
        raise typer.Exit(1)

    base_path = Path(data.get("basePath", ".")).resolve()
    files = data.get("files", [])
    folders = data.get("folders", [])

    if not files and not folders:
        console.print("[yellow]Warning: No files or folders found in selection.[/yellow]")
        raise typer.Exit(0)

    include_patterns: list[str] = []
    include_patterns.extend(files)
    include_patterns.extend(f"{folder}/**" for folder in folders)

    includes_str = ",".join(include_patterns)
    cmd = [
        repomix_bin,
        "--output",
        str(output.resolve()),
        "--style",
        style,
        "--include",
        includes_str,
    ]

    console.print(f"[blue]Running Repomix in {base_path}...[/blue]")
    if verbose:
        console.print(f"[dim]Command: {' '.join(cmd)}[/dim]")

    try:
        result = subprocess.run(
            cmd,
            cwd=base_path,
            capture_output=not verbose,
            text=True,
            check=False,
        )
    except Exception as exc:  # pragma: no cover - defensive
        console.print(f"[red]Execution error: {exc}[/red]")
        raise typer.Exit(1)

    if result.returncode == 0:
        console.print(f"[green]Success! Context generated at: {output}[/green]")
    else:
        console.print("[red]Repomix failed:[/red]")
        if result.stderr:
            console.print(result.stderr)
        raise typer.Exit(result.returncode)
