# ai_context_manager/commands/generate_cmd.py

"""Command to generate context via Repomix."""
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, List, Optional, Set

import typer
import yaml
from rich.console import Console
from rich.table import Table

from ..config import CLI_CONTEXT_SETTINGS
from ..utils.clipboard import copy_file_uri_to_clipboard

app = typer.Typer(help="Generate context using repomix", context_settings=CLI_CONTEXT_SETTINGS)
console = Console()

_METADATA_HINT_KEYS = {
    "description",
    "documentType",
    "createdAt",
    "createdBy",
    "updatedAt",
    "updatedBy",
    "tags",
    "owners",
    "project",
}


def _count_files_and_folders(include_items: List[str], base_path: Path) -> tuple[int, int]:
    """
    Count files and folders in a selection's include list.
    Returns: (file_count, folder_count)
    """
    file_count = 0
    folder_count = 0
    
    for item in include_items:
        path_obj = Path(item)
        full_path = path_obj if path_obj.is_absolute() else (base_path / path_obj).resolve()
        
        if not full_path.exists():
            continue
            
        if full_path.is_file():
            file_count += 1
        elif full_path.is_dir():
            folder_count += 1
    
    return file_count, folder_count


def _format_path(path: Path, is_dir: bool, highlight: str) -> str:
    """
    Return a Rich-formatted string for an absolute path with optional directory suffix.
    """
    suffix = "/" if is_dir else ""
    return f"[{highlight}]{path}{suffix}[/{highlight}]"


def _print_metadata(
    meta: dict,
    filename: str,
    file_count: int = 0,
    folder_count: int = 0,
    absolute_path: Optional[Path] = None,
) -> None:
    """Print extracted metadata to the console."""
    meta = meta or {}

    console.print(f"[bold blue]Processing: {filename}[/bold blue]")
    if absolute_path:
        console.print(f"  File Path: {_format_path(absolute_path, absolute_path.is_dir(), 'magenta')}")

    description = meta.get("description")
    if description:
        console.print(f"  Description: [green]{description}[/green]")

    tags = meta.get("tags", [])
    if tags:
        console.print(f"  Tags:        {', '.join(tags)}")

    related = meta.get("relatedTags", [])
    if related:
        console.print(f"  See Also:    [italic cyan]{', '.join(related)}[/italic cyan]")

    if "updatedAt" in meta:
        by = f" by {meta['updatedBy']}" if meta.get("updatedBy") else ""
        console.print(f"  Updated:     {meta['updatedAt']}{by}")
    elif "createdAt" in meta:
        by = f" by {meta['createdBy']}" if meta.get("createdBy") else ""
        console.print(f"  Created:     {meta['createdAt']}{by}")

    # Show file/folder counts if provided
    if file_count > 0 or folder_count > 0:
        console.print(f"  Files:       [cyan]{file_count}[/cyan]")
        console.print(f"  Folders:     [cyan]{folder_count}[/cyan]")

    console.print()


def _load_selection(path: Path) -> dict:
    """
    Load YAML, handling multi-document streams (Metadata + Content).
    Returns normalized dict: {'meta': {}, 'content': {}}
    """
    try:
        with open(path, "r", encoding="utf-8") as file:
            documents = list(yaml.safe_load_all(file))
    except Exception as exc:
        console.print(f"[red]Error parsing {path}: {exc}[/red]")
        raise typer.Exit(1)

    final_data: dict[str, dict[str, Any]] = {"meta": {}, "content": {}}

    for doc in documents:
        if not isinstance(doc, dict):
            continue

        if "meta" in doc and "content" in doc:
            meta_section = doc.get("meta") or {}
            content_section = doc.get("content") or {}
            final_data["meta"] = dict(meta_section) if isinstance(meta_section, dict) else {}
            final_data["content"] = dict(content_section) if isinstance(content_section, dict) else {}
            break

        has_content_keys = any(key in doc for key in ("basePath", "include", "content"))
        if has_content_keys:
            if isinstance(doc.get("content"), dict):
                final_data["content"].update(doc["content"])
                if isinstance(doc.get("meta"), dict):
                    final_data["meta"].update(doc["meta"])
            else:
                for key, value in doc.items():
                    if key == "meta":
                        if isinstance(value, dict):
                            final_data["meta"].update(value)
                        continue
                    final_data["content"][key] = value
                for key, value in doc.items():
                    if key not in {"basePath", "include", "content", "meta"}:
                        final_data["meta"][key] = value
            continue

        meta_payload = doc.get("meta")
        if isinstance(meta_payload, dict):
            final_data["meta"].update(meta_payload)
        else:
            if _METADATA_HINT_KEYS.intersection(doc.keys()):
                final_data["meta"].update(doc)

    return final_data


def _ensure_content(node: dict, field: str, file: Path) -> Any:
    if "content" not in node or field not in node["content"]:
        console.print(
            f"[red]Error: {file} does not match the required schema (missing content.{field}).[/red]"
        )
        raise typer.Exit(1)
    return node["content"][field]


def _find_files_by_tags(directory: Path, tags: List[str], verbose: bool = False) -> List[Path]:
    """
    Scan a directory and return YAML files whose meta.tags intersect the requested tags.
    """
    matches: List[Path] = []
    required_tags: Set[str] = set(tags)

    if not directory.exists() or not directory.is_dir():
        console.print(f"[red]Error: Directory {directory} not found.[/red]")
        raise typer.Exit(1)

    candidates = list(directory.glob("*.yaml")) + list(directory.glob("*.yml"))

    if verbose:
        console.print(
            f"[dim]Scanning {len(candidates)} files in {directory} for tags: {', '.join(tags)}[/dim]"
        )

    for file_path in candidates:
        try:
            data = _load_selection(file_path)
        except Exception as exc:
            if verbose:
                console.print(
                    f"[yellow]  ⚠ Skipping {file_path.name}: Parsing error ({exc})[/yellow]"
                )
            continue

        file_meta = data.get("meta", {})
        raw_tags = file_meta.get("tags", [])
        if not isinstance(raw_tags, list):
            raw_tags = []
        file_tags = set(raw_tags)

        if verbose:
            tag_str = ", ".join(sorted(file_tags)) if file_tags else "<none>"
            if required_tags.isdisjoint(file_tags):
                console.print(
                    f"[dim]  • {file_path.name}: [yellow]No match[/yellow] (Found: {tag_str})[/dim]"
                )
            else:
                console.print(
                    f"[dim]  • {file_path.name}: [green]Match[/green] (Found: {tag_str})[/dim]"
                )

        if required_tags.isdisjoint(file_tags):
            continue

        matches.append(file_path)

    return sorted(matches)


@app.command("tags")
def list_available_tags(
    context_dir: Path = typer.Option(
        ..., "--dir", "-d", help="Directory to scan for context definitions", exists=True, file_okay=False
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show processing details"),
):
    """
    List all unique tags found in context definition files within a directory.
    """
    candidates = list(context_dir.glob("*.yaml")) + list(context_dir.glob("*.yml"))

    if not candidates:
        console.print(f"[yellow]No YAML files found in {context_dir}[/yellow]")
        raise typer.Exit(0)

    tag_counts = Counter()
    files_without_tags = 0

    if verbose:
        console.print(f"[dim]Scanning {len(candidates)} files...[/dim]")

    for file_path in candidates:
        try:
            data = _load_selection(file_path)
        except Exception as exc:
            if verbose:
                console.print(
                    f"[yellow]  ⚠ Skipping {file_path.name}: Parsing error ({exc})[/yellow]"
                )
            continue

        meta = data.get("meta", {})
        tags = meta.get("tags", [])

        if isinstance(tags, list) and tags:
            tag_counts.update(tags)
            if verbose:
                console.print(
                    f"[dim]  • {file_path.name}: Tags -> {', '.join(sorted(tags))}[/dim]"
                )
        else:
            files_without_tags += 1
            if verbose:
                console.print(f"[dim]  • {file_path.name}: [yellow]No tags[/yellow][/dim]")

    if not tag_counts:
        console.print(f"[yellow]No tags found in {len(candidates)} files.[/yellow]")
        if files_without_tags:
            console.print(f"[dim]({files_without_tags} files had no tags)[/dim]")
        return

    table = Table(title=f"Available Tags in {context_dir.name}")
    table.add_column("Tag", style="cyan")
    table.add_column("Count", style="green", justify="right")

    for tag, count in tag_counts.most_common():
        table.add_row(tag, str(count))

    console.print(table)

    if files_without_tags > 0:
        console.print(f"[dim]({files_without_tags} files had no tags)[/dim]")


@app.command("repomix")
def generate_repomix(
    selection_files: Optional[List[Path]] = typer.Argument(
        None, help="Specific selection YAML files"
    ),
    context_dir: Optional[Path] = typer.Option(
        None, "--dir", "-d", help="Directory to scan for context definitions"
    ),
    tags: Optional[List[str]] = typer.Option(
        None, "--tag", "-t", help="Tags to filter by (requires --dir)"
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output file. Defaults to a temp file if not set."
    ),
    style: str = typer.Option("xml", "--style", help="Repomix output style (xml, markdown, plain)"),
    copy: bool = typer.Option(
        False, "--copy", "-c", help="Copy the output file reference to system clipboard (requires xclip)."
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed execution info and repomix output"),
):
    """
    Execute repomix using selection files, or discover them via directory + tags.
    """
    # Validate style parameter
    valid_styles = {"xml", "markdown", "plain"}
    if style not in valid_styles:
        console.print(f"[red]Error: Invalid style '{style}'. Valid options are: {', '.join(sorted(valid_styles))}[/red]")
        raise typer.Exit(1)

    final_selection_files: List[Path] = []

    if selection_files:
        final_selection_files.extend(selection_files)

    if context_dir and tags:
        discovered = _find_files_by_tags(context_dir, tags, verbose)
        if not discovered:
            console.print(
                f"[yellow]No files found in {context_dir} matching tags: {', '.join(tags)}[/yellow]"
            )
            raise typer.Exit(1)
        final_selection_files.extend(discovered)
    elif context_dir and not tags:
        console.print("[red]Error: When using --dir, you must provide at least one --tag.[/red]")
        raise typer.Exit(1)

    if not final_selection_files:
        console.print("[red]Error: No selection files provided. Pass files or use --dir with --tag.[/red]")
        raise typer.Exit(1)

    # Deduplicate while keeping deterministic order
    final_selection_files = list(dict.fromkeys(final_selection_files))

    for file_path in final_selection_files:
        if not file_path.exists():
            console.print(f"[red]Error: {file_path} not found.[/red]")
            raise typer.Exit(1)

    repomix_bin = shutil.which("repomix")
    if not repomix_bin:
        console.print("[red]Error: 'repomix' not found. Run: npm install -g repomix[/red]")
        raise typer.Exit(1)

    first_data = _load_selection(final_selection_files[0])
    execution_root = Path(_ensure_content(first_data, "basePath", final_selection_files[0])).resolve()

    if verbose:
        console.print(f"[dim]Using Base Path: {execution_root}[/dim]")

    if not execution_root.exists():
        console.print(f"[red]Error: Base path {execution_root} does not exist.[/red]")
        raise typer.Exit(1)

    # 1. Handle Output Path Logic
    if output is None:
        if tags:
            sanitized_name = f"context_{'_'.join(tags)}"
        else:
            primary_file = final_selection_files[0]
            sanitized_name = primary_file.stem.replace(" ", "_")
            if len(final_selection_files) > 1:
                sanitized_name = f"{sanitized_name}_merged"
        temp_dir = Path(tempfile.gettempdir())
        ext = "md" if style == "markdown" else "xml" if style == "xml" else "txt"
        output = temp_dir / f"acm__{sanitized_name}.{ext}"

    output = output.resolve()

    final_patterns: List[str] = []

    for sel_file in final_selection_files:
        sel_absolute_path = sel_file.resolve()
        data = _load_selection(sel_file)

        if data.get("meta"):
            # Compute file/folder counts
            include_items = _ensure_content(data, "include", sel_file)
            raw_base = _ensure_content(data, "basePath", sel_file)
            
            if Path(raw_base).is_absolute():
                current_base = Path(raw_base).resolve()
            else:
                current_base = (sel_file.parent / raw_base).resolve()
            
            file_count, folder_count = _count_files_and_folders(include_items, current_base)
            _print_metadata(
                data["meta"],
                sel_file.name,
                file_count,
                folder_count,
                sel_absolute_path,
            )
        else:
            _print_metadata({}, sel_file.name, absolute_path=sel_absolute_path)

        raw_base = _ensure_content(data, "basePath", sel_file)
        include_items = _ensure_content(data, "include", sel_file)

        if Path(raw_base).is_absolute():
            current_base = Path(raw_base).resolve()
        else:
            current_base = (sel_file.parent / raw_base).resolve()

        if verbose:
            console.print(f"[dim]Processing {sel_file} ({len(include_items)} entries)[/dim]")

        include_details: List[tuple[Path, bool]] = []

        for item in include_items:
            path_obj = Path(item)
            full_path = path_obj if path_obj.is_absolute() else (current_base / path_obj).resolve()
            is_dir = full_path.exists() and full_path.is_dir()
            include_details.append((full_path, is_dir))

            try:
                rel_path = full_path.relative_to(execution_root)
                pattern = rel_path.as_posix()
            except ValueError:
                pattern = full_path.as_posix()

            if is_dir:
                pattern = f"{pattern}/**"

            final_patterns.append(pattern)

        if verbose and include_details:
            console.print("  Includes:")
            for full_path, is_dir in include_details:
                style = "cyan" if is_dir else "green"
                console.print(f"    • {_format_path(full_path, is_dir, style)}")

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