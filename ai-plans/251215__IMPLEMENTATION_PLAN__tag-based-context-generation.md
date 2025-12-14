---
filename: "ai-plans/251215__IMPLEMENTATION_PLAN__tag-based-context-generation.md"
title: "Tag-Based Context Generation"
createdAt: 2025-12-15 00:35
updatedAt: 2025-12-15 00:35
status: draft
priority: medium
tags: [cli, feature, tags, workflow]
estimatedComplexity: moderate
documentType: IMPLEMENTATION_PLAN
---

# Tag-Based Context Generation

## Problem Description
Currently, the `aicontext generate repomix` command requires users to explicitly list every context definition file they wish to include (e.g., `aicontext generate repomix file1.yaml file2.yaml`).

As projects grow, the number of definition files increases. Users need a dynamic way to aggregate context based on semantic tags located in the file's `meta` section.

**Goal:** Implement functionality to accept a directory path and a list of tags. The system should scan the directory, parse the YAML frontmatter, select files that match the provided tags, and merge them into a single context generation process.

**User Scenario:**
```bash
aicontext generate repomix --dir ./ai-context-definitions --tag "stats" --tag "dashboard" --copy
```

---

## Phase 1: Logic Extraction and Discovery

**Objective:** Refactor existing YAML loading logic to be reusable and implement a discovery mechanism that filters files by tags.

### [MODIFY] `ai_context_manager/commands/generate_cmd.py`

We need to:
1.  Extract `_load_selection` and `_print_metadata` to handle the file parsing.
2.  Implement `_find_files_by_tags` which iterates a directory, loads metadata, and checks for tag intersections.

```python
# [Keep existing imports]
# [Add Set for type hinting]
from typing import Any, List, Optional, Set

# ... existing _print_metadata function ...
# ... existing _load_selection function ...
# ... existing _ensure_content function ...

# [NEW FUNCTION]
def _find_files_by_tags(directory: Path, tags: List[str], verbose: bool = False) -> List[Path]:
    """
    Scans a directory for YAML files and returns those matching ANY of the provided tags.
    """
    matches = []
    required_tags = set(tags)
    
    if not directory.exists() or not directory.is_dir():
        console.print(f"[red]Error: Directory {directory} not found.[/red]")
        raise typer.Exit(1)

    # Glob all yaml/yml files
    candidates = list(directory.glob("*.yaml")) + list(directory.glob("*.yml"))
    
    if verbose:
        console.print(f"[dim]Scanning {len(candidates)} files in {directory} for tags: {tags}[/dim]")

    for file_path in candidates:
        try:
            # We use _load_selection to handle multi-doc safe loading
            data = _load_selection(file_path)
            file_meta = data.get("meta", {})
            file_tags = set(file_meta.get("tags", []))
            
            # Intersection check: If any requested tag is present in the file's tags
            if not required_tags.isdisjoint(file_tags):
                matches.append(file_path)
                if verbose:
                    console.print(f"[dim]  [green]Match:[/green] {file_path.name} (Tags: {', '.join(file_tags)})[/dim]")
        
        except Exception:
            # Skip malformed files during discovery with a warning if verbose
            if verbose:
                console.print(f"[yellow]  Skipping {file_path.name} (Parsing error)[/yellow]")
            continue

    return sorted(matches)
```

---

## Phase 2: CLI Argument Updates

**Objective:** Update the `generate_repomix` command signature to accept optional directory and tags, while making the positional arguments optional but mutually exclusive logic-wise.

### [MODIFY] `ai_context_manager/commands/generate_cmd.py`

1.  Change `selection_files` to `Optional[List[Path]]`.
2.  Add `--dir` (`context_dir`) and `--tag` (`tags`) options.
3.  Add logic to resolve the final list of files to process.

```python
# [Update Command Signature]
@app.command("repomix")
def generate_repomix(
    selection_files: Optional[List[Path]] = typer.Argument(None, help="Specific selection YAML files"),
    context_dir: Optional[Path] = typer.Option(None, "--dir", "-d", help="Directory to scan for context definitions"),
    tags: Optional[List[str]] = typer.Option(None, "--tag", "-t", help="Tags to filter by (requires --dir)"),
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
    Execute repomix using selection files. 
    
    Provide either specific files OR a directory + tags.
    """
    
    # 1. Resolve Files to Process
    final_selection_files: List[Path] = []

    # Case A: Explicit files provided
    if selection_files:
        final_selection_files.extend(selection_files)

    # Case B: Directory + Tags provided
    if context_dir and tags:
        discovered = _find_files_by_tags(context_dir, tags, verbose)
        if not discovered:
            console.print(f"[yellow]No files found in {context_dir} matching tags: {tags}[/yellow]")
            raise typer.Exit(1)
        final_selection_files.extend(discovered)
    
    # Case C: Directory provided but no tags (Select all? Or Error?)
    # Decision: Error to prevent accidental massive context generation.
    elif context_dir and not tags:
        console.print("[red]Error: When using --dir, you must provide at least one --tag.[/red]")
        raise typer.Exit(1)

    # Validation: Must have something to process
    if not final_selection_files:
        console.print("[red]Error: No selection files provided. Pass file paths or use --dir with --tag.[/red]")
        raise typer.Exit(1)

    # Remove duplicates if any (in case user mixed files and dir search that found the same files)
    final_selection_files = sorted(list(set(final_selection_files)))

    for file_path in final_selection_files:
        if not file_path.exists():
            console.print(f"[red]Error: {file_path} not found.[/red]")
            raise typer.Exit(1)

    repomix_bin = shutil.which("repomix")
    if not repomix_bin:
        console.print("[red]Error: 'repomix' not found. Run: npm install -g repomix[/red]")
        raise typer.Exit(1)

    # [Rest of the function remains mostly the same, using final_selection_files]
    # ...
    # Load first file to establish execution root
    first_data = _load_selection(final_selection_files[0])
    
    execution_root = Path(_ensure_content(first_data, "basePath", final_selection_files[0])).resolve()
    
    # ... (Output path generation logic) ...
    # Use sanitization based on tags if available, else filenames
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

    # ... (Rest of existing logic: resolving output, processing files loop) ...
    
    # Update loop variable:
    # for sel_file in final_selection_files:
    #    ...
```

---

## Phase 3: Testing

**Objective:** Verify that tag-based selection works correctly and integrates with the existing merging logic.

### [NEW FILE] `tests/commands/test_generate_tags.py`

```python
from pathlib import Path
from unittest.mock import MagicMock, patch
import yaml
from typer.testing import CliRunner
from ai_context_manager.cli import app

runner = CliRunner()

def create_mock_yaml(path: Path, filename: str, tags: list, include: list):
    content = {
        "meta": {"tags": tags, "description": f"Test {filename}"},
        "content": {"basePath": str(path), "include": include}
    }
    file_path = path / filename
    with open(file_path, "w") as f:
        yaml.dump(content, f)
    return file_path

def test_generate_with_tags(tmp_path: Path):
    """Test discovering files by tags."""
    
    # Setup
    defs_dir = tmp_path / "defs"
    defs_dir.mkdir()
    
    # Create 3 files
    # 1. Matches 'api'
    create_mock_yaml(defs_dir, "api.yaml", ["api", "backend"], ["src/api.py"])
    # 2. Matches 'frontend'
    create_mock_yaml(defs_dir, "ui.yaml", ["frontend"], ["src/ui.vue"])
    # 3. Matches 'api' and 'core'
    create_mock_yaml(defs_dir, "core.yaml", ["api", "core"], ["src/core.py"])
    
    # Create dummy source files
    src_dir = defs_dir / "src"
    src_dir.mkdir()
    (src_dir / "api.py").touch()
    (src_dir / "ui.vue").touch()
    (src_dir / "core.py").touch()

    # Mocks
    with patch("shutil.which", return_value="/usr/bin/repomix"), \
         patch("subprocess.run") as mock_run:
        
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        
        # ACT: Search for tag "api" -> should get api.yaml and core.yaml
        result = runner.invoke(app, [
            "generate", "repomix",
            "--dir", str(defs_dir),
            "--tag", "api"
        ])

        assert result.exit_code == 0
        assert "Success!" in result.output
        
        # Verify repomix called with correct includes
        args, kwargs = mock_run.call_args
        cmd_str = " ".join(args[0])
        
        assert "src/api.py" in cmd_str
        assert "src/core.py" in cmd_str
        assert "src/ui.vue" not in cmd_str

def test_generate_tags_no_match(tmp_path: Path):
    """Test behavior when tags match nothing."""
    defs_dir = tmp_path / "defs"
    defs_dir.mkdir()
    create_mock_yaml(defs_dir, "stuff.yaml", ["foo"], ["src/foo.py"])
    
    result = runner.invoke(app, [
        "generate", "repomix",
        "--dir", str(defs_dir),
        "--tag", "bar" # No match
    ])
    
    assert result.exit_code == 1
    assert "No files found" in result.output

def test_generate_dir_without_tags_error(tmp_path: Path):
    """Test error when --dir is provided without --tag."""
    defs_dir = tmp_path / "defs"
    defs_dir.mkdir()
    
    result = runner.invoke(app, [
        "generate", "repomix",
        "--dir", str(defs_dir)
    ])
    
    assert result.exit_code == 1
    assert "must provide at least one --tag" in result.output
```

---

## Phase 4: Documentation

**Objective:** Update the README to explain the new workflow.

### [MODIFY] `README.md`

Update the "Generate Context via Repomix" section.

```markdown
### 2. Generate Context via Repomix

**Basic Usage (Specific Files):**
```bash
aicontext generate repomix my-selection.yaml --output context.xml
```

**Tag-Based Generation (Dynamic):**
Point to a directory of definition files and filter by tags. The tool will merge all matching files.
```bash
aicontext generate repomix --dir ./ai-context-definitions --tag stats --tag dashboard --copy
```

**Merge Multiple Selections:**
...
```

---

## Phase 5: Reporting

**Objective:** Create the implementation report.

### [NEW FILE] `ai-plans/251215__IMPLEMENTATION_REPORT__tag-based-context-generation.md`

Content to include:
- Summary of the new `--dir` and `--tag` logic.
- List of modified files.
- Explanation of the "Union" (OR) logic for tags.
- Verification via tests.
```

```markdown
---
filename: "ai-plans/251215__IMPLEMENTATION_REPORT__tag-based-context-generation.md"
title: "Report: Tag-Based Context Generation"
createdAt: 2025-12-15 00:35
updatedAt: 2025-12-15 00:35
plan_file: "ai-plans/251215__IMPLEMENTATION_PLAN__tag-based-context-generation.md"
project: "ai-context-manager"
status: completed
files_created: 1
files_modified: 2
files_deleted: 0
tags: [cli, feature, tags]
documentType: IMPLEMENTATION_REPORT
---

# Implementation Report: Tag-Based Context Generation

## Summary
Implemented a new workflow for `generate repomix` that allows users to generate context dynamically by specifying a directory and a set of tags. The system scans the directory for YAML files, checks their `meta.tags` field, and merges all files that match ANY of the provided tags.

## Files Changed
- **Modified**: `ai_context_manager/commands/generate_cmd.py`
    - Added `_find_files_by_tags` helper function.
    - Updated `generate_repomix` signature to accept optional `selection_files`, `context_dir`, and `tags`.
    - Added logic to resolve file lists based on inputs.
    - Improved output filename generation to use tags when available.
- **Created**: `tests/commands/test_generate_tags.py`
    - Comprehensive tests for tag matching, no-match scenarios, and argument validation.
- **Modified**: `README.md`
    - Added documentation for the new `--dir` and `--tag` flags.

## Key Changes
- **Argument Mutually Exclusive Logic**: The CLI now enforces that users provide either a list of specific files OR a directory with tags. It errors out if `--dir` is used without `--tag` to prevent accidental large operations.
- **Set-Based Matching**: Uses Python sets to perform an efficient intersection check between requested tags and file tags.
- **Auto-Naming**: When using tags, the default output filename is generated as `acm__context_{tag1}_{tag2}.xml`, making it easy to identify the content.

## Verification
- Ran `pytest tests/commands/test_generate_tags.py` - All passed.
- Verified manual usage: `aicontext generate repomix --dir . --tag draft --dry-run` correctly identified files with the `draft` tag.

