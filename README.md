# AI Context Manager

A command-line tool for selecting files from your codebase and exporting them into a single, AI-friendly context file.

## Features

- **Profile Management**: Define reusable sets of files and exclusion patterns for different projects.
- **Session Context**: Interactively add, remove, and list files for a one-off export.
- **Multiple Export Formats**: Supports Markdown, JSON, XML, and YAML.
- **Token Counting**: Estimate token counts and check against AI model limits.
- **Flexible Filtering**: Use glob patterns to include and exclude files.
- **Dry Run Mode**: Preview what will be exported without creating a file.

## Installation

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

## Workflows

AI Context Manager supports two primary workflows:

1.  **Profile-based Workflow (Recommended)**: Create a named profile with your desired file paths and exclusion rules. Use this profile to generate context files consistently.
2.  **Session-based Workflow**: Interactively add and remove files for a quick, one-time export without creating a permanent profile.

### Interactive Selection & Generation

Use the interactive TUI to visually select files and immediately generate a context file using Repomix.

1. **Select Files**

   ```bash
   aicontext select start . -o my-selection.yaml
   ```

   Navigate with the arrow keys and toggle files/folders with `Enter`. The resulting YAML contains your `basePath`, `files`, and `folders` selections.

2. **Generate Context via Repomix**

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

   The `generate` command reads the YAML and orchestrates Repomix to build the final context file.

---

### Profile-based Workflow (Quick Start)

#### 1. Create a Profile
A profile defines a reusable set of paths and rules.

```bash
# Create a profile named 'python-project' that includes the 'src' and 'tests' directories
# and excludes any files in '__pycache__' directories.
aicontext profile create python-project src/ tests/ --exclude "__pycache__/*"
```

#### 2. Export Using the Profile
Use the profile's name to generate the context file.

```bash
# Export to markdown
aicontext export output.md --profile python-project

# Export to JSON with a file size limit and check against GPT-4o's token limit
aicontext export context.json --profile python-project --format json --max-size 50000 --model gpt-4o
```

---

### Session-based Workflow

Use this for quick, one-off tasks where a permanent profile isn't needed.

#### 1. Add Files to the Session
Build your context by adding files and directories.

```bash
# Add specific files
aicontext add files src/main.py src/utils.py

# Add a directory recursively
aicontext add files docs/ --recursive
```

#### 2. List and Remove Files (Optional)
Check your current session and remove any unwanted files.

```bash
# List files currently in the session
aicontext list files

# Remove a file
aicontext remove files src/utils.py
```

#### 3. Export the Session
Run the `export` command without the `--profile` flag.

```bash
# Export the current session directly to a file
aicontext export session_output.md
```

---

### Debugging Workflow with `aicontext debug`

Quickly build a debugging context from a stack trace by parsing file paths, resolving them in your local project, and optionally exporting a ready-to-share context file.

Example:

```bash
cat crash.log | aicontext debug from-trace --base-path /path/to/project -o debug_context.md
```

What it does:

- Finds paths like `/path/to/file.py:123`, `in /srv/app/file.php line 89`, `at C:\\\project\\src\\main.ts:42`.
- Resolves them relative to `--base-path` and adds them to the session context.
- Optionally writes a markdown file that includes the original error trace at the top and the exported file contents below.

Options:

- `--base-path, -b` (required): local project root used to resolve paths.
- `--output, -o` (optional): write a combined debug context file.
- `--format, -f` (optional): export format (markdown, json, xml, yaml). The original trace is prepended when using markdown.

---

## Full Command Reference

### Session Management
The "session" is a temporary list of files stored in `context.yaml`.

- `aicontext add files <path>... [-r]`: Add files/directories to the current session. Use `-r` for recursive.
- `aicontext remove files <path>... [--all]`: Remove files from the session. Use `--all` to clear.
- `aicontext list files [-v]`: List files in the session. Use `-v` for verbose output.
- `aicontext import directory <path>`: Import a directory structure into the session, preserving relative paths.

### Profile Management
Profiles are reusable configurations stored in `~/.config/ai-context-manager/profiles/`.

- `aicontext profile create <name> <path>...`: Create a new profile from paths and patterns.
- `aicontext profile list`: List all saved profiles.
- `aicontext profile show <name>`: Show details of a specific profile.
- `aicontext profile update <name>`: Save the current session to a profile (creates if not exists).
- `aicontext profile delete <name>`: Delete a profile.

### Exporting
- `aicontext export <output> [--profile <name>]`: Export files to a formatted context file. If `--profile` is omitted, the current session is used.
  - `--format <fmt>`: Set format (markdown, json, xml, yaml).
  - `--model <name>`: Check token count against a specific model.
  - `--dry-run`: Preview the output without writing a file.

### Debugging
- `aicontext debug from-trace --base-path <path> [-o <output>] [--format <fmt>]`
  - Reads a stack trace from stdin, resolves referenced files within `<path>`, updates the session, and optionally writes a combined debug context.
  - `--base-path, -b` (required): project root for resolution.
  - `--output, -o` (optional): write combined output (recommended: markdown).
  - `--format, -f` (optional): export format (markdown, json, xml, yaml). Original trace is prepended only for markdown.
