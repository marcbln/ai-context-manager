# ai_context_manager/commands/generate_cmd.py

"""Command to generate context via Repomix."""
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional

import typer
import yaml
from rich.console import Console

from ..config import CLI_CONTEXT_SETTINGS
from ..utils.clipboard import copy_file_uri_to_clipboard

app = typer.Typer(help="Generate context using repomix", context_settings=CLI_CONTEXT_SETTINGS)
console = Console()

@app.command("repomix")
def generate_repomix(
    selection_files: List[Path] = typer.Argument(..., help="One or more selection YAML files"),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output file. Defaults to a temp file if not set."
    ),
    style: str = typer.Option("xml", "--style", help="Repomix output style (xml, markdown, plain)"),
    copy: bool = typer.Option(
        False, "--copy", "-c", help="Copy the output file reference to system clipboard (requires xclip)."
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed execution info and repomix output"),
):
    """Execute repomix using the paths from one or more selection.yaml files."""
    for file_path in selection_files:
        if not file_path.exists():
            console.print(f"[red]Error: {file_path} not found.[/red]")
            raise typer.Exit(1)

    repomix_bin = shutil.which("repomix")
    if not repomix_bin:
        console.print("[red]Error: 'repomix' not found. Run: npm install -g repomix[/red]")
        raise typer.Exit(1)

    def _load_selection(path: Path) -> dict:
        try:
            with open(path, "r") as file:
                return yaml.safe_load(file) or {}
        except Exception as exc:
            console.print(f"[red]Error parsing {path}: {exc}[/red]")
            raise typer.Exit(1)

    first_data = _load_selection(selection_files[0])
    execution_root = Path(first_data.get("basePath", ".")).resolve()

    if verbose:
        console.print(f"[dim]Using Base Path: {execution_root}[/dim]")

    if not execution_root.exists():
        console.print(f"[red]Error: Base path {execution_root} does not exist.[/red]")
        raise typer.Exit(1)

    # 1. Handle Output Path Logic
    if output is None:
        primary_file = selection_files[0]
        sanitized_name = primary_file.stem.replace(" ", "_")
        if len(selection_files) > 1:
            sanitized_name = f"{sanitized_name}_merged"
        temp_dir = Path(tempfile.gettempdir())
        ext = "md" if style == "markdown" else "xml" if style == "xml" else "txt"
        output = temp_dir / f"acm__{sanitized_name}.{ext}"

    output = output.resolve()

    def _gather_includes(data: dict) -> List[str]:
        includes: List[str] = []
        for key in ("include", "files", "folders"):
            values = data.get(key) or []
            includes.extend(values)
        return includes

    final_patterns: List[str] = []

    for sel_file in selection_files:
        data = _load_selection(sel_file)
        current_base = Path(data.get("basePath", ".")).resolve()

        includes = _gather_includes(data)
        if verbose:
            console.print(f"[dim]Processing {sel_file} ({len(includes)} entries)[/dim]")

        for raw_item in includes:
            item = str(raw_item)
            path_obj = Path(item)
            if path_obj.is_absolute():
                full_path = path_obj
            else:
                full_path = (current_base / path_obj).resolve()

            is_dir = full_path.exists() and full_path.is_dir()

            try:
                rel_path = full_path.relative_to(execution_root)
                pattern = rel_path.as_posix()
            except ValueError:
                pattern = full_path.as_posix()

            if is_dir:
                pattern = f"{pattern}/**"

            final_patterns.append(pattern)

    unique_patterns = list(dict.fromkeys(final_patterns))

    if not unique_patterns:
        console.print("[yellow]Warning: No paths found in selections.[/yellow]")
        raise typer.Exit(0)

    cmd = [
        repomix_bin,
        "--output",
        str(output),
        "--style",
        style,
        "--include",
        ",".join(unique_patterns),
    ]

    console.print(f"[blue]Running Repomix in {execution_root}...[/blue]")
    if verbose:
        console.print(f"[dim]Command: {' '.join(cmd)}[/dim]")
        console.print(f"[dim]Output target: {output}[/dim]")

    try:
        result = subprocess.run(cmd, cwd=execution_root, capture_output=not verbose, text=True)
    except Exception as exc:
        console.print(f"[red]Execution error: {exc}[/red]")
        raise typer.Exit(1)

    if result.returncode == 0:
        # Verify output file existence
        if not output.exists():
            console.print(f"[red]Error: Repomix reported success, but output file is missing.[/red]")
            console.print(f"Expected at: {output}")

            # Fallback check: did it ignore absolute path and write relative to CWD?
            possible_rel = execution_root / output.name
            if possible_rel.exists():
                console.print(f"[yellow]Found file at {possible_rel}. Using it instead.[/yellow]")
                output = possible_rel
            else:
                raise typer.Exit(1)

        console.print(f"[green]Success! Context generated at: {output}[/green]")
        
        # 3. Handle Clipboard Logic
        if copy:
            if copy_file_uri_to_clipboard(output):
                console.print(f"[bold green]File URI copied to clipboard![/bold green]")
                console.print(f"[dim](Ready to paste into Claude/ChatGPT upload dialog)[/dim]")
    else:
        console.print("[red]Repomix failed.[/red]")
        if result.stderr:
            console.print(result.stderr)
        raise typer.Exit(result.returncode)