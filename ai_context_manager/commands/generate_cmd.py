# ai_context_manager/commands/generate_cmd.py

"""Command to generate context via Repomix."""
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, List, Optional

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

    def _wrap_content(content: dict) -> dict:
        return {"content": content}

    def _extract_content(doc: Any) -> Optional[dict]:
        if not isinstance(doc, dict):
            return None

        content = doc.get("content")
        if isinstance(content, dict):
            return _wrap_content(content)

        if "basePath" in doc or "include" in doc:
            return _wrap_content(doc)

        return None

    def _load_selection(path: Path) -> dict:
        try:
            with open(path, "r", encoding="utf-8") as file:
                documents = [doc for doc in yaml.safe_load_all(file)]
        except Exception as exc:
            console.print(f"[red]Error parsing {path}: {exc}[/red]")
            raise typer.Exit(1)

        # Prefer documents that contain the actual content definition
        for doc in documents:
            content = _extract_content(doc)
            if content:
                return content

        # Fallback: first dict document
        for doc in documents:
            if isinstance(doc, dict):
                return _wrap_content(doc)

        return {"content": {}}

    def _ensure_content(node: dict, field: str, file: Path) -> Any:
        if "content" not in node or field not in node["content"]:
            console.print(
                f"[red]Error: {file} does not match the required schema (missing content.{field}).[/red]"
            )
            raise typer.Exit(1)
        return node["content"][field]

    first_data = _load_selection(selection_files[0])
    execution_root = Path(_ensure_content(first_data, "basePath", selection_files[0])).resolve()

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

    final_patterns: List[str] = []

    for sel_file in selection_files:
        data = _load_selection(sel_file)

        raw_base = _ensure_content(data, "basePath", sel_file)
        include_items = _ensure_content(data, "include", sel_file)

        if Path(raw_base).is_absolute():
            current_base = Path(raw_base).resolve()
        else:
            current_base = (sel_file.parent / raw_base).resolve()

        if verbose:
            console.print(f"[dim]Processing {sel_file} ({len(include_items)} entries)[/dim]")

        for item in include_items:
            path_obj = Path(item)
            full_path = path_obj if path_obj.is_absolute() else (current_base / path_obj).resolve()
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