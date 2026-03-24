# Implementation Plan: Simplify Generate Command & Add Clipboard Support

## Problem Description
The current `aicontext generate repomix` command is verbose, requiring the user to manually specify an output path and then manually run a separate script to copy the file reference to the clipboard for LLM uploading.

**Current Workflow:**
1. Run long command: `aicontext generate repomix selection.yaml -o output.xml`
2. Run script: `copyfile output.xml`

**Desired Workflow:**
Run: `aicontext generate repomix selection.yaml --copy`
*   Automatically generates a temporary file (e.g., in `/tmp`).
*   Automatically copies the file URI (`file://...`) to the clipboard using `xclip` (Linux) for immediate pasting into AI interfaces.

---

## Phase 1: Clipboard Utility

**Objective:** Create a dedicated utility module to handle clipboard interactions, specifically focusing on the `text/uri-list` format required for file uploads.

**Action:** Create `ai_context_manager/utils/clipboard.py`.

```python
"""Clipboard utilities for AI Context Manager."""
import shutil
import subprocess
from pathlib import Path
from rich.console import Console

console = Console()

def is_xclip_installed() -> bool:
    """Check if xclip is available on the system."""
    return shutil.which("xclip") is not None

def copy_file_uri_to_clipboard(file_path: Path) -> bool:
    """
    Copy the file URI to the clipboard using xclip (Linux).
    Target format is text/uri-list for file uploads.
    """
    if not is_xclip_installed():
        console.print("[red]Error: 'xclip' is not installed. Please install it to use the --copy feature.[/red]")
        return False

    abs_path = file_path.resolve()
    if not abs_path.exists():
        console.print(f"[red]Error: File not found at {abs_path}[/red]")
        return False

    # Construct URI (file:///absolute/path)
    file_uri = abs_path.as_uri()

    try:
        # echo -n "file://..." | xclip -selection clipboard -t text/uri-list
        subprocess.run(
            ["xclip", "-selection", "clipboard", "-t", "text/uri-list"],
            input=file_uri.encode("utf-8"),
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to copy to clipboard: {e}[/red]")
        return False
```

---

## Phase 2: Refactor Generate Command

**Objective:** Update the `generate repomix` command to make the `--output` argument optional and implement the auto-naming and clipboard logic.

**Action:** Modify `ai_context_manager/commands/generate_cmd.py`.

**Changes:**
1.  Import the new clipboard utility.
2.  Change `output` from `typer.Option` to `Optional[Path]`.
3.  Add `copy` (`-c`) boolean flag.
4.  Implement logic to generate a temp path if `output` is not provided.
5.  Invoke clipboard copy if flag is set.

```python
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
```

---

## Phase 3: Testing

**Objective:** Verify the default path generation and clipboard interaction logic (mocked).

**Action:** Update `tests/commands/test_generate_cmd.py`.

```python
# tests/commands/test_generate_cmd.py

# ... existing imports ...
import tempfile
from unittest.mock import patch, MagicMock

# ... existing tests ...

def test_generate_repomix_default_output_and_copy(tmp_path: Path) -> None:
    """Test generation with default temp output and clipboard flag."""

    selection_file = tmp_path / "selection.yaml"
    data = {
        "basePath": str(tmp_path),
        "include": ["main.py"],
    }
    with selection_file.open("w") as f:
        yaml.dump(data, f)
    
    (tmp_path / "main.py").touch()

    # Mock repomix, xclip check, and subprocess for xclip execution
    with patch("shutil.which", side_effect=lambda x: "/usr/bin/xclip" if x == "xclip" else "/usr/bin/repomix"), \
         patch("subprocess.run") as mock_run:
        
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        
        result = runner.invoke(
            app,
            [
                "generate",
                "repomix",
                str(selection_file),
                "--copy", # Enable copy
                # No output flag provided
            ],
        )

    assert result.exit_code == 0
    assert "Success!" in result.output
    assert "File URI copied to clipboard" in result.output

    # Verify calls
    # 1. Repomix call
    repomix_call = mock_run.call_args_list[0]
    cmd_list = repomix_call[0][0]
    assert "repomix" in cmd_list
    
    # Check that output path is in temp directory
    output_arg_index = cmd_list.index("--output") + 1
    output_path = cmd_list[output_arg_index]
    assert tempfile.gettempdir() in output_path
    assert "acm__selection.xml" in output_path # based on filename

    # 2. Clipboard call
    clipboard_call = mock_run.call_args_list[1]
    clip_cmd = clipboard_call[0][0]
    assert clip_cmd == ["xclip", "-selection", "clipboard", "-t", "text/uri-list"]
```

---

## Phase 4: Documentation

**Objective:** Update the README to highlight the new "easy mode" for generation.

**Action:** Update `README.md`.

*   Update the "Generate Context" section.

```markdown
### 2. Generate Context via Repomix

**Basic Usage:**
```bash
aicontext generate repomix my-selection.yaml --output context.xml
```

**Quick Usage (Auto-copy):**
Generate to a temporary file and copy the file reference to your clipboard for immediate uploading.

```bash
# Requires xclip on Linux
aicontext generate repomix my-selection.yaml --copy
```

---

## Phase 5: Status Report

**Action:** Create `ai-plans/251211__REPORT__simplify-generate-command.md` summarizing the changes:
*   Created `clipboard.py` utility.
*   Updated `generate_cmd.py` to handle optional output and clipboard flag.
*   Updated tests.
*   Updated documentation.

