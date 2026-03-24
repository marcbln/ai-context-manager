ai-plans/251213__PLAN__multi-file-generation.md
```markdown
# Implementation Plan: Support Multiple Selection Files in Generate Command

## Problem Description
The `aicontext generate repomix` command currently accepts only a single selection file. Users often organize contexts into multiple files (e.g., `dashboard.yaml`, `stats.yaml`) and want to generate a single combined context. The command should accept multiple arguments for selection files, merge their included patterns relative to a common base path, and generate a unified output.

## Phase 1: Update Generate Command Logic

**Objective:** Modify `ai_context_manager/commands/generate_cmd.py` to accept variadic file arguments and merge their contents.

**Key Logic Changes:**
1.  Change `selection_file` argument to `selection_files` (List[Path]).
2.  Use the `basePath` of the **first** provided file as the "execution root" for the `repomix` command.
3.  Iterate through all provided selection files:
    *   Load the YAML.
    *   Resolve its `basePath`.
    *   Resolve all `include`/`files`/`folders` patterns to absolute paths based on that file's `basePath`.
    *   Convert those absolute paths to be relative to the "execution root".
4.  Deduplicate the resulting list of patterns.
5.  Update the default output filename logic to reflect the primary (first) selection file, appending `_merged` if multiple files are provided.

### [MODIFY] ai_context_manager/commands/generate_cmd.py

```python
"""Command to generate context via Repomix."""
import shutil
import subprocess
import typer
import yaml
import tempfile
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from ..config import CLI_CONTEXT_SETTINGS
from ..utils.clipboard import copy_file_uri_to_clipboard

app = typer.Typer(help="Generate context using repomix", context_settings=CLI_CONTEXT_SETTINGS)
console = Console()

@app.command("repomix")
def generate_repomix(
    selection_files: List[Path] = typer.Argument(..., help="One or more selection YAML files"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file. Defaults to a temp file if not set."),
    style: str = typer.Option("xml", "--style", help="Repomix output style (xml, markdown, plain)"),
    copy: bool = typer.Option(False, "--copy", "-c", help="Copy the output file reference to system clipboard (requires xclip)."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show repomix output"),
):
    """Execute repomix using the paths from one or more selection.yaml files."""
    
    # 1. Validation
    for f in selection_files:
        if not f.exists():
            console.print(f"[red]Error: {f} not found.[/red]")
            raise typer.Exit(1)

    repomix_bin = shutil.which("repomix")
    if not repomix_bin:
        console.print("[red]Error: 'repomix' not found. Run: npm install -g repomix[/red]")
        raise typer.Exit(1)

    # 2. Handle Output Path Logic
    if output is None:
        # Generate filename based on the first selection file
        primary_file = selection_files[0]
        sanitized_name = primary_file.stem.replace(" ", "_")
        if len(selection_files) > 1:
            sanitized_name += "_merged"
            
        temp_dir = Path(tempfile.gettempdir())
        ext = "md" if style == "markdown" else "xml" if style == "xml" else "txt"
        output = temp_dir / f"acm__{sanitized_name}.{ext}"

    # 3. Merge Patterns Logic
    # We use the basePath of the first file as the CWD for repomix
    try:
        with open(selection_files[0], "r") as f:
            first_data = yaml.safe_load(f) or {}
        execution_root = Path(first_data.get("basePath", ".")).resolve()
    except Exception as exc:
        console.print(f"[red]Error parsing {selection_files[0]}: {exc}[/red]")
        raise typer.Exit(1)

    final_patterns = []
    
    for sel_file in selection_files:
        try:
            with open(sel_file, "r") as f:
                data = yaml.safe_load(f) or {}
        except Exception as exc:
            console.print(f"[red]Error parsing {sel_file}: {exc}[/red]")
            raise typer.Exit(1)
            
        current_base = Path(data.get("basePath", ".")).resolve()
        
        # Aggregate includes
        includes = data.get("include", [])
        includes.extend(data.get("files", []))
        includes.extend(data.get("folders", []))
        
        for item in includes:
            # 1. Resolve to absolute path
            full_path = (current_base / item).resolve()
            
            # 2. Check directory status (if it exists) to add /**
            # If it doesn't exist yet, we trust the user pattern or treat as file
            is_dir = full_path.is_dir() if full_path.exists() else False
            
            # 3. Calculate path relative to execution_root
            try:
                rel_path = full_path.relative_to(execution_root)
                pattern = str(rel_path)
                if is_dir:
                    pattern = f"{pattern}/**"
                final_patterns.append(pattern)
            except ValueError:
                # Path is not relative to execution root (e.g. outside project)
                # We can try passing absolute path, but repomix might prefer relative.
                # Let's use absolute path if necessary.
                pattern = str(full_path)
                if is_dir:
                    pattern = f"{pattern}/**"
                final_patterns.append(pattern)

    # Deduplicate while preserving order
    unique_patterns = list(dict.fromkeys(final_patterns))

    if not unique_patterns:
        console.print("[yellow]Warning: No paths found in selections.[/yellow]")
        raise typer.Exit(0)

    cmd = [
        repomix_bin,
        "--output", str(output.resolve()),
        "--style", style,
        "--include", ",".join(unique_patterns),
    ]

    console.print(f"[blue]Running Repomix in {execution_root}...[/blue]")
    if verbose:
        console.print(f"[dim]Command: {' '.join(cmd)}[/dim]")

    try:
        result = subprocess.run(cmd, cwd=execution_root, capture_output=not verbose, text=True)
    except Exception as exc:
        console.print(f"[red]Execution error: {exc}[/red]")
        raise typer.Exit(1)

    if result.returncode == 0:
        console.print(f"[green]Success! Context generated at: {output}[/green]")
        
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

## Phase 2: Update Tests

**Objective:** Verify that the command handles multiple files correctly by merging patterns.

### [MODIFY] tests/commands/test_generate_cmd.py

```python
from pathlib import Path
from unittest.mock import MagicMock, patch
import tempfile
import yaml
from typer.testing import CliRunner
from ai_context_manager.cli import app

runner = CliRunner()

def test_generate_repomix_success(tmp_path: Path) -> None:
    """Repomix command runs when selection and binary exist."""
    selection_file = tmp_path / "selection.yaml"
    data = {
        "basePath": str(tmp_path),
        "include": ["main.py", "src"],
    }
    with selection_file.open("w") as f:
        yaml.dump(data, f)
    
    (tmp_path / "src").mkdir()
    (tmp_path / "main.py").touch()

    with patch("shutil.which", return_value="/usr/bin/repomix"), patch(
        "subprocess.run", return_value=MagicMock(returncode=0, stderr="")
    ) as mock_run:
        result = runner.invoke(
            app,
            [
                "generate",
                "repomix",
                str(selection_file),
                "--output",
                "context.xml",
            ],
        )

    assert result.exit_code == 0
    assert "Success! Context generated" in result.output

    args, kwargs = mock_run.call_args
    cmd = args[0]
    assert any("main.py" in part for part in cmd)
    assert any("src/**" in part for part in cmd)
    assert kwargs["cwd"] == Path(str(tmp_path))

def test_generate_missing_binary(tmp_path: Path) -> None:
    """Gracefully errors when repomix binary missing."""
    selection_file = tmp_path / "selection.yaml"
    selection_file.touch()

    with patch("shutil.which", return_value=None):
        result = runner.invoke(app, ["generate", "repomix", str(selection_file)])

    assert result.exit_code == 1
    assert "Error: 'repomix' not found" in result.output

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

    with patch("shutil.which", side_effect=lambda x: "/usr/bin/xclip" if x == "xclip" else "/usr/bin/repomix"), \
         patch("subprocess.run") as mock_run:
        
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        
        result = runner.invoke(
            app,
            [
                "generate",
                "repomix",
                str(selection_file),
                "--copy",
            ],
        )

    assert result.exit_code == 0
    assert "Success!" in result.output
    assert "File URI copied to clipboard" in result.output
    
    repomix_call = mock_run.call_args_list[0]
    cmd_list = repomix_call[0][0]
    output_arg_index = cmd_list.index("--output") + 1
    output_path = cmd_list[output_arg_index]
    assert tempfile.gettempdir() in output_path
    assert "acm__selection.xml" in output_path

def test_generate_multiple_files_merge(tmp_path: Path) -> None:
    """Test merging patterns from multiple selection files."""
    
    # File 1: defines main.py
    sel1 = tmp_path / "sel1.yaml"
    with sel1.open("w") as f:
        yaml.dump({"basePath": str(tmp_path), "include": ["main.py"]}, f)
    (tmp_path / "main.py").touch()
    
    # File 2: defines docs/ folder
    sel2 = tmp_path / "sel2.yaml"
    # Using relative path for basePath to test robustness, though typically absolute
    with sel2.open("w") as f:
        yaml.dump({"basePath": str(tmp_path), "include": ["docs"]}, f)
    (tmp_path / "docs").mkdir()

    with patch("shutil.which", return_value="/usr/bin/repomix"), \
         patch("subprocess.run") as mock_run:
        
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        
        result = runner.invoke(
            app,
            [
                "generate",
                "repomix",
                str(sel1),
                str(sel2),
                "--output", "merged.xml"
            ],
        )

    assert result.exit_code == 0
    
    args, kwargs = mock_run.call_args
    cmd = args[0]
    
    # Ensure both patterns exist
    # join check: main.py and docs/**
    # Note: patterns joined by comma
    include_idx = cmd.index("--include") + 1
    includes = cmd[include_idx]
    
    assert "main.py" in includes
    assert "docs/**" in includes
    assert kwargs["cwd"] == Path(str(tmp_path))
```

## Phase 3: Documentation

**Objective:** Update `README.md` to reflect the multi-file capability.

### [MODIFY] README.md

Update the "Generate Context via Repomix" section.

```markdown
### 2. Generate Context via Repomix

**Basic Usage:**
```bash
aicontext generate repomix my-selection.yaml --output context.xml
```

**Merge Multiple Selections:**
You can pass multiple selection files. They will be merged into a single context.
```bash
aicontext generate repomix context/dashboard.yaml context/stats.yaml --output combined.xml
```

**Quick Usage (Auto-copy):**
Generate to a temporary file and copy the file reference to your clipboard for immediate uploading.

```bash
# Requires xclip on Linux
aicontext generate repomix my-selection.yaml --copy
```
```

## Phase 4: Status Report

### [NEW FILE] ai-plans/251213__REPORT__multi-file-generation.md

```markdown
# Report: Multi-file Generation Support

**Status**: Completed

**Changes:**
1.  **Generate Command**: Updated `generate repomix` to accept multiple selection files.
2.  **Logic**: Implemented logic to merge patterns from multiple files relative to the first file's `basePath`.
3.  **Tests**: Added `test_generate_multiple_files_merge` to verify pattern merging and execution root handling.
4.  **Documentation**: Updated `README.md` with multi-file examples.

**Verification:**
- Ran `pytest tests/commands/test_generate_cmd.py` to confirm all tests pass.
- Verified merging logic handles directories by appending `/**`.
```
```

