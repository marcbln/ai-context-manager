---
filename: "ai-plans/251215__IMPLEMENTATION_PLAN__print-metadata-in-generate.md"
title: "Support Multi-Document YAML and Print Metadata in Generate Command"
createdAt: 2025-12-15 00:16
updatedAt: 2025-12-15 00:16
status: draft
priority: medium
tags: [cli, ux, yaml, metadata]
estimatedComplexity: moderate
documentType: IMPLEMENTATION_PLAN
---

# Support Multi-Document YAML and Print Metadata in Generate Command

## Problem Description
The `aicontext generate repomix` command currently expects a single-document YAML structure containing `basePath` and `include`. However, the project has evolved to use multi-document YAML files (separated by `---`) where the first document contains metadata (frontmatter like `description`, `createdAt`) and the second document contains the actual context definition (`content`).

Currently, `yaml.safe_load` only reads the first document. If the file starts with metadata, the command fails to find `basePath`. Additionally, the user requested that this metadata be printed to the console to provide context about what is being generated.

## Phase 1: Update Generate Command Logic

**Objective:** Modify `ai_context_manager/commands/generate_cmd.py` to support multi-document YAML streams, normalize the data structure, and print metadata to the console using `rich`.

### [MODIFY] `ai_context_manager/commands/generate_cmd.py`

**Changes:**
1.  Add `_print_metadata` helper function.
2.  Add `_load_selection` helper function to handle `yaml.safe_load_all` and merge documents into a normalized structure (`{'meta': ..., 'content': ...}`).
3.  Refactor `generate_repomix` to use these helpers.

```python
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
from rich.panel import Panel

from ..config import CLI_CONTEXT_SETTINGS
from ..utils.clipboard import copy_file_uri_to_clipboard

app = typer.Typer(help="Generate context using repomix", context_settings=CLI_CONTEXT_SETTINGS)
console = Console()

def _print_metadata(meta: dict, filename: str) -> None:
    """Print extracted metadata to the console."""
    console.print(f"[bold blue]Processing: {filename}[/bold blue]")
    
    if "description" in meta:
        console.print(f"  Description: [green]{meta['description']}[/green]")
    
    if "updatedAt" in meta:
        by = f" by {meta['updatedBy']}" if "updatedBy" in meta else ""
        console.print(f"  Updated:     {meta['updatedAt']}{by}")
    elif "createdAt" in meta:
        # Fallback to created if updated is missing
        by = f" by {meta['createdBy']}" if "createdBy" in meta else ""
        console.print(f"  Created:     {meta['createdAt']}{by}")
        
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

    final_data = {"meta": {}, "content": {}}

    for doc in documents:
        if not isinstance(doc, dict):
            continue

        # Case A: Schema Compliant (single doc with meta/content keys)
        if "meta" in doc and "content" in doc:
            final_data = doc
            break

        # Case B: Content Definition (Flat or Wrapped)
        # Check if it looks like content (has content-specific keys)
        if "basePath" in doc or "include" in doc or "content" in doc:
            if "content" in doc and isinstance(doc["content"], dict):
                final_data["content"].update(doc["content"])
                # It might also have meta at top level
                if "meta" in doc:
                    final_data["meta"].update(doc["meta"])
            else:
                # Flat content (legacy or split file)
                final_data["content"].update(doc)
                
                # If legacy mixed keys exist, copy non-content keys to meta
                for k, v in doc.items():
                    if k not in ["basePath", "include", "content"]:
                        final_data["meta"][k] = v

        # Case C: Metadata Definition (Frontmatter style)
        # If it has metadata keys but NO content keys
        elif "description" in doc or "documentType" in doc or "createdAt" in doc:
            final_data["meta"].update(doc)

    return final_data

def _ensure_content(node: dict, field: str, file: Path) -> Any:
    if "content" not in node or field not in node["content"]:
        console.print(
            f"[red]Error: {file} does not match the required schema (missing content.{field}).[/red]"
        )
        raise typer.Exit(1)
    return node["content"][field]

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

    # Load first file to establish execution root
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
        
        # Print Metadata
        if data.get("meta"):
            _print_metadata(data["meta"], sel_file.name)

        raw_base = _ensure_content(data, "basePath", sel_file)
        include_items = _ensure_content(data, "include", sel_file)

        if Path(raw_base).is_absolute():
            current_base = Path(raw_base).resolve()
        else:
            current_base = (sel_file.parent / raw_base).resolve()

        if verbose:
            console.print(f"[dim]Processing includes from {sel_file} ({len(include_items)} entries)[/dim]")

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
```

## Phase 2: Create Report

**Objective**: Document the changes and provide verification steps.

### [NEW FILE] `ai-plans/251215__IMPLEMENTATION_REPORT__print-metadata-in-generate.md`

```yaml
---
filename: "ai-plans/251215__IMPLEMENTATION_REPORT__print-metadata-in-generate.md"
title: "Report: Support Multi-Document YAML and Print Metadata"
createdAt: 2025-12-15 00:20
updatedAt: 2025-12-15 00:20
plan_file: "ai-plans/251215__IMPLEMENTATION_PLAN__print-metadata-in-generate.md"
project: "ai-context-manager"
status: completed
files_created: 0
files_modified: 1
files_deleted: 0
tags: [cli, yaml, ux]
documentType: IMPLEMENTATION_REPORT
---

# Implementation Report: Support Multi-Document YAML and Print Metadata

## Summary
The `generate repomix` command has been upgraded to support multi-document YAML files (containing separate metadata and content blocks). It now extracts metadata such as `description`, `createdAt`, and `updatedAt` from these files and prints them to the console during execution, providing better context to the user.

## Files Changed
- **Modified**: `ai_context_manager/commands/generate_cmd.py`
  - Replaced `yaml.safe_load` with `yaml.safe_load_all` to handle multi-part files.
  - Added `_load_selection` to normalize data into a `meta`/`content` structure.
  - Added `_print_metadata` to display file info using Rich formatting.

## Key Changes
- **Multi-Document Support**: Can now parse files where metadata is separated from content by `---`.
- **UX Improvement**: The CLI now announces which files it is processing and shows their description and modification info.
- **Robust Loading**: Logic added to handle both schema-compliant JSON/YAML and legacy/flat YAML structures gracefully.

## Technical Decisions
- **Normalization Strategy**: Instead of strict schema validation at the CLI loading level, a normalization approach was taken to merge multi-document streams into a single dictionary. This ensures backward compatibility with legacy single-doc files while supporting the new frontmatter style.
- **Rich Integration**: Used `console.print` with style tags for readable output.

## Testing Notes
1. **Verification**: Run `aicontext generate repomix /path/to/ai-docs__ALL.yaml`.
2. **Success Criteria**:
   - The command should not crash on `---` separated files.
   - The console should output "Description: ...", "Updated: ...".
   - The final Repomix generation should succeed.

## Usage Examples
```bash
> aicontext generate repomix ai-docs.yaml
Processing: ai-docs.yaml
  Description: Main Documentation Context
  Updated:     2025-12-14 by User

Running Repomix in /path/to/project...
Success! Context generated at: /tmp/acm__ai-docs.xml
```

