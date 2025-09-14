### Project Goal

The objective is to mature the `ai-context-manager` tool into a robust, well-tested, and easy-to-use utility. This involves cleaning up the existing test structure, adding comprehensive tests for all CLI commands, improving the core export workflow to be more intuitive, and overhauling the documentation to be clear and accurate.

---

### Phase 1: Codebase Cleanup and Test Consolidation

**Objective:** Remove obsolete and duplicate test files to create a clean and canonical test suite structure. This prevents confusion and ensures we are testing the correct, current implementation.

**Action:** Delete the following redundant test files from the root `tests/` directory. The correct versions of these tests reside in subdirectories like `tests/commands/` and `tests/core/`.

1.  **DELETE File:** `tests/test_profile_cmd.py`
2.  **DELETE File:** `tests/test_export_cmd.py`
3.  **DELETE File:** `tests/test_profile.py`
4.  **DELETE File:** `tests/test_exporter.py`
5.  **DELETE File:** `tests/test_selector.py`
6.  **DELETE File:** `tests/test_token_counter.py`
7.  **DELETE File:** `test_import_command.py` (This is a standalone script that will be replaced by a proper pytest test in the next phase).

---

### Phase 2: Implement Comprehensive Command Tests

**Objective:** Add dedicated test files for the `add`, `remove`, `list`, and `import` commands, which are currently untested. This will ensure their functionality is correct and prevent future regressions.

**Action 1:** Create a new test file for the `add` command.

**File to Create:** `tests/commands/test_add_cmd.py`

```python
from pathlib import Path
import yaml
from typer.testing import CliRunner

from ai_context_manager.cli import app
from ai_context_manager.config import get_config_dir

runner = CliRunner()

def test_add_single_file(tmp_path: Path):
    """Test adding a single file to the context."""
    config_dir = tmp_path / ".config"
    get_config_dir.cache_clear()
    monkeypatch.setattr("ai_context_manager.config.get_config_dir", lambda: config_dir)
    
    file1 = tmp_path / "file1.txt"
    file1.touch()
    
    result = runner.invoke(app, ["add", "files", str(file1)])
    
    assert result.exit_code == 0
    assert "Added 1 new file(s) to context" in result.output
    
    context_file = config_dir / "context.yaml"
    with open(context_file, 'r') as f:
        context = yaml.safe_load(f)
    
    assert context["files"] == [str(file1.resolve())]

def test_add_directory_recursively(tmp_path: Path, monkeypatch):
    """Test adding a directory recursively."""
    config_dir = tmp_path / ".config"
    get_config_dir.cache_clear()
    monkeypatch.setattr("ai_context_manager.config.get_config_dir", lambda: config_dir)

    dir1 = tmp_path / "dir1"
    dir1.mkdir()
    file1 = dir1 / "file1.txt"
    file1.touch()
    
    subdir = dir1 / "subdir"
    subdir.mkdir()
    file2 = subdir / "file2.txt"
    file2.touch()
    
    result = runner.invoke(app, ["add", "files", str(dir1), "-r"])
    
    assert result.exit_code == 0
    assert "Added 2 new file(s) to context" in result.output
    
    context_file = config_dir / "context.yaml"
    with open(context_file, 'r') as f:
        context = yaml.safe_load(f)
    
    expected_files = sorted([str(file1.resolve()), str(file2.resolve())])
    assert sorted(context["files"]) == expected_files

def test_add_nonexistent_path(tmp_path: Path, monkeypatch):
    """Test adding a path that does not exist."""
    config_dir = tmp_path / ".config"
    get_config_dir.cache_clear()
    monkeypatch.setattr("ai_context_manager.config.get_config_dir", lambda: config_dir)

    result = runner.invoke(app, ["add", "files", "nonexistent/path"])
    
    assert result.exit_code == 0
    assert "Warning: Path does not exist" in result.output
    
    context_file = config_dir / "context.yaml"
    assert not context_file.exists()
```

**Action 2:** Create new test files for the `remove` and `list` commands.

**File to Create:** `tests/commands/test_remove_list_cmd.py`

```python
from pathlib import Path
import yaml
from typer.testing import CliRunner

from ai_context_manager.cli import app
from ai_context_manager.config import get_config_dir

runner = CliRunner()

def setup_context(config_dir: Path, files_to_add: list):
    """Helper to set up a context.yaml file."""
    context_file = config_dir / "context.yaml"
    resolved_files = [str(Path(f).resolve()) for f in files_to_add]
    with open(context_file, 'w') as f:
        yaml.dump({"files": resolved_files}, f)
    return resolved_files

def test_list_and_remove_files(tmp_path: Path, monkeypatch):
    """Test listing files and then removing one."""
    config_dir = tmp_path / ".config"
    get_config_dir.cache_clear()
    monkeypatch.setattr("ai_context_manager.config.get_config_dir", lambda: config_dir)
    
    file1 = tmp_path / "file1.txt"
    file1.touch()
    file2 = tmp_path / "file2.py"
    file2.touch()
    
    # Setup context with two files
    setup_context(config_dir, [file1, file2])
    
    # Test 'list'
    result = runner.invoke(app, ["list", "files"])
    assert result.exit_code == 0
    assert str(file1.resolve()) in result.output
    assert str(file2.resolve()) in result.output
    
    # Test 'remove'
    result = runner.invoke(app, ["remove", "files", str(file1)])
    assert result.exit_code == 0
    assert f"- {file1.resolve()}" in result.output
    
    # List again to confirm removal
    result = runner.invoke(app, ["list", "files"])
    assert result.exit_code == 0
    assert str(file1.resolve()) not in result.output
    assert str(file2.resolve()) in result.output

def test_remove_all_files(tmp_path: Path, monkeypatch):
    """Test removing all files with the --all flag."""
    config_dir = tmp_path / ".config"
    get_config_dir.cache_clear()
    monkeypatch.setattr("ai_context_manager.config.get_config_dir", lambda: config_dir)
    
    (tmp_path / "file1.txt").touch()
    (tmp_path / "file2.py").touch()
    setup_context(config_dir, [tmp_path / "file1.txt", tmp_path / "file2.py"])
    
    result = runner.invoke(app, ["remove", "files", "--all"])
    assert result.exit_code == 0
    assert "Removed all 2 files from context" in result.output

    # List to confirm it's empty
    result = runner.invoke(app, ["list", "files"])
    assert "No files in context" in result.output
```

**Action 3:** Create a new test file for the `import` command, replacing the old standalone script.

**File to Create:** `tests/commands/test_import_cmd.py`

```python
from pathlib import Path
import yaml
from typer.testing import CliRunner

from ai_context_manager.cli import app
from ai_context_manager.config import get_config_dir

runner = CliRunner()

def test_import_directory(tmp_path: Path, monkeypatch):
    """Test importing a directory structure."""
    config_dir = tmp_path / ".config"
    get_config_dir.cache_clear()
    monkeypatch.setattr("ai_context_manager.config.get_config_dir", lambda: config_dir)
    
    # Create a project structure to import
    project_dir = tmp_path / "my_project"
    src_dir = project_dir / "src"
    src_dir.mkdir(parents=True)
    (src_dir / "main.py").touch()
    (project_dir / "README.md").touch()
    
    result = runner.invoke(app, ["import", "directory", str(project_dir), "--base-path", str(project_dir)])
    
    assert result.exit_code == 0
    assert "Added 2 new file(s) to context" in result.output
    
    context_file = config_dir / "context.yaml"
    with open(context_file, 'r') as f:
        context = yaml.safe_load(f)
    
    # Paths should be relative to the specified base_path
    expected_files = sorted(["src/main.py", "README.md"])
    assert sorted(context["files"]) == expected_files
```

---

### Phase 3: Improve Core Export Workflow

**Objective:** Enhance the `export` command so it can directly export the current session context without requiring the user to first save it as a profile. This removes significant user friction.

**Action:** Overwrite the `ai_context_manager/commands/export_cmd.py` file with the refactored code below. The key change is making `--profile` optional and adding logic to create a temporary profile from the session if no profile name is provided.

**File to Modify:** `ai_context_manager/commands/export_cmd.py`

```python
"""Export command for AI Context Manager."""

from pathlib import Path
from typing import Optional, List, Any, Dict
from datetime import datetime

import typer
import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ai_context_manager.core.profile import Profile, PathEntry
from ai_context_manager.core.exporter import ContextExporter
from ai_context_manager.utils.token_counter import check_token_limits, format_token_count
from ai_context_manager.config import CLI_CONTEXT_SETTINGS, get_config_dir

app = typer.Typer(context_settings=CLI_CONTEXT_SETTINGS)
console = Console()


def load_session_context() -> Dict[str, Any]:
    """Load the current session context from a YAML file."""
    config_dir = get_config_dir()
    context_file = config_dir / "context.yaml"
    if not context_file.exists():
        return {"files": []}
    with open(context_file, 'r') as f:
        return yaml.safe_load(f) or {"files": []}


@app.command("export")
def export_context(
    output: Path = typer.Argument(..., help="Output file path"),
    profile_name: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile name to use. If not provided, exports the current session."),
    format: str = typer.Option("markdown", "--format", "-f", help="Export format: markdown, json, xml, yaml"),
    max_size: int = typer.Option(102400, "--max-size", "-s", help="Maximum file size in bytes"),
    include_binary: bool = typer.Option(False, "--include-binary", "-b", help="Include binary files"),
    model: str = typer.Option("gpt-4", "--model", "-m", help="AI model for token limit checking"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be exported without creating file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed information"),
):
    """Export selected files to an AI context format from a profile or the current session."""
    
    profile_obj: Profile
    
    if profile_name:
        try:
            profile_obj = Profile.load(profile_name)
        except FileNotFoundError:
            console.print(f"[red]Error: Profile '{profile_name}' not found.[/red]")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[red]Error loading profile: {e}[/red]")
            raise typer.Exit(1)
    else:
        # Create a temporary profile from the current session
        session_context = load_session_context()
        session_files = session_context.get("files", [])
        if not session_files:
            console.print("[yellow]No files in the current session to export. Use 'aicontext add' to add files.[/yellow]")
            raise typer.Exit()
        
        profile_obj = Profile(
            name="current-session",
            created=datetime.now(),
            modified=datetime.now(),
            base_path=Path.cwd(),
            paths=[PathEntry(path=Path(f), is_directory=False, recursive=False) for f in session_files],
            exclude_patterns=[]
        )
        profile_name = "current session" # For display purposes

    # Validate format
    valid_formats = ["markdown", "json", "xml", "yaml"]
    if format.lower() not in valid_formats:
        console.print(f"[red]Error: Invalid format '{format}'. Valid formats: {', '.join(valid_formats)}[/red]")
        raise typer.Exit(1)
    
    exporter = ContextExporter(profile_obj)
    
    if dry_run:
        console.print(f"\n[bold blue]Dry Run - Using: {profile_name}[/bold blue]")
        selected_files = exporter.selector.select_files(
            max_file_size=max_size,
            include_binary=include_binary,
        )
        if not selected_files:
            console.print("[yellow]No files would be exported.[/yellow]")
            return
            
        summary = exporter.selector.get_summary(selected_files)
        console.print(f"\n[bold]Would export {len(selected_files)} files:[/bold]")
        
        from ai_context_manager.utils.token_counter import count_tokens
        estimated_content = exporter._export_markdown(selected_files, summary)
        tokens = count_tokens(estimated_content)
        formatted_tokens = format_token_count(tokens)
        
        console.print(f"Estimated tokens: {formatted_tokens}")
        limit_check = check_token_limits(tokens, model)
        if limit_check["is_within_limits"]:
            console.print(f"[green]✓ Within {model} limits ({limit_check['percentage']:.1f}%)[/green]")
        else:
            console.print(f"[red]✗ Exceeds {model} limits ({limit_check['percentage']:.1f}%)[/red]")
        return
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Exporting files...", total=None)
        
        result = exporter.export_to_file(
            output_path=output,
            format=format,
            max_file_size=max_size,
            include_binary=include_binary,
        )
    
    if result["success"]:
        console.print(f"\n[green]✓ {result['message']}[/green]")
        console.print(f"\n[bold]Export Summary:[/bold]")
        console.print(f"Files exported: {len(result['files'])}")
        console.print(f"Total size: {result['total_size_human']}")
        console.print(f"Total tokens: {format_token_count(result['total_tokens'])}")
        
        limit_check = check_token_limits(result["total_tokens"], model)
        if limit_check["is_within_limits"]:
            console.print(f"[green]✓ Within {model} limits ({limit_check['percentage']:.1f}%)[/green]")
        else:
            console.print(f"[red]✗ Exceeds {model} limits ({limit_check['percentage']:.1f}%)[/red]")
            console.print(f"[yellow]Consider using a model with higher limits or reducing file selection.[/yellow]")
        
        if verbose:
            console.print(f"\n[dim]Output file: {result['output_path']}[/dim]")
    else:
        console.print(f"\n[red]✗ Export failed: {result['message']}[/red]")
        raise typer.Exit(1)

@app.command("formats")
def list_formats():
    """List available export formats."""
    # This command remains unchanged
    ...

@app.command("models")
def list_models():
    """List AI models with token limits."""
    # This command remains unchanged
    ...

if __name__ == "__main__":
    app()
```

---

### Phase 4: Documentation Overhaul

**Objective:** Rewrite the `README.md` to clearly explain the two primary workflows (profile-based and session-based) and provide accurate, easy-to-follow examples for all major commands.

**Action:** Overwrite the `README.md` file with the new, comprehensive version below.

**File to Modify:** `README.md`

```markdown
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
- `aicontext profile import <file>`: Import a profile from a YAML file.
- `aicontext profile export <name>`: Export a profile to a YAML file.

### Exporting
- `aicontext export <output_path> [--profile <name>]`: Export a profile or the current session to a context file.
- `aicontext export formats`: List available export formats.
- `aicontext export models`: List AI models and their token limits.

## Development

### Setup Development Environment
```bash
# Install uv (if you haven't already)
pip install uv
# Create and activate virtual environment
uv venv
source .venv/bin/activate
# Install dependencies
uv pip install -e .[dev]
```

### Running Tests
```bash
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
```

---

### Phase 5: Final Validation

**Objective:** Ensure the entire codebase is consistent, well-formatted, and passes all checks after the extensive refactoring.

**Action:** Run the full suite of quality assurance tools.

**Commands to execute:**
1.  `pytest`
2.  `ruff format .`
3.  `ruff check . --fix`
4.  `mypy ai_context_manager/`

This completes the comprehensive implementation plan. Once executed, the tool will be significantly more robust, tested, and user-friendly.

