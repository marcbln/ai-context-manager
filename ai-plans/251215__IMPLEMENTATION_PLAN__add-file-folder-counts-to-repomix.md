---
filename: "ai-plans/251215__IMPLEMENTATION_PLAN__add-file-folder-counts-to-repomix.md"
title: "Add File and Folder Counts to Repomix Generate Command"
createdAt: 2025-12-15 01:15
updatedAt: 2025-12-15 01:15
status: draft
priority: medium
tags: [cli, repomix, generate, ui-improvement]
estimatedComplexity: simple
documentType: IMPLEMENTATION_PLAN
---

## Problem Statement

The `ai-context-manager generate repomix` command currently processes context definition files and shows basic metadata (description, updated date) but doesn't display how many files and folders each context definition includes. Users want to see the file/folder counts to better understand the scope of each context before generation.

## Implementation Plan

### Phase 1: Add Counting Logic to Generate Command

**File: `ai_context_manager/commands/generate_cmd.py`**

Add a new helper function to count files and folders for a selection:

[MODIFY]
```python
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
```

Modify the `_print_metadata` function to include counts:

[MODIFY]
```python
def _print_metadata(meta: dict, filename: str, file_count: int = 0, folder_count: int = 0) -> None:
    """Print extracted metadata to the console."""
    if not meta:
        return

    console.print(f"[bold blue]Processing: {filename}[/bold blue]")

    description = meta.get("description")
    if description:
        console.print(f"  Description: [green]{description}[/green]")

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
```

Update the main processing loop in `generate_repomix` to compute and pass counts:

[MODIFY]
```python
    for sel_file in final_selection_files:
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
            _print_metadata(data["meta"], sel_file.name, file_count, folder_count)
        else:
            _print_metadata({}, sel_file.name)

        raw_base = _ensure_content(data, "basePath", sel_file)
        include_items = _ensure_content(data, "include", sel_file)
        # ... rest of existing processing logic
```

### Phase 2: Update Tests

**File: `tests/commands/test_generate_cmd.py`**

Add tests for the new counting functionality:

[MODIFY]
```python
def test_count_files_and_folders():
    """Test the file/folder counting logic."""
    from ai_context_manager.commands.generate_cmd import _count_files_and_folders
    from pathlib import Path
    import tempfile
    import os
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        
        # Create test structure
        test_file = base / "test.txt"
        test_file.write_text("content")
        
        test_dir = base / "subdir"
        test_dir.mkdir()
        
        # Test counting
        file_count, folder_count = _count_files_and_folders(["test.txt", "subdir"], base)
        assert file_count == 1
        assert folder_count == 1
        
        # Test non-existent paths (should be ignored)
        file_count, folder_count = _count_files_and_folders(["nonexistent.txt"], base)
        assert file_count == 0
        assert folder_count == 0

def test_generate_repomix_shows_counts(capsys, tmp_path):
    """Test that generate repomix shows file/folder counts."""
    # Create test selection file
    selection_file = tmp_path / "test.yaml"
    selection_content = """
meta:
  description: "Test selection"
  updatedAt: "2025-12-15"
  updatedBy: "Test User"
content:
  basePath: "."
  include:
    - "README.md"
    - "src/"
"""
    selection_file.write_text(selection_content)
    
    # Create mock files
    (tmp_path / "README.md").write_text("# Test")
    (tmp_path / "src").mkdir()
    
    # Run command (mock repomix to avoid dependency)
    with patch('ai_context_manager.commands.generate_cmd.subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Mock output"
        
        runner = CliRunner()
        result = runner.invoke(app, ["repomix", str(selection_file)])
        
        captured = capsys.readouterr()
        assert "Files:" in captured.out
        assert "Folders:" in captured.out
        assert "1" in captured.out  # Should show 1 file
```

### Phase 3: Update Documentation

**File: `docs/export.md`**

Add documentation about the new file/folder count display:

[MODIFY]
```markdown
## Generate Repomix Output

When running `ai-context-manager generate repomix`, the command now displays detailed information about each context definition file:

```
Processing: dashboard.yaml
  Description: Dashboard
  Updated:     2025-12-14 by Marc Christenfeldt (Desktop)
  Files:       15
  Folders:     3

Processing: organization-stats.yaml
  Description: Organization stats
  Updated:     2025-12-14 by Marc Christenfeldt (Desktop)
  Files:       8
  Folders:     1
```

The file and folder counts represent the number of include entries in each context definition that resolve to existing files and directories on the filesystem.
```

## Technical Considerations

### Design Decisions

1. **Non-recursive counting**: The counts show the number of include entries, not the total files after recursive expansion. This aligns with how Repomix processes patterns and provides a quick overview without expensive filesystem traversal.

2. **Graceful handling**: Non-existent paths are ignored in counting to prevent errors when context definitions reference missing files.

3. **Backward compatibility**: The counts are optional parameters to `_print_metadata`, maintaining existing behavior when no counts are provided.

### Error Handling

- Missing files/folders are silently ignored in counts (consistent with current behavior)
- Invalid paths in include lists don't crash the command
- Counts are only shown when both are > 0 to avoid cluttering output

### Performance Impact

- Minimal overhead: only checks filesystem existence for include entries
- No recursive directory traversal (expensive operation avoided)
- Counts computed once per selection file during normal processing

## Final Report

After implementation, create a report at `ai-plans/251215__IMPLEMENTATION_REPORT__add-file-folder-counts-to-repomix.md` documenting the changes and providing usage examples.
