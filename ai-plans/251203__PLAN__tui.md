## Problem Description
The current `ai-context-manager` relies on CLI commands (`add`, `remove`) or profile definitions to build context. Users need a more intuitive, interactive way to select files and folders from a directory tree (TUI). Additionally, the system lacks a direct integration with [Repomix](https://github.com/yamadashy/repomix) (formerly Repopack) to immediately convert that selection into a final context file for LLMs.

This plan implements:
1.  **`aicontext select`**: A TUI to browse, filter, and checkmark files/folders, saving the state to a YAML file.
2.  **`aicontext generate`**: A command to read that YAML file and orchestrate `repomix` to generate the final output.

---

## Phase 1: Environment & Dependencies

**Objective**: Update the project to support TUI libraries.

1.  **Update `pyproject.toml`**:
    Add `textual` to the project dependencies.

    ```toml
    # pyproject.toml
    [project]
    # ... existing config ...
    dependencies = [
        "typer[all]>=0.9.0",
        "rich>=13.7.0",
        "pyyaml>=6.0",
        "python-dotenv>=1.0.0",
        "pathspec>=0.12.0",
        "textual>=0.70.0",  # <--- NEW DEPENDENCY
    ]
    ```

2.  **Install/Sync Environment**:
    ```bash
    uv pip install -e .
    ```

---

## Phase 2: Implement TUI Selection Command

**Objective**: Create the interactive terminal interface for selecting files.

1.  **Create `ai_context_manager/commands/select_cmd.py`**:

```python
"""Interactive TUI for selecting files and folders."""
import yaml
from pathlib import Path
from typing import Set, List, Optional

import typer
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import DirectoryTree, Footer, Header, Input, Button, Label
from textual.binding import Binding
from textual.events import Mount

from ..config import CLI_CONTEXT_SETTINGS

app = typer.Typer(help="Interactive file selection TUI", context_settings=CLI_CONTEXT_SETTINGS)

class SelectableDirectoryTree(DirectoryTree):
    """A DirectoryTree that allows selecting nodes."""

    def __init__(self, path: str, **kwargs):
        super().__init__(path, **kwargs)
        self.selected_paths: Set[Path] = set()

    def on_tree_node_selected(self, event: DirectoryTree.NodeSelected) -> None:
        """Handle node selection (toggle inclusion)."""
        event.stop()
        node = event.node
        path = node.data.path

        # Toggle selection
        if path in self.selected_paths:
            self.selected_paths.remove(path)
            if node.label.plain.startswith("[x] "):
                 node.set_label(node.label.plain.replace("[x] ", ""))
            node.remove_class("is-selected")
        else:
            self.selected_paths.add(path)
            node.set_label(f"[x] {node.label.plain}")
            node.add_class("is-selected")

    def filter_tree(self, query: str):
        """Basic name filtering (visual only)."""
        # Note: Deep filtering in DirectoryTree requires custom filtering logic 
        # on the load_directory method. For MVP, we highlight matches or 
        # simplistic filtering can be added here if extended.
        pass

class SelectionApp(App):
    """Textual App for file selection."""

    CSS = """
    Screen { layout: vertical; }
    .header-box { height: auto; dock: top; padding: 1; background: $primary-background-darken-1; }
    Input { margin-bottom: 1; }
    DirectoryTree { border: solid $accent; height: 1fr; scrollbar-gutter: stable; }
    .is-selected { color: $success; text-style: bold; }
    .footer-box { height: auto; dock: bottom; padding: 1; background: $primary-background-darken-1; align: right middle; }
    Button { margin-left: 1; }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("s", "save_and_quit", "Save & Quit"),
    ]

    def __init__(self, base_path: Path, output_file: Path, preselected: dict = None):
        super().__init__()
        self.base_path = base_path
        self.output_file = output_file
        self.preselected = preselected or {}
        self.tree_widget = SelectableDirectoryTree(str(base_path), id="file_tree")

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Label("Search (Highlight):"),
            Input(placeholder="Highlight filenames...", id="search_box"),
            classes="header-box"
        )
        yield self.tree_widget
        yield Container(
            Button("Cancel", variant="error", id="cancel"),
            Button("Save Selection (S)", variant="primary", id="save"),
            classes="footer-box"
        )
        yield Footer()

    def on_mount(self, event: Mount) -> None:
        """Load previous selections if provided."""
        # Future improvement: Traverse tree to visually checkmark preselected files
        pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            self.action_save_and_quit()
        elif event.button.id == "cancel":
            self.exit(result=False)

    def action_save_and_quit(self):
        """Save selection to YAML and exit."""
        files = []
        folders = []
        
        for path in self.tree_widget.selected_paths:
            # Convert to relative paths
            try:
                rel_path = path.relative_to(self.base_path)
            except ValueError:
                rel_path = path # Should not happen if within tree
            
            if path.is_file():
                files.append(str(rel_path))
            elif path.is_dir():
                folders.append(str(rel_path))

        files.sort()
        folders.sort()

        data = {
            "basePath": str(self.base_path.resolve()),
            "files": files,
            "folders": folders
        }

        with open(self.output_file, "w") as f:
            yaml.dump(data, f, sort_keys=False)
        
        self.exit(result=True)

@app.command()
def start(
    path: Path = typer.Argument(".", help="Base path to scan", exists=True, file_okay=False),
    output: Path = typer.Option("selection.yaml", "--output", "-o", help="Output YAML file"),
):
    """
    Launch the interactive TUI for file selection.
    """
    base_path = path.resolve()
    
    # Load existing if available to prepopulate (logic to be added in on_mount)
    preselected = {}
    if output.exists():
        try:
            with open(output, 'r') as f:
                preselected = yaml.safe_load(f) or {}
        except Exception:
            pass

    tui = SelectionApp(base_path=base_path, output_file=output, preselected=preselected)
    result = tui.run()

    if result:
        typer.echo(f"Selection saved to: {output}")
    else:
        typer.echo("Selection cancelled.")
```

---

## Phase 3: Implement Repomix Wrapper Command

**Objective**: Create a command that invokes `repomix` based on the YAML list created in Phase 2.

1.  **Create `ai_context_manager/commands/generate_cmd.py`**:

```python
"""Command to generate context via Repomix using a selection file."""
import shutil
import subprocess
import typer
import yaml
from pathlib import Path
from rich.console import Console

from ..config import CLI_CONTEXT_SETTINGS

app = typer.Typer(help="Generate context using repomix", context_settings=CLI_CONTEXT_SETTINGS)
console = Console()

@app.command("repomix")
def generate_repomix(
    selection_file: Path = typer.Argument(..., help="The YAML selection file created by 'select'"),
    output: Path = typer.Option("repomix-output.xml", "--output", "-o", help="Final context output file"),
    style: str = typer.Option("xml", "--style", help="Repomix output style (xml, markdown, plain)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show repomix output"),
):
    """
    Execute Repomix using the file lists from a selection YAML file.
    """
    if not selection_file.exists():
        console.print(f"[red]Error: Selection file {selection_file} not found.[/red]")
        raise typer.Exit(1)

    # Check for repomix availability
    repomix_bin = shutil.which("repomix")
    if not repomix_bin:
        console.print("[red]Error: 'repomix' executable not found in PATH.[/red]")
        console.print("Please install it via: [bold]npm install -g repomix[/bold]")
        raise typer.Exit(1)

    # Load selection data
    try:
        with open(selection_file, 'r') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        console.print(f"[red]Error parsing YAML: {e}[/red]")
        raise typer.Exit(1)

    base_path = Path(data.get("basePath", "."))
    files = data.get("files", [])
    folders = data.get("folders", [])

    if not files and not folders:
        console.print("[yellow]Warning: No files or folders found in selection.[/yellow]")
        raise typer.Exit(0)

    # Construct Repomix arguments
    # Repomix usually takes patterns. We will construct comma-separated includes.
    include_patterns = []
    include_patterns.extend(files)
    # For folders, we ensure we get contents
    for folder in folders:
        include_patterns.append(f"{folder}/**")

    includes_str = ",".join(include_patterns)

    cmd = [
        "repomix",
        "--output", str(output.resolve()),
        "--style", style,
        "--include", includes_str
    ]

    console.print(f"[blue]Running Repomix in {base_path}...[/blue]")
    if verbose:
        console.print(f"[dim]Command: {' '.join(cmd)}[/dim]")

    try:
        # Run repomix inside the basePath so relative paths work
        result = subprocess.run(
            cmd, 
            cwd=base_path, 
            capture_output=not verbose, 
            text=True
        )
        
        if result.returncode == 0:
            console.print(f"[green]Success! Context generated at: {output}[/green]")
        else:
            console.print("[red]Repomix failed:[/red]")
            console.print(result.stderr)
            raise typer.Exit(result.returncode)

    except Exception as e:
        console.print(f"[red]Execution error: {e}[/red]")
        raise typer.Exit(1)
```

---

## Phase 4: Integration

**Objective**: Register the new commands in the main CLI entry point.

1.  **Modify `ai_context_manager/cli.py`**:

```python
# ... imports ...
from ai_context_manager.commands import (
    # ... existing ...
    select_cmd,
    generate_cmd
)

# ... existing app setup ...

# Add subcommands
app.add_typer(select_cmd.app, name="select", help="Interactive selection TUI")
app.add_typer(generate_cmd.app, name="generate", help="Generate context via external tools")

# ... existing code ...
```

---

## Phase 5: Testing

**Objective**: Ensure the logic holds up without needing manual TUI interaction for tests.

1.  **Create `tests/commands/test_generate_cmd.py`**:

```python
import yaml
from pathlib import Path
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from ai_context_manager.cli import app

runner = CliRunner()

def test_generate_repomix_success(tmp_path):
    """Test successful repomix invocation."""
    
    # 1. Create dummy selection.yaml
    selection_file = tmp_path / "selection.yaml"
    data = {
        "basePath": str(tmp_path),
        "files": ["main.py"],
        "folders": ["src"]
    }
    with open(selection_file, 'w') as f:
        yaml.dump(data, f)

    # 2. Mock shutil.which and subprocess.run
    with patch("shutil.which", return_value="/usr/bin/repomix"), \
         patch("subprocess.run") as mock_run:
        
        mock_run.return_value = MagicMock(returncode=0)
        
        result = runner.invoke(app, [
            "generate", "repomix", 
            str(selection_file), 
            "--output", "context.xml"
        ])

        assert result.exit_code == 0
        assert "Success!" in result.output
        
        # 3. Verify arguments passed to repomix
        args, kwargs = mock_run.call_args
        cmd_list = args[0]
        assert "repomix" in cmd_list
        # Check if includes were merged correctly
        assert any("main.py" in x for x in cmd_list)
        assert any("src/**" in x for x in cmd_list)
        # Check CWD
        assert kwargs["cwd"] == Path(str(tmp_path))

def test_generate_missing_binary(tmp_path):
    """Test error when repomix is not installed."""
    selection_file = tmp_path / "selection.yaml"
    selection_file.touch()
    
    with patch("shutil.which", return_value=None):
        result = runner.invoke(app, ["generate", "repomix", str(selection_file)])
        assert result.exit_code == 1
        assert "repomix' executable not found" in result.output
```

---

## Phase 6: Documentation Update

**Objective**: Update `README.md` to reflect new workflows.

1.  **Add "Interactive Workflow" section**:

```markdown
## Interactive Selection & Generation

Use the interactive TUI to visually select files and immediately generate a context file using Repomix.

### 1. Select Files
Launch the interactive file browser. Use arrow keys to navigate and `Enter` to select/deselect files.

```bash
aicontext select . -o my-selection.yaml
```

This creates a YAML file containing your `basePath` and lists of selected files and folders.

### 2. Generate Context
Feed the selection file into the generator to run Repomix.

```bash
# Requires repomix installed (npm install -g repomix)
aicontext generate repomix my-selection.yaml --output context.xml --style xml
```

