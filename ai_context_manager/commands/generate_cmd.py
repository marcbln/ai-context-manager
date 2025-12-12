# ai_context_manager/commands/generate_cmd.py

"""Command to generate context via Repomix."""
import shutil
import subprocess
import typer
import yaml
import tempfile
import os
from pathlib import Path
from typing import Optional, List
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
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed execution info and repomix output"),
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

    raw_base = data.get("basePath", ".")
    # If basePath is absolute, resolve returns it. If relative, it resolves to CWD / relative.
    base_path = Path(raw_base).resolve()

    if verbose:
        console.print(f"[dim]Using Base Path: {base_path}[/dim]")

    if not base_path.exists():
         console.print(f"[red]Error: Base path {base_path} does not exist.[/red]")
         raise typer.Exit(1)

    # 1. Handle Output Path Logic
    if output is None:
        # Generate a temporary filename based on the selection file name to be identifiable
        sanitized_name = selection_file.stem.replace(" ", "_")
        temp_dir = Path(tempfile.gettempdir())
        ext = "md" if style == "markdown" else "xml" if style == "xml" else "txt"
        output = temp_dir / f"acm__{sanitized_name}.{ext}"
    
    # Force absolute path for output to avoid CWD confusion
    output = output.resolve()

    # Handle unified list + legacy support
    includes = data.get("include", [])
    includes.extend(data.get("files", []))
    includes.extend(data.get("folders", []))

    if not includes:
        console.print("[yellow]Warning: No paths found in selection.[/yellow]")
        raise typer.Exit(0)

    # 2. Validation & Pattern Construction
    if verbose:
        console.print(f"[dim]Processing {len(includes)} include entries...[/dim]")

    final_patterns = []
    missing_items = []
    
    # Helper to check if string contains glob characters
    def is_glob(s: str) -> bool:
        return any(c in s for c in "*?[]")

    for item in includes:
        # If it looks like a glob, pass it through to Repomix but try to check matches if verbose
        if is_glob(item):
            final_patterns.append(item)
            if verbose:
                matches = list(base_path.glob(item))
                if matches:
                    console.print(f"[dim]  Glob '{item}' matched {len(matches)} files[/dim]")
                else:
                    console.print(f"[yellow]  Glob '{item}' matched 0 files[/yellow]")
            continue
        
        # Explicit path check
        full_path = base_path / item
        if not full_path.exists():
            missing_items.append(item)
            if verbose:
                console.print(f"[yellow]  Missing: {item}[/yellow]")
        else:
            # If directory, append /** to ensure Repomix recurses
            if full_path.is_dir():
                final_patterns.append(f"{item}/**")
                if verbose:
                    console.print(f"[dim]  Dir: {item} -> {item}/**[/dim]")
            else:
                final_patterns.append(item)
                if verbose:
                    console.print(f"[dim]  File: {item}[/dim]")

    if missing_items:
        console.print(f"[yellow]Warning: {len(missing_items)} explicit paths in selection do not exist:[/yellow]")
        for item in missing_items:
            console.print(f"  - {item}")
    
    if not final_patterns:
        console.print("[red]Error: No valid patterns to pass to Repomix.[/red]")
        raise typer.Exit(1)

    cmd = [
        repomix_bin,
        "--output", str(output),
        "--style", style,
        "--include", ",".join(final_patterns),
    ]

    console.print(f"[blue]Running Repomix in {base_path}...[/blue]")
    if verbose:
        console.print(f"[dim]Command: {' '.join(cmd)}[/dim]")
        console.print(f"[dim]Output target: {output}[/dim]")

    try:
        # Run in base_path so relative includes work
        result = subprocess.run(cmd, cwd=base_path, capture_output=not verbose, text=True)
    except Exception as exc:
        console.print(f"[red]Execution error: {exc}[/red]")
        raise typer.Exit(1)

    if result.returncode == 0:
        # Verify output file existence
        if not output.exists():
             console.print(f"[red]Error: Repomix reported success, but output file is missing.[/red]")
             console.print(f"Expected at: {output}")
             
             # Fallback check: did it ignore absolute path and write relative to CWD?
             possible_rel = base_path / output.name
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