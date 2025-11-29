"""Debug command: build context from a stack trace."""

import sys
import re
from pathlib import Path
import typer
from rich.console import Console
from typing import List, Set, Tuple, Optional

from ..config import CLI_CONTEXT_SETTINGS
from .add_cmd import load_context, save_context
from ai_context_manager.core.profile import Profile, PathEntry
from ai_context_manager.core.exporter import ContextExporter
from datetime import datetime

app = typer.Typer(help="Create a debug context from a stack trace.", context_settings=CLI_CONTEXT_SETTINGS)
console = Console()


def _extract_paths(trace_text: str) -> List[str]:
    """Extract unique file paths from a stack trace-like text."""
    # Match paths ending with common source extensions, optionally followed by :<line> or ' line <num>'
    pattern = re.compile(
        r"(?P<path>[A-Za-z]:\\[\\\w .\-_/]+?\.(?:php|py|js|ts|jsx|tsx|java|rb|go|cs|c|cpp))(?::\d+)?|(?P<nixpath>[/~][\w@%:/.\-]+?\.(?:php|py|js|ts|jsx|tsx|java|rb|go|cs|c|cpp))(?:[: ]\d+|\s+line\s+\d+)?",
        re.IGNORECASE,
    )
    candidates: Set[str] = set()
    for m in pattern.finditer(trace_text):
        p = m.group("path") or m.group("nixpath")
        if not p:
            continue
        # Normalize backslashes to forward slashes for suffix matching
        p = p.replace("\\", "/")
        # Strip possible line info like :123
        p = re.sub(r":\d+$", "", p)
        candidates.add(p)
    return sorted(candidates)


def _resolve_against_base(extracted: List[str], base_path: Path) -> Tuple[List[str], List[str]]:
    """Resolve extracted trace paths to local files under base_path.
    Returns (resolved_abs_paths, unresolved_originals).
    """
    resolved: List[str] = []
    unresolved: List[str] = []
    base_path = base_path.resolve()

    for raw in extracted:
        suffix = raw
        # Keep only path suffix (remove drive letters or container-specific prefixes)
        # We try to match by tail segments, so we start with filename and verify suffix match
        filename = Path(suffix).name
        matches: List[Path] = list(base_path.rglob(filename))
        chosen: Optional[Path] = None
        if matches:
            # Prefer the one whose absolute path ends with the normalized suffix
            norm_suffix = suffix.replace("\\", "/")
            for cand in matches:
                cand_norm = str(cand.resolve()).replace("\\", "/")
                if cand_norm.endswith(norm_suffix):
                    chosen = cand
                    break
            # Fallback: choose the first match
            if chosen is None:
                chosen = matches[0]
        if chosen and chosen.is_file():
            resolved.append(str(chosen.resolve()))
        else:
            unresolved.append(raw)

    # Deduplicate while preserving order
    seen: Set[str] = set()
    dedup_resolved: List[str] = []
    for p in resolved:
        if p not in seen:
            seen.add(p)
            dedup_resolved.append(p)

    return dedup_resolved, unresolved


@app.command(name="from-trace")
def from_trace(
    base_path: Path = typer.Option(..., "--base-path", "-b", exists=True, file_okay=False, dir_okay=True, readable=True, help="Local project root used to resolve paths from the stack trace."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Optional output file to write a debug context (markdown)."),
    format: str = typer.Option("markdown", "--format", "-f", help="Export format: markdown, json, xml, yaml"),
):
    """
    Parses a stack trace from stdin to create a debug context.
    """
    if sys.stdin.isatty():
        console.print("[yellow]No input received on stdin. Pipe a stack trace, e.g.:[/yellow]")
        console.print("  cat crash.log | aicontext debug from-trace --base-path .")
        raise typer.Exit(1)

    trace_text = sys.stdin.read()
    if not trace_text.strip():
        console.print("[yellow]Empty input received on stdin.[/yellow]")
        raise typer.Exit(1)

    extracted = _extract_paths(trace_text)
    console.print(f"[bold]Found {len(extracted)} file path(s) in trace.[/bold]")

    resolved_files, unresolved = _resolve_against_base(extracted, base_path)

    if resolved_files:
        context = load_context()
        existing = set(context.get("files", []))
        new_files = [p for p in resolved_files if p not in existing]
        context["files"] = sorted(existing.union(new_files))
        save_context(context)

        console.print(f"[green]Adding {len(new_files)} file(s) to the session context:[/green]")
        for f in new_files:
            console.print(f"  + {f}")
        console.print(f"[green]Context now has {len(context['files'])} file(s).[/green]")
    else:
        console.print("[yellow]No files could be resolved locally from the trace.[/yellow]")

    if unresolved:
        console.print(f"[yellow]Unresolved paths ({len(unresolved)}):[/yellow]")
        for p in unresolved:
            console.print(f"  - {p}")

    # Optional direct export
    if output:
        console.print("\n[bold]Preparing export of resolved files...[/bold]")
        if not resolved_files:
            console.print("[yellow]No resolved files to export.[/yellow]")
            raise typer.Exit(1)

        profile_obj = Profile(
            name="debug-from-trace",
            description="Temporary profile generated from stack trace",
            created=datetime.now(),
            modified=datetime.now(),
            base_path=base_path.resolve(),
            paths=[PathEntry(path=Path(p), is_directory=False, recursive=False) for p in resolved_files],
            exclude_patterns=[],
        )
        exporter = ContextExporter(profile_obj)

        # Export to a temporary path first
        tmp_path = output.parent / (output.name + ".tmp")
        result = exporter.export_to_file(
            output_path=tmp_path,
            format=format,
            max_file_size=102400,
            include_binary=False,
        )
        if not result.get("success"):
            console.print(f"[red]Export failed: {result.get('message')}[/red]")
            raise typer.Exit(1)

        try:
            exported_content = tmp_path.read_text(encoding="utf-8")
        except Exception as e:
            console.print(f"[red]Failed to read temporary export: {e}[/red]")
            raise typer.Exit(1)

        if format.lower() == "markdown":
            combined = []
            combined.append("# Debug Context\n")
            combined.append("## Original Error Trace\n")
            combined.append("`````\n")
            combined.append(trace_text.rstrip("\n") + "\n")
            combined.append("`````\n\n")
            combined.append(exported_content)
            final_content = "".join(combined)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(final_content, encoding="utf-8")
            tmp_path.unlink(missing_ok=True)
            console.print(f"[green]✓ Wrote debug context to {output}[/green]")
        else:
            # For non-markdown, just move the file as-is
            output.parent.mkdir(parents=True, exist_ok=True)
            tmp_path.replace(output)
            console.print(f"[yellow]Note: Original trace prepending is only supported for markdown. Wrote exported {format} to {output}[/yellow]")
