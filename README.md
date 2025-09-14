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
pip install .
```

## Workflows

AI Context Manager supports two primary workflows:

1.  **Profile-based Workflow (Recommended)**: Create a named profile with your desired file paths and exclusion rules. Use this profile to generate context files consistently.
2.  **Session-based Workflow**: Interactively add and remove files for a quick, one-time export without creating a permanent profile.

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
