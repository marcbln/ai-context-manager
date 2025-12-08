# Implementation Plan: Visual Context Manager Refactor

## Problem Description
The current `ai-context-manager` codebase is over-engineered, relying on complex state management (sessions), regex/glob pattern matching, and profile configuration files. This complexity creates friction for the user.

The goal is to refactor the tool into a stateless, visual, two-step workflow:
1.  **Select**: Use a TUI to visually checkmark files and folders, saving the list to a simple YAML file (`selection.yaml`) using a unified `include` list.
2.  **Generate**: Create the context file using one of two engines:
    *   **Native (`export`)**: Python-based exporter (fast, token counting, multiple formats).
    *   **Repomix (`generate`)**: Wrapper around the `repomix` Node.js tool.

---

## Phase 1: Prune Deprecated Components

**Objective**: Remove state management, legacy profile logic, and unused commands to clean the slate.

1.  **Delete Command Files**:
    Delete the following files from `ai_context_manager/commands/`:
    *   `add_cmd.py`
    *   `remove_cmd.py`
    *   `list_cmd.py`
    *   `profile_cmd.py`
    *   `init_cmd.py`
    *   `import_cmd.py`
    *   *Note: Keep `select_cmd.py`, `export_cmd.py` (will modify), and `generate_cmd.py` (will modify).*

2.  **Delete Core Files**:
    Delete the following files from `ai_context_manager/core/`:
    *   `profile.py`
    *   `selector.py`

3.  **Update `ai_context_manager/commands/__init__.py`**:
    Overwrite with:
    ```python
    """Expose command interfaces."""
    # This file can be empty or just expose the modules if needed dynamically.
    ```

---

## Phase 2: Implement Unified Data Model

**Objective**: Create a lightweight model to handle the simplified `selection.yaml` structure.

1.  **Create `ai_context_manager/core/selection.py`**:

```python
"""
Simple data model for handling file selections.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import List
import yaml

@dataclass
class Selection:
    base_path: Path
    include_paths: List[Path]

    @classmethod
    def load(cls, yaml_path: Path) -> 'Selection':
        """Load selection from a YAML file."""
        if not yaml_path.exists():
            raise FileNotFoundError(f"Selection file not found: {yaml_path}")

        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        
        # Resolve base path
        raw_base = data.get('basePath')
        if raw_base:
            base = Path(raw_base).resolve()
        else:
            base = yaml_path.parent.resolve()
        
        # Load the unified list. 
        # Support legacy 'files'/'folders' for backward compat if needed, but prefer 'include'.
        raw_includes = data.get('include', [])
        
        # Merge legacy keys if they exist
        raw_includes.extend(data.get('files', []))
        raw_includes.extend(data.get('folders', []))

        # Convert to Path objects relative to base
        include_paths = [base / p for p in raw_includes]
        
        return cls(base_path=base, include_paths=include_paths)

    def resolve_all_files(self) -> List[Path]:
        """
        Flatten the selection into a distinct list of files.
        Checks filesystem to determine if a path is a file or directory.
        """
        final_list = []
        
        for path in self.include_paths:
            if not path.exists():
                continue

            if path.is_file():
                final_list.append(path)
            elif path.is_dir():
                # Recursively add all files in the directory
                for f in path.rglob("*"):
                    if f.is_file():
                        final_list.append(f)
                        
        # Deduplicate and sort
        return sorted(list(set(final_list)))
```

---

## Phase 3: Refactor Native Exporter

**Objective**: Update the `ContextExporter` to use the new `Selection` model instead of the deleted `Profile` model.

1.  **Modify `ai_context_manager/core/exporter.py`**:

```python
"""Export functionality for AI Context Manager."""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any
import datetime

from ai_context_manager.core.selection import Selection
from ai_context_manager.utils.file_utils import get_file_info
from ai_context_manager.utils.token_counter import count_tokens


class ContextExporter:
    """Handles exporting selected files to various formats for AI context."""
    
    def __init__(self, selection: Selection):
        """Initialize exporter with a selection object."""
        self.selection = selection
    
    def export_to_file(
        self,
        output_path: Path,
        format: str = "markdown",
    ) -> Dict[str, Any]:
        """Export selected files to the specified format."""
        
        # 1. Resolve files using the simplified logic
        files = self.selection.resolve_all_files()
        
        if not files:
            return {
                "success": False,
                "message": "No files found in selection",
                "files": [],
                "total_tokens": 0,
            }
        
        # 2. Get summary information
        summary = self._get_summary(files)
        
        # 3. Generate export content based on format
        if format.lower() == "json":
            content = self._export_json(files, summary)
        elif format.lower() == "xml":
            content = self._export_xml(files, summary)
        elif format.lower() == "yaml":
            content = self._export_yaml(files, summary)
        else:  # markdown
            content = self._export_markdown(files, summary)
        
        # 4. Write to file
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding='utf-8')
            
            # Count tokens in the exported content
            total_tokens = count_tokens(content)
            
            return {
                "success": True,
                "message": f"Successfully exported {len(files)} files to {output_path}",
                "files": [str(f) for f in files],
                "total_size_human": summary["total_size_human"],
                "total_tokens": total_tokens,
                "output_path": str(output_path),
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to export: {str(e)}",
                "files": [],
                "total_tokens": 0,
            }
    
    def _get_summary(self, files: List[Path]) -> Dict[str, Any]:
        """Get summary statistics for selected files."""
        total_size = 0
        total_lines = 0
        languages = {}
        
        for file_path in files:
            info = get_file_info(file_path)
            total_size += info["size"]
            total_lines += info["lines"]
            
            ext = file_path.suffix.lower()
            if ext not in languages:
                languages[ext] = 0
            languages[ext] += 1
            
        return {
            "total_files": len(files),
            "total_size": total_size,
            "total_size_human": self._format_size(total_size),
            "total_lines": total_lines,
            "languages": languages,
        }

    def _format_size(self, size_bytes: int) -> str:
        if size_bytes == 0: return "0 B"
        units = ["B", "KB", "MB", "GB"]
        size = float(size_bytes)
        idx = 0
        while size >= 1024 and idx < len(units) - 1:
            size /= 1024
            idx += 1
        return f"{size:.1f} {units[idx]}"

    def _export_markdown(self, files: List[Path], summary: Dict[str, Any]) -> str:
        lines = []
        lines.append("# AI Context Export")
        lines.append(f"Generated on: {datetime.datetime.now().isoformat()}")
        lines.append("")
        lines.append("## Summary")
        lines.append(f"- **Total Files**: {summary['total_files']}")
        lines.append(f"- **Total Size**: {summary['total_size_human']}")
        lines.append("")
        lines.append("## File Contents")
        lines.append("")
        
        for file_path in files:
            try:
                try:
                    display_path = file_path.relative_to(self.selection.base_path)
                except ValueError:
                    display_path = file_path

                content = file_path.read_text(encoding='utf-8', errors='replace')
                ext = file_path.suffix.lstrip('.') or 'txt'
                
                lines.append(f"### {display_path}")
                lines.append(f"```{ext}")
                lines.append(content)
                lines.append("```")
                lines.append("")
            except Exception as e:
                lines.append(f"### {file_path} (Error: {e})")
                lines.append("")
        return "\n".join(lines)

    def _export_json(self, files: List[Path], summary: Dict[str, Any]) -> str:
        export_data = {
            "metadata": {"generated_at": datetime.datetime.now().isoformat(), "summary": summary},
            "files": []
        }
        for file_path in files:
            try:
                try:
                    rel_path = str(file_path.relative_to(self.selection.base_path))
                except ValueError:
                    rel_path = str(file_path)
                content = file_path.read_text(encoding='utf-8', errors='replace')
                export_data["files"].append({"path": rel_path, "content": content})
            except Exception as e:
                export_data["files"].append({"path": str(file_path), "error": str(e)})
        return json.dumps(export_data, indent=2, ensure_ascii=False)

    def _export_xml(self, files: List[Path], summary: Dict[str, Any]) -> str:
        root = ET.Element("ai_context_export")
        ET.SubElement(root, "metadata").text = datetime.datetime.now().isoformat()
        files_elem = ET.SubElement(root, "files")
        for file_path in files:
            f_elem = ET.SubElement(files_elem, "file")
            try:
                try:
                    rel_path = str(file_path.relative_to(self.selection.base_path))
                except ValueError:
                    rel_path = str(file_path)
                f_elem.set("path", rel_path)
                f_elem.text = file_path.read_text(encoding='utf-8', errors='replace')
            except Exception as e:
                f_elem.set("error", str(e))
        return ET.tostring(root, encoding='unicode')

    def _export_yaml(self, files: List[Path], summary: Dict[str, Any]) -> str:
        import yaml
        data = {"metadata": {"generated": datetime.datetime.now().isoformat()}, "files": []}
        for file_path in files:
            try:
                try:
                    rel_path = str(file_path.relative_to(self.selection.base_path))
                except ValueError:
                    rel_path = str(file_path)
                content = file_path.read_text(encoding='utf-8', errors='replace')
                data["files"].append({"path": rel_path, "content": content})
            except Exception:
                pass
        return yaml.dump(data, sort_keys=False)
```

---

## Phase 4: Update Commands

**Objective**: Ensure the TUI saves to the new unified format and the export commands read it correctly.

1.  **Modify `ai_context_manager/commands/select_cmd.py`**:
    Update `action_save_and_quit` to save the unified `include` list.

```python
    # ... imports ...
    
    # ... inside SelectionApp class ...
    def action_save_and_quit(self) -> None:
        """Save selection to YAML and exit."""
        includes = []

        for path in self.tree_widget.selected_paths:
            try:
                rel_path = path.relative_to(self.base_path)
            except ValueError:
                rel_path = path

            # Add path to unified list
            includes.append(str(rel_path))

        includes.sort()

        data = {
            "basePath": str(self.base_path.resolve()),
            "include": includes,
        }

        with open(self.output_file, "w") as f:
            yaml.dump(data, f, sort_keys=False)

        self.exit(result=True)
```

2.  **Modify `ai_context_manager/commands/export_cmd.py`**:
    Update to use `Selection` logic.

```python
"""Native Export command."""
from pathlib import Path
import typer
from rich.console import Console
from ai_context_manager.core.selection import Selection
from ai_context_manager.core.exporter import ContextExporter
from ai_context_manager.config import CLI_CONTEXT_SETTINGS

app = typer.Typer(context_settings=CLI_CONTEXT_SETTINGS)
console = Console()

@app.command("export")
def export(
    selection_file: Path = typer.Argument(..., help="Path to selection.yaml", exists=True),
    output: Path = typer.Option("context.md", "--output", "-o", help="Output file path"),
    format: str = typer.Option("markdown", "--format", "-f", help="Format: markdown, json, xml, yaml"),
):
    """Generate context file using the native Python exporter."""
    try:
        selection = Selection.load(selection_file)
    except Exception as e:
        console.print(f"[red]Error loading selection file: {e}[/red]")
        raise typer.Exit(1)

    console.print(f"[blue]Exporting from {selection.base_path}...[/blue]")
    exporter = ContextExporter(selection)
    result = exporter.export_to_file(output_path=output, format=format)

    if result["success"]:
        console.print(f"[green]✓ {result['message']}[/green]")
        console.print(f"  Total Tokens: [bold]{result['total_tokens']}[/bold]")
    else:
        console.print(f"[red]✗ Export failed: {result['message']}[/red]")
        raise typer.Exit(1)
```

3.  **Modify `ai_context_manager/commands/generate_cmd.py`**:
    Update Repomix wrapper to handle the unified list and detect folders dynamically.

```python
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
```

---

## Phase 5: CLI Entry Point & Clean Up

**Objective**: Update the main entry point to register only the active commands.

1.  **Modify `ai_context_manager/cli.py`**:

```python
"""Main CLI entry point."""
import typer
from rich.console import Console
from ai_context_manager.commands import select_cmd, export_cmd, generate_cmd
from ai_context_manager.config import CLI_CONTEXT_SETTINGS

app = typer.Typer(
    name="aicontext",
    help="Visual Context Manager - Select files visually and export for AI.",
    add_completion=False,
    context_settings=CLI_CONTEXT_SETTINGS,
)
console = Console()

app.add_typer(select_cmd.app, name="select", help="Open visual file selector")
app.add_typer(export_cmd.app, name="export", help="Native: Generate context from selection.yaml")
app.add_typer(generate_cmd.app, name="generate", help="Repomix: Generate context using external tool")

@app.command()
def version():
    """Show version information."""
    console.print("AI Context Manager v0.2.0 (Visual Edition)")

if __name__ == "__main__":
    app()
```

2.  **Cleanup Tests**:
    *   Delete tests in `tests/` and `tests/commands/` related to deleted commands (`add`, `remove`, `list`, `profile`).
    *   Ensure remaining tests (for `export`, `generate`) align with the new method signatures.

---

## Phase 6: Documentation Update

**Objective**: Update `README.md` to reflect the new functionality.

1.  **Overwrite `README.md`**:

```markdown
# AI Context Manager

A visual tool to select files from your codebase and package them for Large Language Models (LLMs).

## Features
- **Visual Selection**: Interactive TUI to browse and checkmark files/folders.
- **Unified Config**: Selections saved to a simple `selection.yaml`.
- **Dual Engine**: Export using the built-in Python engine or via Repomix.

## Installation
```bash
uv pip install -e .
```

## Workflow

### 1. Select Files
Launch the visual interface.
```bash
aicontext select . -o my-selection.yaml
```
*   **Navigate**: Arrow keys.
*   **Toggle**: `Enter` key (works on files and folders).
*   **Save**: `s` key.

This creates a YAML file:
```yaml
basePath: /absolute/path/to/project
include:
  - README.md
  - src/utils
```

### 2. Generate Context

#### Option A: Native Exporter (`export`)
Fast, Python-only, supports token counting.
```bash
aicontext export my-selection.yaml -o context.md --format markdown
```

#### Option B: Repomix Wrapper (`generate`)
Uses the industry-standard `repomix` tool (requires `npm install -g repomix`).
```bash
aicontext generate repomix my-selection.yaml --style xml
```




