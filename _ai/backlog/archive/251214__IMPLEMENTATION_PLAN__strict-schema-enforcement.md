	---
filename: "ai-plans/251214__IMPLEMENTATION_PLAN__strict-schema-enforcement.md"
title: "Strict Integration of Context Definition Schema"
createdAt: 2025-12-14 23:55
updatedAt: 2025-12-14 23:55
status: draft
priority: high
tags: [schema, breaking-change, validation, refactor]
estimatedComplexity: moderate
documentType: IMPLEMENTATION_PLAN
---

# Strict Integration of Context Definition Schema

## Problem Description
The `ai-context-manager` currently allows loose, unstructured YAML files for context definition. We want to professionalize the workflow by strictly enforcing a `context-definition.schema.json`.

This schema mandates a specific structure:
1.  **`meta` object**: Contains authorship, timestamps, description, and tags.
2.  **`content` object**: Contains `basePath` and the `include` list.

**Constraint:** No backward compatibility for legacy flat-file structures. The tool must enforce this schema strictly.

---

## Phase 1: Dependencies and Schema Storage

**Objective**: Add validation libraries and store the schema definition within the package.

### 1. Update Dependencies
[MODIFY] `pyproject.toml`
Add `jsonschema` to the main dependencies.

```toml
# pyproject.toml

[project]
# ... existing ...
dependencies = [
    "typer[all]>=0.9.0",
    "rich>=13.7.0",
    "pyyaml>=6.0",
    "python-dotenv>=1.0.0",
    "pathspec>=0.12.0",
    "textual>=0.70.0",
    "jsonschema>=4.0.0", # NEW
]
# ...
```

### 2. Store Schema Definition
[NEW FILE] `ai_context_manager/schemas/context-definition.schema.json`
(Content as provided in the prompt)

```json
{
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://topdata.example/schema/context-definition.schema.json",
    "title": "Context Definition Document",
    "description": "Schema for AI context definition files with YAML frontmatter and structured content.",
    "type": "object",
    "required": ["meta", "content"],
    "additionalProperties": false,

    "properties": {
        "meta": {
            "type": "object",
            "description": "Frontmatter metadata",
            "required": [
                "description",
                "createdAt",
                "createdBy",
                "updatedAt",
                "updatedBy",
                "documentType"
            ],
            "additionalProperties": false,
            "properties": {
                "description": {
                    "type": "string",
                    "minLength": 3
                },
                "createdAt": {
                    "type": "string",
                    "format": "date"
                },
                "createdBy": {
                    "type": "string",
                    "minLength": 3
                },
                "updatedAt": {
                    "type": "string",
                    "format": "date"
                },
                "updatedBy": {
                    "type": "string",
                    "minLength": 3
                },
                "tags": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "minLength": 1
                    },
                    "uniqueItems": true
                },
                "documentType": {
                    "type": "string",
                    "enum": ["CONTEXT_DEFINITION"]
                },
                "version": {
                    "type": "string",
                    "pattern": "^v[0-9]+(\\.[0-9]+)*$",
                    "description": "Optional semantic-like version, e.g. v1 or v1.2"
                }
            }
        },

        "content": {
            "type": "object",
            "description": "Main document content",
            "required": ["basePath", "include"],
            "additionalProperties": false,
            "properties": {
                "basePath": {
                    "type": "string",
                    "minLength": 1,
                    "description": "Root path used to resolve included files"
                },
                "include": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "string",
                        "minLength": 1
                    },
                    "uniqueItems": true,
                    "description": "List of files or directories included in this context"
                }
            }
        }
    }
}
```

---

## Phase 2: Strict Data Model Implementation

**Objective**: Rewrite `Selection.load` to enforce schema validation and remove all legacy loading logic.

### [MODIFY] `ai_context_manager/core/selection.py`

```python
"""
Strict data model for handling file selections via JSON Schema.
"""
import json
import jsonschema
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml

# Load schema relative to this file
SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "context-definition.schema.json"

@dataclass
class SelectionMeta:
    description: str
    createdAt: str
    createdBy: str
    updatedAt: str
    updatedBy: str
    documentType: str
    tags: List[str] = field(default_factory=list)
    version: Optional[str] = None

@dataclass
class Selection:
    base_path: Path
    include_paths: List[Path]
    meta: SelectionMeta

    @classmethod
    def load(cls, yaml_path: Path) -> 'Selection':
        """
        Load selection from a YAML file with strict Schema validation.
        No legacy support.
        """
        if not yaml_path.exists():
            raise FileNotFoundError(f"Selection file not found: {yaml_path}")

        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
        except Exception as e:
            raise ValueError(f"Failed to parse YAML: {e}")

        # 1. Strict Schema Validation
        cls._validate_schema(data)
        
        # 2. Parse Content
        content = data["content"]
        raw_base = content["basePath"]
        
        # Resolve basePath
        if Path(raw_base).is_absolute():
            base = Path(raw_base).resolve()
        else:
            base = (yaml_path.parent / raw_base).resolve()
        
        # Resolve includes relative to base
        includes = content.get("include", [])
        include_paths = [base / p for p in includes]

        # 3. Parse Meta
        m = data["meta"]
        meta_obj = SelectionMeta(
            description=m["description"],
            createdAt=m["createdAt"],
            createdBy=m["createdBy"],
            updatedAt=m["updatedAt"],
            updatedBy=m["updatedBy"],
            documentType=m["documentType"],
            tags=m.get("tags", []),
            version=m.get("version")
        )

        return cls(base_path=base, include_paths=include_paths, meta=meta_obj)

    @staticmethod
    def _validate_schema(data: Dict[str, Any]):
        """Validate data against the JSON schema."""
        if not SCHEMA_PATH.exists():
            # In production build, this should probably be fatal, 
            # but for dev we might warn. Here we enforce strictness.
            raise RuntimeError("Internal Error: Schema definition file missing.")

        schema = json.loads(SCHEMA_PATH.read_text(encoding='utf-8'))
        try:
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.ValidationError as e:
            # Provide a clean error message to the user
            path = " -> ".join([str(p) for p in e.path]) if e.path else "root"
            raise ValueError(f"Schema Validation Error at '{path}': {e.message}") from e

    def resolve_all_files(self) -> List[Path]:
        """Flatten the selection into a distinct list of files."""
        final_list = []
        for path in self.include_paths:
            if not path.exists():
                continue
            if path.is_file():
                final_list.append(path)
            elif path.is_dir():
                for f in path.rglob("*"):
                    if f.is_file():
                        final_list.append(f)
        return sorted(list(set(final_list)))
```

---

## Phase 3: Update TUI to Enforce Schema

**Objective**: The visual selector must save files that strictly comply with the schema.

### [MODIFY] `ai_context_manager/commands/select_cmd.py`

Updates:
1.  Import `getpass` and `date`.
2.  Rewrite `action_save_and_quit` to build the nested structure.
3.  Implement logic to preserve existing `createdAt` but update `updatedAt`.

```python
# ... imports
import getpass
from datetime import date
# ...

class SelectionApp(App):
    # ... existing code ...

    def action_save_and_quit(self) -> None:
        """Save selection to YAML strictly adhering to the schema."""
        includes = []

        # 1. Collect Paths
        for path in self.tree_widget.selected_paths:
            try:
                rel_path = path.relative_to(self.base_path)
            except ValueError:
                rel_path = path
            includes.append(str(rel_path))

        includes.sort()

        # 2. Prepare Metadata
        current_user = getpass.getuser()
        today_str = date.today().isoformat()

        # Defaults for new files
        meta_data = {
            "description": "Context selection",
            "createdAt": today_str,
            "createdBy": current_user,
            "updatedAt": today_str,
            "updatedBy": current_user,
            "documentType": "CONTEXT_DEFINITION",
            "tags": ["auto-generated"],
            "version": "v1"
        }

        # 3. Load existing metadata if updating
        if self.output_file.exists():
            try:
                with open(self.output_file, 'r') as f:
                    existing = yaml.safe_load(f) or {}
                    if "meta" in existing and isinstance(existing["meta"], dict):
                        # Preserve creation info
                        existing_meta = existing["meta"]
                        meta_data["createdAt"] = existing_meta.get("createdAt", today_str)
                        meta_data["createdBy"] = existing_meta.get("createdBy", current_user)
                        meta_data["description"] = existing_meta.get("description", "Context selection")
                        meta_data["tags"] = existing_meta.get("tags", ["auto-generated"])
                        meta_data["version"] = existing_meta.get("version", "v1")
                        # Always update modification info
                        meta_data["updatedAt"] = today_str
                        meta_data["updatedBy"] = current_user
            except Exception:
                # If file is corrupt or unreadable, overwrite with new defaults
                pass

        # 4. Construct Strict Structure
        data = {
            "meta": meta_data,
            "content": {
                "basePath": str(self.base_path.resolve()),
                "include": includes
            }
        }

        # 5. Save
        with open(self.output_file, "w") as f:
            yaml.dump(data, f, sort_keys=False)

        self.exit(result=True)
```

---

## Phase 4: Update Generator Command

**Objective**: The `generate` command parses YAML manually to pass args to `repomix`. It must be updated to strictly expect the new structure.

### [MODIFY] `ai_context_manager/commands/generate_cmd.py`

```python
# ... imports ...

# ... inside generate_repomix ...

    # 1. Determine Root from First File
    try:
        with open(selection_files[0], "r") as f:
            first_data = yaml.safe_load(f) or {}
        
        # Strict check for content.basePath
        if "content" not in first_data or "basePath" not in first_data["content"]:
             console.print(f"[red]Error: {selection_files[0]} does not match the required schema (missing content.basePath).[/red]")
             raise typer.Exit(1)
             
        execution_root = Path(first_data["content"]["basePath"]).resolve()
    except Exception as exc:
        console.print(f"[red]Error parsing {selection_files[0]}: {exc}[/red]")
        raise typer.Exit(1)

    final_patterns = []

    # 2. Iterate and Collect Patterns
    for sel_file in selection_files:
        try:
            with open(sel_file, "r") as f:
                data = yaml.safe_load(f) or {}
        except Exception as exc:
            console.print(f"[red]Error parsing {sel_file}: {exc}[/red]")
            raise typer.Exit(1)

        # Strict Structure Check
        if "content" not in data or "include" not in data["content"]:
             console.print(f"[red]Error: {sel_file} is missing 'content.include'. Legacy files are not supported.[/red]")
             raise typer.Exit(1)

        raw_base = data["content"]["basePath"]
        if Path(raw_base).is_absolute():
            current_base = Path(raw_base).resolve()
        else:
            current_base = (sel_file.parent / raw_base).resolve()

        includes = data["content"]["include"]

        for item in includes:
            full_path = (current_base / item).resolve()
            is_dir = full_path.is_dir() if full_path.exists() else False

            try:
                rel_path = full_path.relative_to(execution_root)
                pattern = str(rel_path)
                if is_dir:
                    pattern = f"{pattern}/**"
                final_patterns.append(pattern)
            except ValueError:
                # Fallback to absolute path if not relative to root
                pattern = str(full_path)
                if is_dir:
                    pattern = f"{pattern}/**"
                final_patterns.append(pattern)

    # ... rest of the function (deduplication, repomix call) remains the same ...
```

---

## Phase 5: Update Exporter Metadata Rendering

**Objective**: Ensure the `export` command (native python exporter) utilizes the strict metadata.

### [MODIFY] `ai_context_manager/core/exporter.py`

Update `_export_markdown` to assume `self.selection.meta` exists (since `Selection` model enforces it now).

```python
    def _export_markdown(self, files: List[Path], summary: Dict[str, Any]) -> str:
        lines = []
        lines.append("# AI Context Export")
        
        # Meta is guaranteed by Selection class now
        m = self.selection.meta
        lines.append("## Metadata")
        lines.append(f"- **Description**: {m.description}")
        lines.append(f"- **Type**: {m.documentType}")
        lines.append(f"- **Created**: {m.createdAt} by {m.createdBy}")
        lines.append(f"- **Updated**: {m.updatedAt} by {m.updatedBy}")
        
        if m.tags:
            lines.append(f"- **Tags**: {', '.join(m.tags)}")
        if m.version:
            lines.append(f"- **Version**: {m.version}")
            
        lines.append("")
        lines.append("## Summary")
        # ... rest of export logic ...
```

---

## Phase 6: Reporting

**Objective**: Document the strict enforcement.

### [NEW FILE] `ai-plans/251214__IMPLEMENTATION_REPORT__strict-schema-enforcement.md`

```yaml
---
filename: "ai-plans/251214__IMPLEMENTATION_REPORT__strict-schema-enforcement.md"
title: "Report: Strict Schema Enforcement"
createdAt: 2025-12-14 23:55
updatedAt: 2025-12-14 23:55
plan_file: "ai-plans/251214__IMPLEMENTATION_PLAN__strict-schema-enforcement.md"
project: "ai-context-manager"
status: completed
files_created: 1
files_modified: 5
files_deleted: 0
tags: [schema, breaking-change]
documentType: IMPLEMENTATION_REPORT
---

# Implementation Report: Strict Schema Enforcement

## Summary
The `ai-context-manager` has been upgraded to strictly enforce `context-definition.schema.json`. Legacy configuration files (flat YAML) are no longer supported and will raise validation errors. All internal components (TUI, Exporter, Generator) now operate on the structured `meta`/`content` model.

## Files Changed
- **New**: `ai_context_manager/schemas/context-definition.schema.json`
- **Modified**: `pyproject.toml` (Added `jsonschema` dependency)
- **Modified**: `ai_context_manager/core/selection.py` (Strict validation logic, removed legacy fallback)
- **Modified**: `ai_context_manager/commands/select_cmd.py` (Save format updated to schema)
- **Modified**: `ai_context_manager/commands/generate_cmd.py` (Input parsing updated to schema)
- **Modified**: `ai_context_manager/core/exporter.py` (Markdown header includes detailed metadata)

## Key Changes
- **Breaking Change**: `Selection.load()` now throws `ValueError` if the YAML does not contain `meta` and `content` objects matching the schema.
- **Smart TUI**: The selection interface now preserves `createdAt` timestamps while updating `updatedAt` timestamps during edits.
- **Explicit Context**: Exports now contain clear metadata headers derived from the schema.

## Testing Notes
1. **Validation**: Attempting to use a legacy file results in a clear schema validation error.
2. **New Creation**: Using `aicontext select` creates a valid file with the new structure.
3. **Migration**: Users must manually migrate existing files or use the TUI to re-save them.
```

