# AI Context Manager

A command-line tool for selecting files from your codebase and exporting them into a single, AI-friendly context file.

## Features

- **Interactive Selection TUI**: Visually pick folders/files and emit Repomix-ready YAML.
- **Repomix Orchestration**: Run `repomix` with local selections or tag-filtered definition files.
- **Native Exporter**: Convert a selection into Markdown/JSON/XML/YAML without Repomix.
- **Tag Indexing**: Discover available tags across your definition files.
- **Chat & RAG Mode**: Index selections into Qdrant and ask questions over them.

## Installation

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
uv pip install -e ".[ai]"
```

## Quick Start

### 1. Select files visually

```bash
aicontext select start . -o dashboard.yaml
```

Navigate with the arrow keys, press `Enter` to toggle files/folders, then save. The YAML produced under `content.basePath` and `content.include` can be reused by every other command.

### 2. Generate context via Repomix

```bash
aicontext generate repomix dashboard.yaml --output /tmp/dashboard.xml
```

- Pass multiple YAML files to merge them.
- Use `--copy` to place the file URI on the clipboard (requires `xclip` on Linux).
- `--style` supports `xml` (default), `markdown`, or `plain`.

### 3. Discover tags and run tag-filtered generation

```bash
aicontext generate tags --dir ./ai-context-definitions
aicontext generate repomix --dir ./ai-context-definitions --tag stats --tag dashboard
```

Definition files are scanned for `meta.tags`, and their `include` lists are merged automatically.

### 4. Export natively (no Repomix)

```bash
aicontext export export selection.yaml --output ctx.md --format markdown
```

The native exporter understands the same YAML schema emitted by the TUI.

### 5. Chat / RAG

```bash
# Requires `uv pip install -e ".[ai]"`
aicontext chat index selection.yaml
aicontext chat ask "Where is Selection.load defined?"
aicontext chat schema
```

Refer to [docs/rag.md](docs/rag.md) for environment setup.

---

## Generate workflow details

### Repomix command reference

```bash
aicontext generate repomix <selection.yaml>... [OPTIONS]
```

Key options:

- `--dir / --tag`: Discover selection files by scanning a directory for tags.
- `--output/-o`: Target file (defaults to `/tmp/acm__*.xml`|`md` depending on `--style`).
- `--style`: `xml` (default), `markdown`, or `plain`.
- `--copy/-c`: Copy the resulting file URI to the clipboard (Linux/xclip only).
- `--verbose/-v`: Echo every include path and the underlying Repomix command.

### Tag discovery

```bash
aicontext generate tags --dir ./ai-context-definitions [-v]
```

Prints a table of tags with file counts so you can craft meaningful `--tag` filters before invoking Repomix.

### Native exporter

```bash
aicontext export export selection.yaml --output context.md --format markdown
```

Use this path when Repomix is unavailable or when you need a quick Markdown/JSON/XML/YAML export powered entirely by Python.

---

## Chat workflow

1. `aicontext chat index selection.yaml` – chunk files from the selection into Qdrant.
2. `aicontext chat ask "question"` – query the indexed data. Omit the question to enter interactive mode.
3. `aicontext chat schema` – view the documentation frontmatter schema used when enriching selection metadata.

---

## Command reference

- `aicontext select start`: Interactive TUI for creating selection YAML files.
- `aicontext generate repomix`: Run Repomix using one or more selection YAML definitions.
- `aicontext generate tags`: Inspect tags inside a directory of context definitions.
- `aicontext export export`: Native exporter that reads a selection YAML and produces Markdown/JSON/XML/YAML.
- `aicontext chat <index|ask|schema>`: Qdrant-backed RAG helpers (requires `.[ai]` extras).

Legacy session/profile commands have been removed; follow the workflow above to manage selections via YAML files instead.
