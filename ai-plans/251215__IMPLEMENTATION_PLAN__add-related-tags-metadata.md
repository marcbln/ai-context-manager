---
filename: "ai-plans/251215__IMPLEMENTATION_PLAN__add-related-tags-metadata.md"
title: "Add Related Tags Metadata to Context Schema"
createdAt: 2025-12-15 01:25
updatedAt: 2025-12-15 01:25
status: draft
priority: medium
tags: [schema, metadata, ux, discovery]
estimatedComplexity: simple
documentType: IMPLEMENTATION_PLAN
---

# Add Related Tags Metadata to Context Schema

## Problem Description
As the number of context definition files grows, there is a need to establish relationships between them. For example, a "Dashboard" context might heavily rely on components defined in a "Dashboard Cards" context.

Currently, there is no standardized way to suggest related contexts or tags within a definition file. Users have requested a mechanism to define `relatedTags` (or suggestions) in the YAML frontmatter. This helps users discover other relevant contexts (e.g., `["dashboard-card-rss", "howto-api"]`) when working with a specific file.

## Implementation Plan

### Phase 1: Update Schema and Data Model

**Objective:** Modify the strict JSON schema to allow a new optional `relatedTags` array in the metadata section, and update the Python data model to handle this field.

**File: `ai_context_manager/schemas/context-definition.schema.json`**

Add `relatedTags` to the `meta` properties.

[MODIFY]
```json
{
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    // ... existing header ...
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
                // ... existing properties (description, createdAt, etc) ...
                "tags": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "minLength": 1
                    },
                    "uniqueItems": true
                },
                "relatedTags": {
                    "type": "array",
                    "description": "Suggested tags relevant to this context",
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
            // ... existing content definition ...
        }
    }
}
```

**File: `ai_context_manager/core/selection.py`**

Update the `SelectionMeta` dataclass and the `load` method to ingest the new field.

[MODIFY]
```python
@dataclass
class SelectionMeta:
    description: str
    createdAt: str
    createdBy: str
    updatedAt: str
    updatedBy: str
    documentType: str
    tags: List[str] = field(default_factory=list)
    relatedTags: List[str] = field(default_factory=list)  # <--- Added field
    version: Optional[str] = None


@dataclass
class Selection:
    # ... existing class definition ...

    @classmethod
    def load(cls, yaml_path: Path) -> "Selection":
        # ... existing loading and validation logic ...

        # 3. Parse Meta
        m = data["meta"]
        meta = SelectionMeta(
            description=m["description"],
            createdAt=m["createdAt"],
            createdBy=m["createdBy"],
            updatedAt=m["updatedAt"],
            updatedBy=m["updatedBy"],
            documentType=m["documentType"],
            tags=m.get("tags", []),
            relatedTags=m.get("relatedTags", []),  # <--- Map new field
            version=m.get("version"),
        )

        return cls(base_path=base, include_paths=include_paths, meta=meta)
```

---

### Phase 2: Update CLI Output

**Objective:** Surface these related tags to the user when running the `generate` command. This acts as a "Did you know?" or "See also" feature.

**File: `ai_context_manager/commands/generate_cmd.py`**

Modify `_print_metadata` to display related tags if they exist.

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

    # Display Tags
    tags = meta.get("tags", [])
    if tags:
        console.print(f"  Tags:        {', '.join(tags)}")

    # Display Related Tags (New)
    related = meta.get("relatedTags", [])
    if related:
        console.print(f"  See Also:    [italic cyan]{', '.join(related)}[/italic cyan]")

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

---

### Phase 3: Verification and Reporting

**Objective:** Verify that files containing `relatedTags` pass schema validation and are correctly displayed in the CLI.

**File: `tests/commands/test_generate_cmd.py`**

Add a test case ensuring the new metadata field is parsed and displayed.

[MODIFY]
```python
def test_generate_prints_related_tags(tmp_path: Path) -> None:
    """Ensure relatedTags are parsed and printed."""
    
    selection_file = tmp_path / "related.yaml"
    selection_content = """---
meta:
  description: "Main Dashboard"
  createdAt: "2025-12-15"
  createdBy: "Tester"
  updatedAt: "2025-12-15"
  updatedBy: "Tester"
  documentType: "CONTEXT_DEFINITION"
  tags: ["dashboard"]
  relatedTags: ["dashboard-cards", "api-docs"]
---
content:
  basePath: "."
  include: ["README.md"]
"""
    selection_file.write_text(selection_content, encoding="utf-8")
    (tmp_path / "README.md").touch()
    
    # Mock Repomix execution
    with patch("shutil.which", return_value="/bin/repomix"), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        
        result = runner.invoke(app, ["generate", "repomix", str(selection_file)])
        
        assert result.exit_code == 0
        assert "See Also:" in result.output
        assert "dashboard-cards, api-docs" in result.output
```

### Final Step: Create Report

After implementation, create the final report file.

**File: `ai-plans/251215__IMPLEMENTATION_REPORT__add-related-tags-metadata.md`**

```markdown
---
filename: "ai-plans/251215__IMPLEMENTATION_REPORT__add-related-tags-metadata.md"
title: "Report: Add Related Tags Metadata"
createdAt: 2025-12-15 01:45
updatedAt: 2025-12-15 01:45
plan_file: "ai-plans/251215__IMPLEMENTATION_PLAN__add-related-tags-metadata.md"
project: "ai-context-manager"
status: completed
files_created: 0
files_modified: 4
files_deleted: 0
tags: [schema, metadata]
documentType: IMPLEMENTATION_REPORT
---

# Summary
Added support for `relatedTags` in the context definition schema. This allows definition files to cross-reference other semantic tags (e.g., a Dashboard suggesting Dashboard Cards). The CLI now displays these suggestions under a "See Also" label during generation.

# Files Changed
- **Modified**: `ai_context_manager/schemas/context-definition.schema.json` (Added `relatedTags` array definition).
- **Modified**: `ai_context_manager/core/selection.py` (Updated `SelectionMeta` dataclass and load logic).
- **Modified**: `ai_context_manager/commands/generate_cmd.py` (Updated `_print_metadata` to display "See Also").
- **Modified**: `tests/commands/test_generate_cmd.py` (Added verification test).

# Key Changes
- JSON Schema now permits `relatedTags: [string, ...]`.
- CLI output highlights these relations in cyan/italic to distinguish them from the file's own tags.

# Testing Notes
- Run `pytest tests/commands/test_generate_cmd.py::test_generate_prints_related_tags` to verify.

