### Project Goal

Implement a new `aicontext init` command to initialize or reset the user's session context. This involves creating a dedicated command file, integrating it into the main CLI application, and adding corresponding unit tests to ensure its correctness and prevent regressions. The main `cli.py` file will remain clean, only serving to orchestrate the subcommands.

---

### Phase 1: Create the `init` Command Logic

**Objective:** Implement the core logic for the `init` command in a new, separate file, following the project's established command structure.

1.  **Create the Command File**
    *   In the `ai_context_manager/commands/` directory, create a new file named `init_cmd.py`.

2.  **Implement the Command Logic in `init_cmd.py`**
    *   Populate `ai_context_manager/commands/init_cmd.py` with the following code. This code defines the `init` command, handles the creation of `context.yaml`, and includes a confirmation prompt if the file already exists.

    ```python
    """Initialize session context command."""
    import typer
    import yaml
    from rich.console import Console

    from ..config import get_config_dir, CLI_CONTEXT_SETTINGS

    app = typer.Typer(help="Initialize or reset the session context.", context_settings=CLI_CONTEXT_SETTINGS)
    console = Console()

    @app.command(name="init")
    def init_command():
        """
        Initialize the session context.

        This command creates an empty context.yaml file in the configuration directory.
        This file is used to store the list of files for the current session.
        If the file already exists, it will prompt for confirmation before overwriting.
        """
        config_dir = get_config_dir()
        context_file = config_dir / "context.yaml"

        if context_file.exists():
            overwrite = typer.confirm(
                f"Session context file already exists at {context_file}.\n"
                "Overwrite and start a new session?"
            )
            if not overwrite:
                console.print("[yellow]Initialization cancelled.[/yellow]")
                raise typer.Abort()

        context = {"files": []}
        try:
            with open(context_file, "w") as f:
                yaml.dump(context, f, default_flow_style=False)
            console.print(f"[green]✓ Initialized empty session context at: {context_file}[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to initialize session context: {e}[/red]")
            raise typer.Exit(1)

    ```

---

### Phase 2: Integrate the New Command into the Main CLI

**Objective:** Register the new `init` command with the main `aicontext` application so it becomes available to the end-user.

1.  **Modify `ai_context_manager/cli.py`**
    *   Open the main CLI entry point file: `ai_context_manager/cli.py`.

2.  **Import and Register the `init` Subcommand**
    *   Add an import for the new `init_cmd.py` module.
    *   Register it using `app.add_typer()`. To maintain a logical order, place it near the top with other session-management commands.

    ```python
    """Main CLI entry point for AI Context Manager."""

    import typer
    from rich.console import Console

    from ai_context_manager.commands.add_cmd import app as add_app
    from ai_context_manager.commands.export_cmd import app as export_app
    from ai_context_manager.commands.import_cmd import app as import_app
    from ai_context_manager.commands.list_cmd import app as list_app
    from ai_context_manager.commands.profile_cmd import app as profile_app
    from ai_context_manager.commands.remove_cmd import app as remove_app
    from ai_context_manager.commands.init_cmd import app as init_app  # <-- ADD THIS LINE
    from ai_context_manager.config import CLI_CONTEXT_SETTINGS

    app = typer.Typer(
        name="aicontext",
        help="AI Context Manager - Export codebases for AI analysis",
        add_completion=False,
        context_settings=CLI_CONTEXT_SETTINGS,
    )
    console = Console()

    # Add subcommands
    app.add_typer(init_app, name="init") # <-- ADD THIS LINE (name="init" is redundant but explicit)
    app.add_typer(add_app, name="add", help="Add files to the current session context")
    app.add_typer(remove_app, name="remove", help="Remove files from the current session context")
    app.add_typer(list_app, name="list", help="List files in the current session context")
    app.add_typer(export_app, name="export", help="Export files to AI context format")
    app.add_typer(profile_app, name="profile", help="Manage export profiles")
    app.add_typer(import_app, name="import", help="Import files from directory structure")


    @app.command()
    def version():
        """Show version information."""
        console.print("AI Context Manager v0.1.0")


    @app.callback()
    def main():
        """AI Context Manager - Export codebases for AI analysis."""
        pass


    if __name__ == "__main__":
        app()
    ```
    *Note: Since the command is defined as `init` in `init_cmd.py`, you can simply use `app.add_typer(init_app)`. The name will be inferred correctly. Adding `name="init"` is for explicit clarity.*

---

### Phase 3: Add Unit Tests for the `init` Command

**Objective:** Create comprehensive unit tests to validate the `init` command's functionality, including file creation, overwriting, and cancellation.

1.  **Create a New Test File**
    *   In the `tests/commands/` directory, create a new file named `test_init_cmd.py`.

2.  **Implement Unit Tests**
    *   Populate `tests/commands/test_init_cmd.py` with tests for the following scenarios:
        *   Successful creation of a new `context.yaml` file.
        *   Confirmation prompt when the file already exists.
        *   Successful overwrite of an existing file when confirmed.
        *   Cancellation of the operation when overwrite is declined.

    ```python
    from pathlib import Path
    import yaml
    from typer.testing import CliRunner

    from ai_context_manager.cli import app
    from ai_context_manager.config import get_config_dir

    runner = CliRunner()

    def test_init_creates_context_file(tmp_path: Path, monkeypatch):
        """Test that `init` creates a new, empty context.yaml file."""
        config_dir = tmp_path / ".config"
        get_config_dir.cache_clear()
        monkeypatch.setattr("ai_context_manager.config.get_config_dir", lambda: config_dir)

        result = runner.invoke(app, ["init"])

        assert result.exit_code == 0
        assert "Initialized empty session context" in result.output

        context_file = config_dir / "context.yaml"
        assert context_file.exists()

        with open(context_file, 'r') as f:
            context = yaml.safe_load(f)
        assert context == {"files": []}

    def test_init_overwrite_confirmed(tmp_path: Path, monkeypatch):
        """Test that `init` overwrites an existing context file after confirmation."""
        config_dir = tmp_path / ".config"
        config_dir.mkdir()
        context_file = config_dir / "context.yaml"
        with open(context_file, 'w') as f:
            yaml.dump({"files": ["old_file.txt"]}, f)

        get_config_dir.cache_clear()
        monkeypatch.setattr("ai_context_manager.config.get_config_dir", lambda: config_dir)

        # Simulate user typing "y" and pressing Enter
        result = runner.invoke(app, ["init"], input="y\n")

        assert result.exit_code == 0
        assert "Initialized empty session context" in result.output

        with open(context_file, 'r') as f:
            context = yaml.safe_load(f)
        assert context == {"files": []}

    def test_init_overwrite_cancelled(tmp_path: Path, monkeypatch):
        """Test that `init` does not overwrite an existing file if cancelled."""
        config_dir = tmp_path / ".config"
        config_dir.mkdir()
        context_file = config_dir / "context.yaml"
        with open(context_file, 'w') as f:
            yaml.dump({"files": ["old_file.txt"]}, f)

        get_config_dir.cache_clear()
        monkeypatch.setattr("ai_context_manager.config.get_config_dir", lambda: config_dir)

        # Simulate user typing "n" and pressing Enter
        result = runner.invoke(app, ["init"], input="n\n")

        assert result.exit_code == 1  # Aborted
        assert "Initialization cancelled" in result.output

        with open(context_file, 'r') as f:
            context = yaml.safe_load(f)
        assert context == {"files": ["old_file.txt"]} # Should be unchanged
    ```

---

### Phase 4: Final Verification

**Objective:** Manually run the commands and the test suite to confirm that the new feature is working correctly and all existing functionality remains intact.

1.  **Run the Full Test Suite**
    *   From the project root, execute `pytest` to ensure all new and existing tests pass.
    ```bash
    pytest
    ```

2.  **Perform Manual End-to-End Test**
    *   Execute the commands in your terminal to simulate the user workflow:
    ```bash
    # 1. Attempt to list files (should fail and suggest `init`)
    aicontext list files

    # 2. Initialize the session
    aicontext init

    # 3. List files again (should now show "No files in context")
    aicontext list files

    # 4. Add a file and confirm it's listed
    touch README.md
    aicontext add files README.md
    aicontext list files
    ```

This plan ensures the `init` command is added in a way that is clean, modular, and consistent with your project's architecture, while also being thoroughly tested.

