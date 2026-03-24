---
filename: "_ai/backlog/active/260324_1049__IMPLEMENTATION_PLAN__replace-repomix-with-native-xml-generator.md"
title: "Replace External Repomix Dependency with Native XML Generator"
createdAt: 2026-03-24 10:49
updatedAt: 2026-03-24 10:49
status: draft
priority: high
tags: [context-generation, repomix-migration, xml, cli, compression]
estimatedComplexity: complex
documentType: IMPLEMENTATION_PLAN
---

## 1) Problem Statement

`cm generate repomix ...` currently depends on the external `repomix` binary (`npm install -g repomix`) to produce context output, including XML. This introduces operational friction (global dependency, version drift, non-Python runtime requirement) and makes the command less portable.

The objective is to **internalize Repomix-equivalent XML generation into the Python project** (`ai-context-manager`) so the command works without the external binary. Security checks from upstream Repomix are explicitly out of scope for now. The optional `--compress` capability should also be introduced if feasible without disproportionate complexity.

## 2) Executive Summary

This plan migrates `generate repomix` from shelling out to an external Node.js tool into a native Python pipeline that:

1. Reuses existing selection/tag discovery logic.
2. Resolves and loads selected files.
3. Applies optional content transforms (including a practical compression mode).
4. Generates Repomix-compatible XML structure.
5. Preserves CLI ergonomics and backward-compatible command usage.

Implementation is split into phases to reduce risk:
- Phase 1 creates an internal output model and XML renderer.
- Phase 2 wires a native generation engine into CLI flow behind the existing `generate repomix` command.
- Phase 3 adds `--compress` (MVP-compatible, language-aware where feasible, graceful fallback otherwise).
- Phase 4 covers tests, docs, and migration messaging.
- Phase 5 creates the implementation report artifact.

This approach follows SOLID principles by separating responsibilities: CLI orchestration, file collection, content processing, and output rendering each live in dedicated modules.

## 3) Project Environment Details

- Project Name: Python Project
- Frontend root: frontend
- Backend root: src

Additional repository context for this implementation:
- Actual package root: `ai_context_manager`
- CLI entrypoint: `ai_context_manager/cli.py`
- Command module: `ai_context_manager/commands/generate_cmd.py`
- Test suite: `tests/commands/`

## 4) Scope and Non-Goals

### In Scope
- Remove runtime dependency on `repomix` binary for XML generation path.
- Preserve current command UX (`generate repomix ...`) while swapping implementation internals.
- Add optional compression mode for token/cost reduction.
- Keep support for current selection behaviors (single/multi-file selection, `--dir` + `--tag`, metadata display).
- Update docs and tests.

### Out of Scope (for this plan)
- Full parity with all Repomix styles and advanced features not currently needed.
- Security scanning/checks from Repomix.
- Git diff/log embedding features.
- Complex AST infrastructure equivalent to full Tree-sitter multi-language stack in Node.

## 5) Architectural Design (SOLID-Aligned)

### Proposed Modules

1. `core/native_context/models.py`
   - DTOs for rendered context (`ContextFile`, `ContextDocumentOptions`, `ContextRenderInput`).
   - **Single Responsibility**: type-safe data contracts.

2. `core/native_context/file_loader.py`
   - Collect and load selected files, normalize paths relative to execution root.
   - **Single Responsibility**: file discovery + read.

3. `core/native_context/content_transform.py`
   - Transform pipeline (trim, optional remove comments/empty lines, optional compress).
   - **Open/Closed**: easy to add transform strategies.

4. `core/native_context/xml_renderer.py`
   - Build XML output (Repomix-like structure).
   - **Single Responsibility**: serialization only.

5. `core/native_context/generator.py`
   - Orchestrates loader + transforms + renderer.
   - **Dependency Inversion**: takes renderer/transform interfaces where practical for testability.

6. `commands/generate_cmd.py` (modified)
   - CLI orchestration remains here; generation logic delegates to new core modules.

## 6) Multi-Phase Implementation Plan

### Phase 0 — Baseline and Compatibility Contract

**Goal:** Freeze current behavior contract before replacing internals.

**Tasks**
- Inventory existing CLI output and options used in production (`--style`, `--copy`, `--verbose`, `--dir`, `--tag`).
- Confirm XML-only target for migration scope.
- Capture current output expectations from tests and real command output.

**Deliverables**
- Clear behavior matrix (must keep vs. can change).

---

### Phase 1 — Introduce Native XML Rendering Core

**Goal:** Build native XML generation capability independent from CLI command flow.

**Tasks**
- Implement typed models for generation context.
- Implement XML renderer producing structure similar to Repomix XML:
  - root element
  - file summary
  - directory structure
  - files list with path attributes and file content
- Ensure proper escaping and UTF-8-safe output.

**Files**

```python
# [NEW FILE] ai_context_manager/core/native_context/models.py
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class ContextFile:
    path: str
    content: str

@dataclass(frozen=True)
class ContextRenderInput:
    generation_header: str
    tree_string: str
    files: list[ContextFile]
    include_summary: bool = True
    include_tree: bool = True
    include_files: bool = True
```

```python
# [NEW FILE] ai_context_manager/core/native_context/xml_renderer.py
from xml.etree.ElementTree import Element, SubElement, tostring
from .models import ContextRenderInput

class XmlContextRenderer:
    def render(self, payload: ContextRenderInput) -> str:
        root = Element("repomix")
        if payload.include_summary:
            summary = SubElement(root, "file_summary")
            summary.text = payload.generation_header
        if payload.include_tree:
            tree = SubElement(root, "directory_structure")
            tree.text = payload.tree_string
        if payload.include_files:
            files_el = SubElement(root, "files")
            for item in payload.files:
                node = SubElement(files_el, "file", {"path": item.path})
                node.text = item.content
        return tostring(root, encoding="unicode")
```

**Acceptance Criteria**
- Renderer unit tests validate XML shape and escaping.
- No external process call required to produce XML.

---

### Phase 2 — Native Generation Engine + CLI Integration

**Goal:** Replace external subprocess `repomix` invocation with internal engine while preserving command UX.

**Tasks**
- Implement file loader and generator orchestration.
- Reuse current selection parsing and include-pattern resolution behavior.
- Keep metadata printing and file/folder counting unchanged.
- Keep output path default logic (`/tmp/acm__*.xml`) unchanged.
- Remove hard dependency checks for `repomix` binary.

**Files**

```python
# [NEW FILE] ai_context_manager/core/native_context/file_loader.py
from pathlib import Path
from .models import ContextFile

class FileLoader:
    def load(self, execution_root: Path, include_patterns: list[str]) -> list[ContextFile]:
        # Resolve include paths and load content deterministically
        ...
```

```python
# [NEW FILE] ai_context_manager/core/native_context/generator.py
from pathlib import Path
from .file_loader import FileLoader
from .xml_renderer import XmlContextRenderer

class NativeContextGenerator:
    def __init__(self) -> None:
        self._loader = FileLoader()
        self._renderer = XmlContextRenderer()

    def generate_xml(self, execution_root: Path, include_patterns: list[str]) -> str:
        files = self._loader.load(execution_root, include_patterns)
        # build tree + header
        payload = ...
        return self._renderer.render(payload)
```

```python
# [MODIFY] ai_context_manager/commands/generate_cmd.py
# Replace:
#   - shutil.which("repomix") validation
#   - subprocess.run([...repomix...])
# With:
#   - NativeContextGenerator.generate_xml(...)
#   - write text to `output`
# Preserve:
#   - argument contract
#   - metadata display
#   - verbose output semantics
#   - clipboard behavior
```

**Acceptance Criteria**
- `aicontext generate repomix ... --output ...xml` works without installed repomix.
- Existing tag-based and multi-selection workflows keep working.
- Command success/error messaging remains consistent.

---

### Phase 3 — Add `--compress` (Feasible MVP)

**Goal:** Add a practical compression feature inspired by Repomix without introducing heavy complexity.

**Compression Strategy (MVP)**
- Implement `--compress` as transformation pipeline before XML rendering:
  1. Trim and normalize whitespace.
  2. Optional removal of comments/empty lines (language-aware where parser exists).
  3. Structure extraction for Python via stdlib `ast` (classes/functions/signatures/docstrings summary).
  4. Fallback for unsupported languages: non-destructive lightweight compaction (retain code, reduce blank/comment noise when possible).

This delivers immediate value and can later evolve toward full multi-language AST/Tree-sitter parity.

**Files**

```python
# [NEW FILE] ai_context_manager/core/native_context/content_transform.py
from dataclasses import dataclass

@dataclass(frozen=True)
class TransformOptions:
    compress: bool = False

class ContentTransformer:
    def transform(self, text: str, file_path: str, opts: TransformOptions) -> str:
        if not opts.compress:
            return text.strip()
        # Python AST summary for .py, fallback compact mode otherwise
        ...
```

```python
# [MODIFY] ai_context_manager/commands/generate_cmd.py
# Add CLI option:
# compress: bool = typer.Option(False, "--compress", help="Compress output by extracting essential structure")
# Pass option into NativeContextGenerator
```

**Acceptance Criteria**
- `--compress` reduces output size on representative repositories.
- Unsupported file types still produce usable output.
- Fail-safe behavior: transform errors do not break whole generation (fallback to original text per file with warning).

---

### Phase 4 — Tests, Documentation, and Cleanup

**Goal:** Stabilize migration with tests and user-facing docs.

**Tasks**
- Update/replace tests that currently mock `subprocess.run` for repomix execution.
- Add unit tests for:
  - XML renderer
  - file loader path normalization
  - compression behavior and fallbacks
- Add integration-style command tests for native generation success paths.
- Update docs to state that generation is now native and `repomix` binary is no longer required for XML.

**Files**

```python
# [MODIFY] tests/commands/test_generate_cmd.py
# Remove subprocess/repomix-binary assumptions.
# Add assertions for actual generated XML content and output file creation.
```

```python
# [NEW FILE] tests/core/test_native_xml_renderer.py
# XML schema/shape assertions + escaping checks
```

```python
# [NEW FILE] tests/core/test_content_transform.py
# compression path tests + fallback tests
```

```markdown
<!-- [MODIFY] README.md -->
- Replace "Repomix Orchestration" wording with native generator wording.
- Keep command name `generate repomix` for compatibility, clarify implementation is internal.
- Document `--compress` behavior and current scope.
```

```markdown
<!-- [MODIFY] docs/export.md (or docs/generate.md if introduced) -->
- Add migration note and examples.
- Explain expected XML structure and compatibility intent.
```

**Acceptance Criteria**
- Tests pass with `uv run pytest tests/commands/test_generate_cmd.py` and new core tests.
- Documentation accurately reflects behavior.

---

### Phase 5 — Delivery Report Generation (Required)

**Goal:** Produce implementation report artifact after coding phase completion.

**Output File**
- `_ai/backlog/reports/260324_1049__IMPLEMENTATION_REPORT__replace-repomix-with-native-xml-generator.md`

**Required Frontmatter**

```yaml
---
filename: "_ai/backlog/reports/260324_1049__IMPLEMENTATION_REPORT__replace-repomix-with-native-xml-generator.md"
title: "Report: Replace External Repomix Dependency with Native XML Generator"
createdAt: 2026-03-24 10:49
updatedAt: 2026-03-24 10:49
planFile: "_ai/backlog/active/260324_1049__IMPLEMENTATION_PLAN__replace-repomix-with-native-xml-generator.md"
project: "ai-context-manager"
status: completed
filesCreated: 0
filesModified: 0
filesDeleted: 0
tags: [context-generation, repomix-migration, xml, cli, compression]
documentType: IMPLEMENTATION_REPORT
---
```

**Report Sections**
1. Summary
2. Files Changed
3. Key Changes
4. Technical Decisions
5. Testing Notes
6. Usage Examples
7. Documentation Updates
8. Next Steps (optional)

## 7) Detailed Work Breakdown (Task List)

1. Create `core/native_context` package and core modules.
2. Implement XML renderer with deterministic ordering.
3. Implement include-path resolution + file loading service.
4. Integrate native generator into `generate repomix` command.
5. Add `--compress` option and transformer strategy.
6. Update command tests to validate native execution.
7. Add focused core unit tests.
8. Update user docs (`README.md`, `docs/*`).
9. Run targeted test suite and finalize report document.

## 8) Risk Analysis and Mitigations

- **Risk:** Output divergence from Repomix XML expectations.
  - **Mitigation:** Keep root tags and file-path attribute layout compatible; add fixture-based output tests.

- **Risk:** Compression quality varies by language.
  - **Mitigation:** Ship Python-first structural compression + safe fallback for other files.

- **Risk:** Behavioral regressions in CLI metadata and tag workflows.
  - **Mitigation:** Preserve existing parsing/counting methods and extend current command tests rather than replacing them wholesale.

## 9) Testing Strategy

### Unit Tests
- `XmlContextRenderer` output shape, escaping, and optional sections.
- `ContentTransformer` for compressed/non-compressed paths.
- `FileLoader` with mixed file/dir includes and missing files.

### Integration Tests
- `generate repomix` with:
  - single selection file
  - multiple selection files
  - `--dir` + `--tag`
  - `--compress`
  - default output path

### Suggested Commands

```bash
uv run pytest tests/core/test_native_xml_renderer.py -v
uv run pytest tests/core/test_content_transform.py -v
uv run pytest tests/commands/test_generate_cmd.py -v
uv run pytest tests/commands/test_generate_tags.py -v
```

## 10) Documentation Update Plan

- Update `README.md` feature list and quick-start generation section.
- Add migration note: command name unchanged, engine now native (no global npm repomix required for XML).
- Document `--compress` semantics and known limitations.
- Provide before/after example command output snippets for clarity.

## 11) Definition of Done

- Native XML generation works without external `repomix` binary.
- Existing generation workflows remain functional.
- `--compress` available and tested with graceful fallback behavior.
- Tests updated and passing.
- Documentation updated.
- Implementation report created at:
  - `_ai/backlog/reports/260324_1049__IMPLEMENTATION_REPORT__replace-repomix-with-native-xml-generator.md`
