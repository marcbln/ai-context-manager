# AiContextManager - Implementation Plan

## Project Overview
A Python tool for selectively choosing files and folders to create AI-friendly context files, with reusable profile management.

## Phase 1: Project Foundation & Core Structure

### 1.1 Project Setup
```bash
# Initialize project structure
mkdir ai_context_manager
cd ai_context_manager
uv venv
source .venv/bin/activate
```

### 1.2 Create Project Structure
```
/home/marc/devel/ai-context-manager/
├── .venv/
├── pyproject.toml
├── README.md
├── .gitignore
├── .env.example
└── ai_context_manager/
    ├── __init__.py
    ├── cli.py              # Main CLI entry point using Typer
    ├── core/
    │   ├── __init__.py
    │   ├── profile.py      # Profile management logic
    │   ├── selector.py     # File/folder selection logic
    │   └── exporter.py     # Export to context file logic
    ├── utils/
    │   ├── __init__.py
    │   ├── file_utils.py   # File system operations
    │   └── token_counter.py # Token estimation utilities
    ├── commands/
    │   ├── __init__.py
    │   ├── add_cmd.py      # Add files/folders to selection
    │   ├── remove_cmd.py   # Remove from selection
    │   ├── profile_cmd.py  # Profile management commands
    │   ├── export_cmd.py   # Export context file
    │   └── list_cmd.py     # List selections/profiles
    └── config.py           # Configuration handling
```

### 1.3 Create `pyproject.toml`
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "ai-context-manager"
version = "0.1.0"
description = "Manage and export file selections as AI context"
requires-python = ">=3.12"
license = "MIT"
dependencies = [
    "typer[all]>=0.9.0",
    "rich>=13.7.0",
    "pyyaml>=6.0",
    "python-dotenv>=1.0.0",
    "pathspec>=0.12.0",  # For gitignore-style patterns
]

[project.scripts]
aicontext = "ai_context_manager.cli:app"

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "black>=24.0.0",
    "mypy>=1.8.0",
    "ruff>=0.3.0",
]
```

### 1.4 Install Dependencies
```bash
uv pip install -e ".[dev]"
```

## Phase 2: Core Data Models & Configuration

### 2.1 Configuration Module (`config.py`)
- Define configuration paths:
  - Config directory: `~/.config/aicontext/`
  - Profiles directory: `~/.config/aicontext/profiles/`
  - Default settings file: `~/.config/aicontext/config.yaml`
- Load/save configuration
- Handle defaults for exclude patterns

### 2.2 Profile Data Model (`core/profile.py`)
```python
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path
from datetime import datetime

@dataclass
class PathEntry:
    path: Path
    is_directory: bool
    recursive: bool = True

@dataclass
class Profile:
    name: str
    created: datetime
    modified: datetime
    base_path: Optional[Path]
    paths: List[PathEntry]
    exclude_patterns: List[str]
    
    def to_dict() -> dict: ...
    def from_dict(data: dict) -> 'Profile': ...
    def save(filepath: Path) -> None: ...
    def load(filepath: Path) -> 'Profile': ...
```

### 2.3 File Utilities (`utils/file_utils.py`)
- `resolve_path()`: Convert relative to absolute paths
- `get_file_size()`: Get file size in bytes
- `count_lines()`: Count lines in text files
- `is_text_file()`: Check if file is text (not binary)
- `matches_patterns()`: Check if path matches exclude patterns

## Phase 3: CLI Foundation with Typer

### 3.1 Main CLI App (`cli.py`)
```python
import typer
from rich.console import Console
from ai_context_manager.commands import (
    add_cmd, remove_cmd, profile_cmd, 
    export_cmd, list_cmd
)

app = typer.Typer(
    name="aicontext",
    help="Manage file selections for AI context export"
)
console = Console()

# Register subcommands
app.command("add")(add_cmd.add)
app.command("remove")(remove_cmd.remove)
app.command("list")(list_cmd.list_selection)
app.command("export")(export_cmd.export)

# Profile subcommands
profile_app = typer.Typer(help="Manage selection profiles")
app.add_typer(profile_app, name="profile")
profile_app.command("save")(profile_cmd.save)
profile_app.command("load")(profile_cmd.load)
profile_app.command("list")(profile_cmd.list_profiles)
profile_app.command("delete")(profile_cmd.delete)

if __name__ == "__main__":
    app()
```

### 3.2 Basic Commands Implementation

#### `add_cmd.py`
- Add file: `aicontext add path/to/file.py`
- Add directory: `aicontext add path/to/dir/`
- Support multiple paths: `aicontext add file1.py dir1/ file2.js`
- Store in temporary session file

#### `list_cmd.py`
- Show current selection with file sizes
- Display as tree structure
- Show estimated character/line count

#### `export_cmd.py`
- Export current selection: `aicontext export -o context.txt`
- Export from profile: `aicontext export --profile backend -o context.txt`

## Phase 4: Profile Management

### 4.1 Profile Commands (`commands/profile_cmd.py`)
- `save`: Save current selection as named profile
- `load`: Load profile into current selection
- `list`: Show all saved profiles with metadata
- `delete`: Remove a saved profile
- `show`: Display details of a specific profile

### 4.2 Profile Storage
- Store as YAML files in `~/.config/aicontext/profiles/`
- Filename: `{profile_name}.yaml`
- Include metadata: creation date, last modified, description

## Phase 5: Export Functionality

### 5.1 Exporter Module (`core/exporter.py`)
```python
class ContextExporter:
    def __init__(self, paths: List[PathEntry], exclude_patterns: List[str]):
        ...
    
    def generate_tree_structure() -> str:
        """Generate tree visualization of included files"""
        ...
    
    def collect_files() -> List[Path]:
        """Recursively collect all files to include"""
        ...
    
    def export(output_path: Path) -> None:
        """Generate the context file"""
        ...
```

### 5.2 Export Format
- Header with metadata (similar to repomix)
- Directory structure visualization
- File contents with clear separators
- Summary statistics (files, lines, characters)

## Phase 6: Enhanced Features

### 6.1 Token Counting (`utils/token_counter.py`)
```python
def estimate_tokens(text: str, model: str = "gpt-4") -> int:
    """Estimate token count for given text"""
    # Use tiktoken or simple approximation
    ...
```

### 6.2 Interactive Mode (using InquirerPy)
- `aicontext interactive`: Launch interactive file selector
- Navigate filesystem with arrow keys
- Space to select/deselect
- Preview selected files
- Save as profile or export directly

### 6.3 Smart Defaults
- Auto-detect and use `.gitignore` patterns
- Common exclude patterns (`.pyc`, `__pycache__`, `node_modules`, etc.)
- Respect `.aicontextignore` file if present

## Phase 7: Testing & Quality

### 7.1 Test Structure
```
tests/
├── test_profile.py
├── test_selector.py
├── test_exporter.py
├── test_commands.py
└── fixtures/
    └── sample_project/
```

### 7.2 Test Coverage Goals
- Unit tests for all core modules
- Integration tests for CLI commands
- Test profile save/load cycle
- Test export with various file types
- Edge cases: empty selections, missing files, permission errors

## Phase 8: Documentation & Polish

### 8.1 Documentation
- Comprehensive README with examples
- Inline help for all commands
- Example profiles in `examples/` directory

### 8.2 Error Handling
- Graceful handling of:
  - Missing files/directories
  - Permission errors
  - Invalid profile names
  - Disk space issues
- Rich formatting for error messages

### 8.3 Performance Optimization
- Lazy loading for large directories
- Progress bars for long operations
- Caching file metadata

## Implementation Order & Timeline

### Week 1: Foundation
1. Project setup (Phase 1)
2. Core data models (Phase 2)
3. Basic CLI structure (Phase 3.1)

### Week 2: Core Functionality
1. Add/List commands (Phase 3.2)
2. Basic export functionality (Phase 5)
3. Initial tests

### Week 3: Profile Management
1. Profile commands (Phase 4)
2. Profile storage/loading
3. Export with profiles

### Week 4: Enhancement & Polish
1. Token counting (Phase 6.1)
2. Smart defaults (Phase 6.3)
3. Error handling & documentation

### Week 5: Interactive Mode (Optional)
1. Interactive file selector (Phase 6.2)
2. Final testing & refinement

## Success Criteria for MVP

- [ ] Can add individual files and directories to selection
- [ ] Can save selections as named profiles
- [ ] Can export selections to a single context file
- [ ] Respects exclude patterns (gitignore-style)
- [ ] Shows file/token statistics
- [ ] Has comprehensive CLI help
- [ ] Includes basic error handling
- [ ] Passes all unit tests with >80% coverage

## Future Enhancements (Post-MVP)

1. **GUI Version**: tkinter or PyQt interface
2. **Diff Mode**: Show what changed since last export
3. **Templates**: Pre-defined profile templates for common frameworks
4. **Cloud Sync**: Sync profiles across machines
5. **IDE Plugins**: VS Code extension for quick context export
6. **Multiple Export Formats**: Markdown, JSON, XML
7. **Context Splitting**: Auto-split large contexts into chunks
8. **AI Integration**: Direct upload to OpenAI, Claude, etc.

