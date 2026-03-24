---
filename: "ai-plans/251215__IMPLEMENTATION_PLAN__print-absolute-paths.md"
title: "Implementation Plan: Print Absolute Paths for Repomix CLI"
createdAt: 2025-12-15 01:35
updatedAt: 2025-12-15 01:35
status: draft
priority: high
tags: [cli, repomix, ux]
estimatedComplexity: moderate
documentType: IMPLEMENTATION_PLAN
---

## 1. Problem Overview
`aicontext generate repomix` currently prints only the YAML filenames when processing selections. Operators need (a) the absolute filesystem paths to each context definition, and (b) when `-v/--verbose` is used, the fully-qualified absolute paths for every file/folder included in repomix invocation (folders should be suffixed with `/`). Output should leverage Rich syntax highlighting for readability.

## 2. Solution Intent
Deliver a minimally invasive enhancement that:
- Surfaces the resolved absolute path of each selection file during normal execution.
- Extends verbose mode to display every resolved include path (file or folder) with color coding and explicit folder suffixes.
- Preserves existing behavior/tests, adding regression coverage and user documentation updates.
- Ends with a formal implementation report.

## 3. Assumptions & Constraints
- `Path.resolve()` is authoritative for absolute paths; symlinks are acceptable.
- Verbose listing should only trigger once per include entry to avoid excessive duplication.
- Syntax highlighting should use existing Rich console; no new dependencies.
- Folder detection relies on filesystem checks (existing logic already determines this when building repomix include patterns).

## 4. Phased Plan

### Phase 1 – Enhance metadata printing for selection files
1. Introduce helper to format highlighted absolute paths, e.g. `_format_path(path: Path, is_dir: bool, highlight: str) -> str`.
2. Resolve each `sel_file` to an absolute path once and pass into `_print_metadata` for display.
3. Update `_print_metadata` signature to accept `absolute_path: Path | None` and print it after the "Processing" line.

```python
[MODIFY]
# ai_context_manager/commands/generate_cmd.py
@@
def _print_metadata(...):
-    console.print(f"[bold blue]Processing: {filename}[/bold blue]")
+    console.print(f"[bold blue]Processing: {filename}[/bold blue]")
+    if absolute_path:
+        console.print(f"  File Path: [magenta]{absolute_path}[/magenta]")
```

### Phase 2 – Verbose include path emission
1. While iterating `include_items`, capture `(full_path, is_dir)` pairs for reuse.
2. When `verbose` is set, emit a block listing:
   - Header: `console.print("  Includes:")` only once per selection.
   - Each entry with syntax highlighting: folders `[cyan]{path}/[/cyan]`, files `[green]{path}[/green]`.
3. Reuse helper from Phase 1 to ensure folder suffix `/` and maintain Rich styles.

```python
[MODIFY]
# ai_context_manager/commands/generate_cmd.py
@@
for item in include_items:
    ...
    include_details.append((full_path, is_dir))

if verbose and include_details:
    console.print("  Includes:")
    for full_path, is_dir in include_details:
        style = "cyan" if is_dir else "green"
        suffix = "/" if is_dir else ""
        console.print(f"    • [{style}]{full_path}{suffix}[/{style}]")
```

### Phase 3 – Tests & regression coverage
1. Update `tests/commands/test_generate_cmd.py` to assert the new absolute path output.
   - Create `test_generate_repomix_prints_absolute_paths` covering both non-verbose and verbose modes using temporary dirs.
   - Verify folder entries end with `/` when verbose.
2. Adjust existing tests/mocks (if necessary) for changed `_print_metadata` signature.

```python
[MODIFY]
# tests/commands/test_generate_cmd.py
@@
result = runner.invoke(...)
assert str(selection_file.resolve()) in result.output

result_verbose = runner.invoke(..., ["-v"])
assert f"{folder_path.resolve()}/" in result_verbose.output
```

### Phase 4 – Documentation updates
1. Update `docs/export.md` (and other CLI docs if necessary) to describe the new output format and verbose `Includes` block.
2. Add an example snippet showing sample CLI output with highlighted absolute paths and folder suffixes.

```markdown
[MODIFY]
## Verbose Mode Output
```
```
Processing: dashboard.yaml
  File Path: /abs/path/dashboard.yaml
  Includes:
    • /abs/path/datasets/
    • /abs/path/datasets/schema.sql
```
```

### Phase 5 – Final implementation report
1. After coding/testing, capture results in `ai-plans/251215__IMPLEMENTATION_REPORT__print-absolute-paths.md` per template.
2. Summarize deliverables, files touched, testing commands, and any follow-up work.

## 5. Rollout & Validation Checklist
- [ ] Unit tests updated & passing (`pytest tests/commands/test_generate_cmd.py`).
- [ ] Manual smoke test of CLI verbose output (optional if mocked tests comprehensive).
- [ ] Documentation reviewed for clarity.
- [ ] Final report authored and linked to plan.
