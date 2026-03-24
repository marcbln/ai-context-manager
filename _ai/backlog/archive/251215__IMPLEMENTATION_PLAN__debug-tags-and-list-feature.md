---
filename: "ai-plans/251215__IMPLEMENTATION_PLAN__debug-tags-and-list-feature.md"
title: "Enhanced Tag Debugging and Tag Listing Command"
createdAt: 2025-12-15 01:00
updatedAt: 2025-12-15 01:00
status: draft
priority: high
tags: [cli, debugging, feature, tags]
estimatedComplexity: moderate
documentType: IMPLEMENTATION_PLAN
---

# Enhanced Tag Debugging and Tag Listing Command

## Problem Description
The user is encountering a "No files found" error when using `aicontext generate repomix` with `--dir` and `--tag`, despite files existing in the target directory. The current verbose output (`-v`) is insufficient to diagnose why files are being rejected (e.g., parsing errors, missing `meta` section, or tag mismatches).

Additionally, there is no easy way to discover what tags are available in a directory of context definition files, making it hard for users to know which tags to filter by.

## Solution Overview
1.  **Enhance Verbosity**: Refactor `_find_files_by_tags` in `generate_cmd.py` to provide detailed per-file logs when `-v` is active. It will show exactly what tags were found in each file and why a file didn't match.
2.  **New `tags` Command**: Implement a new subcommand `aicontext generate tags --dir <path>` that scans the directory and prints a summary of all available tags and their occurrence counts.

---

## Phase 1: Enhance Tag Discovery Verbosity

**Objective**: Modify the internal discovery logic to print detailed decision logs for every file scanned when verbose mode is enabled.

### [MODIFY] `ai_context_manager/commands/generate_cmd.py`

Update `_find_files_by_tags` to include comprehensive logging.

```python
# ai_context_manager/commands/generate_cmd.py

# ... imports ...

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
        except Exception as e:
            if verbose:
                console.print(f"[yellow]  ⚠ Skipping {file_path.name}: Parsing error ({e})[/yellow]")
            continue

        file_meta = data.get("meta", {})
        # Normalize tags: handle None, empty list, or missing key
        raw_tags = file_meta.get("tags", [])
        if not isinstance(raw_tags, list):
            raw_tags = []
            
        file_tags = set(raw_tags)

        # Verbose Logging for Debugging
        if verbose:
            tag_str = ", ".join(file_tags) if file_tags else "<none>"
            if required_tags.isdisjoint(file_tags):
                console.print(f"[dim]  • {file_path.name}: [yellow]No match[/yellow] (Found: {tag_str})[/dim]")
            else:
                console.print(f"[dim]  • {file_path.name}: [green]Match[/green] (Found: {tag_str})[/dim]")

        if required_tags.isdisjoint(file_tags):
            continue

        matches.append(file_path)

    return sorted(matches)
```

---

## Phase 2: Add `list-tags` Command

**Objective**: Implement a new command to help users inspect available tags in a context directory.

### [MODIFY] `ai_context_manager/commands/generate_cmd.py`

Add the `tags` subcommand to the `app`.

1.  Add `from collections import Counter` to imports.
2.  Implement the command.

```python
# ai_context_manager/commands/generate_cmd.py

# ... existing imports ...
from collections import Counter # <--- NEW IMPORT
from rich.table import Table    # <--- NEW IMPORT

# ... existing code ...

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
            meta = data.get("meta", {})
            tags = meta.get("tags", [])
            
            if isinstance(tags, list) and tags:
                tag_counts.update(tags)
            else:
                files_without_tags += 1
                
        except Exception:
            if verbose:
                console.print(f"[red]Failed to parse: {file_path.name}[/red]")
            continue

    if not tag_counts:
        console.print(f"[yellow]No tags found in {len(candidates)} files.[/yellow]")
        return

    # Display results in a table
    table = Table(title=f"Available Tags in {context_dir.name}")
    table.add_column("Tag", style="cyan")
    table.add_column("Count", style="green", justify="right")

    for tag, count in tag_counts.most_common():
        table.add_row(tag, str(count))

    console.print(table)
    
    if files_without_tags > 0:
        console.print(f"[dim]({files_without_tags} files had no tags)[/dim]")

```

---

## Phase 3: Testing

**Objective**: Verify the verbosity logic and the new command.

### [MODIFY] `tests/commands/test_generate_tags.py`

Add tests for the `tags` command and verify detailed output.

```python
# tests/commands/test_generate_tags.py

# ... existing imports ...

def test_list_tags_command(tmp_path: Path):
    """Test the 'generate tags' command."""
    defs_dir = tmp_path / "defs"
    defs_dir.mkdir()
    base_path = tmp_path / "src"
    
    # Create files with various tags
    create_mock_yaml(defs_dir, base_path, "api.yaml", ["api", "backend"], ["api.py"])
    create_mock_yaml(defs_dir, base_path, "ui.yaml", ["frontend", "ui"], ["ui.vue"])
    create_mock_yaml(defs_dir, base_path, "core.yaml", ["api", "core"], ["core.py"])
    # File with no tags
    create_mock_yaml(defs_dir, base_path, "untagged.yaml", [], ["other.py"])

    result = runner.invoke(app, ["generate", "tags", "--dir", str(defs_dir)])
    
    assert result.exit_code == 0
    assert "Available Tags" in result.output
    # Check for tags and counts
    assert "api" in result.output
    assert "frontend" in result.output
    # 'api' appears twice
    assert "2" in result.output 

def test_find_files_verbosity(tmp_path: Path):
    """Test that -v prints detailed tag info during discovery."""
    defs_dir = tmp_path / "defs"
    defs_dir.mkdir()
    base_path = tmp_path / "src"
    
    create_mock_yaml(defs_dir, base_path, "api.yaml", ["api"], ["api.py"])
    create_mock_yaml(defs_dir, base_path, "ui.yaml", ["frontend"], ["ui.vue"])

    # Mock dependencies to allow execution to proceed to discovery
    with patch("shutil.which", return_value="/usr/bin/repomix"), \
         patch("subprocess.run"):
        
        result = runner.invoke(app, [
            "generate", "repomix", 
            "--dir", str(defs_dir), 
            "--tag", "api", 
            "-v" # Verbose
        ])

    assert result.exit_code == 0
    # Check logs
    assert "Scanning" in result.output
    assert "api.yaml: Match (Found: api)" in result.output
    assert "ui.yaml: No match (Found: frontend)" in result.output
```

---

## Phase 4: Documentation Update

**Objective**: Update `README.md` to reflect the new tool for inspecting tags.

### [MODIFY] `README.md`

Add a section under "Generate Context via Repomix".

```markdown
### 3. Inspect Available Tags
If you are unsure which tags are available in your definition files, use the `tags` command:

```bash
aicontext generate tags --dir ./ai-context-definitions
```
```

---

## Phase 5: Implementation Report

**Objective**: Verify and document the fix.

### [NEW FILE] `ai-plans/251215__IMPLEMENTATION_REPORT__debug-tags-and-list-feature.md`

```yaml
---
filename: "ai-plans/251215__IMPLEMENTATION_REPORT__debug-tags-and-list-feature.md"
title: "Report: Enhanced Tag Debugging and Listing"
createdAt: 2025-12-15 01:00
updatedAt: 2025-12-15 01:00
plan_file: "ai-plans/251215__IMPLEMENTATION_PLAN__debug-tags-and-list-feature.md"
project: "ai-context-manager"
status: completed
files_created: 0
files_modified: 3
files_deleted: 0
tags: [cli, debugging, tags]
documentType: IMPLEMENTATION_REPORT
---

# Report: Enhanced Tag Debugging and Listing

## Summary
To address user confusion when files are not matched by tags, `generate repomix` now provides detailed per-file logging in verbose mode, showing exactly what tags were found in every candidate file. A new command `aicontext generate tags` was added to list all unique tags and their frequencies within a directory.

## Files Changed
- **Modified**: `ai_context_manager/commands/generate_cmd.py`
    - Updated `_find_files_by_tags` to print "Match/No match" and found tags for every file when `-v` is used.
    - Added `list_available_tags` (CLI command: `generate tags`) to aggregate and display tags using a Rich table.
- **Modified**: `tests/commands/test_generate_tags.py`
    - Added `test_list_tags_command` and `test_find_files_verbosity`.
- **Modified**: `README.md`
    - Documented the new `generate tags` command.

## Key Changes
- **Verbose Diagnostics**: Users can now see if a file is being skipped due to a missing tag or a parsing error.
- **Discovery**: Users can now audit their context definitions directory to see the taxonomy of tags in use.

## Verification
1. Run `aicontext generate repomix --dir <dir> --tag <tag> -v`: Verify it prints "Found: tag1, tag2" for every file.
2. Run `aicontext generate tags --dir <dir>`: Verify it prints a table of tags.
```
