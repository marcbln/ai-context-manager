# Implementation Plan: Enable `-h` as a Help Flag Alias

## Overview

This plan details the necessary code modifications to enable the `-h` flag as a universal alias for the `--help` flag across the entire `ai-context-manager` CLI application. This is a standard convention that improves user experience.

The implementation will leverage the existing `CLI_CONTEXT_SETTINGS` dictionary defined in `ai_context_manager/config.py` and apply it to all `typer.Typer()` application instances.

## Goal

The primary goal is that a user can run `aicontext -h`, `aicontext export -h`, `aicontext profile list -h`, etc., and receive the same help output as they would with the `--help` flag.

---

## Phase 1: Preparation and Verification

This phase ensures that the required configuration constant is correctly defined and available before making changes.

*   **Step 1.1: Verify `CLI_CONTEXT_SETTINGS` Constant**
    1.  **Action:** Locate the file `ai_context_manager/config.py`.
    2.  **Verify:** Confirm that the following dictionary is defined within the file. No changes are needed in this step; it is purely for verification.
        ```python
        # CLI configuration
        CLI_CONTEXT_SETTINGS = {
            "help_option_names": ["-h", "--help"],
            "max_content_width": 120,
        }
        ```

---

## Phase 2: Update Main CLI Entry Points

This phase applies the context settings to the main application entry points, which are the top-level `Typer` instances.

*   **Step 2.1: Modify `ai_context_manager/cli.py`**
    1.  **Action:** Open the file `ai_context_manager/cli.py`.
    2.  **Add Import:** Add an import for `CLI_CONTEXT_SETTINGS` from the config module.
    3.  **Modify `Typer` Instantiation:** Update the `app = typer.Typer(...)` call to include the `context_settings` argument.

    **Target Code:**
    ```python:ai_context_manager/cli.py
    """Main CLI entry point for AI Context Manager."""

    import typer
    from rich.console import Console

    from ai_context_manager.commands.export_cmd import app as export_app
    from ai_context_manager.commands.profile_cmd import app as profile_app
    from ai_context_manager.config import CLI_CONTEXT_SETTINGS

    app = typer.Typer(
        name="ai-context-manager",
        help="AI Context Manager - Export codebases for AI analysis",
        add_completion=False,
        context_settings=CLI_CONTEXT_SETTINGS,
    )
    console = Console()

    # Add subcommands
    app.add_typer(export_app, name="export", help="Export files to AI context format")
    app.add_typer(profile_app, name="profile", help="Manage export profiles")


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

*   **Step 2.2: Modify `ai_context_manager/__main__.py`**
    1.  **Action:** Open the file `ai_context_manager/__main__.py`.
    2.  **Add Import:** Add an import for `CLI_CONTEXT_SETTINGS`.
    3.  **Modify `Typer` Instantiation:** Update the `app = typer.Typer(...)` call to include the `context_settings` argument.

    **Target Code:**
    ```python:ai_context_manager/__main__.py
    """Main entry point for AI Context Manager CLI."""
    import typer

    from ai_context_manager.commands.export_cmd import app as export_app
    from ai_context_manager.commands.profile_cmd import app as profile_app
    from ai_context_manager.config import CLI_CONTEXT_SETTINGS

    app = typer.Typer(
        help="AI Context Manager - Export code context for AI analysis",
        context_settings=CLI_CONTEXT_SETTINGS,
    )
    app.add_typer(export_app, name="export")
    app.add_typer(profile_app, name="profile")

    if __name__ == "__main__":
        app()
    ```

---

## Phase 3: Update Subcommand Applications

This phase applies the context settings to all subcommand modules, ensuring that `-h` works for nested commands like `aicontext export ...` and `aicontext profile ...`.

*   **Step 3.1: Modify `ai_context_manager/commands/export_cmd.py`**
    1.  **Action:** Open `ai_context_manager/commands/export_cmd.py`.
    2.  **Add Import:** Add `from ai_context_manager.config import CLI_CONTEXT_SETTINGS`.
    3.  **Modify `Typer` Instantiation:** Update `app = typer.Typer()` to `app = typer.Typer(context_settings=CLI_CONTEXT_SETTINGS)`.

    **Target Code Snippet:**
    ```python
    from ai_context_manager.config import CLI_CONTEXT_SETTINGS
    from ai_context_manager.core.profile import Profile
    # ... other imports

    app = typer.Typer(context_settings=CLI_CONTEXT_SETTINGS)
    console = Console()
    ```

*   **Step 3.2: Modify `ai_context_manager/commands/profile_cmd.py`**
    1.  **Action:** Open `ai_context_manager/commands/profile_cmd.py`.
    2.  **Add Import:** Add `CLI_CONTEXT_SETTINGS` to the existing import from `config`.
    3.  **Modify `Typer` Instantiation:** Add the `context_settings` argument to the `app` definition.

    **Target Code Snippet:**
    ```python
    # ... other imports
    from ai_context_manager.config import get_config_dir, CLI_CONTEXT_SETTINGS

    app = typer.Typer(
        help="Manage AI Context Manager selection profiles.",
        context_settings=CLI_CONTEXT_SETTINGS,
    )
    console = Console()
    ```

*   **Step 3.3: Modify `ai_context_manager/commands/add_cmd.py`**
    1.  **Action:** Open `ai_context_manager/commands/add_cmd.py`.
    2.  **Add Import:** Add `CLI_CONTEXT_SETTINGS` to the existing import from `config`.
    3.  **Modify `Typer` Instantiation:** Add the `context_settings` argument to the `app` definition.

    **Target Code Snippet:**
    ```python
    # ... other imports
    from ..config import get_config_dir, CLI_CONTEXT_SETTINGS

    app = typer.Typer(
        help="Add files to context",
        context_settings=CLI_CONTEXT_SETTINGS,
    )
    ```

*   **Step 3.4: Modify `ai_context_manager/commands/list_cmd.py`**
    1.  **Action:** Open `ai_context_manager/commands/list_cmd.py`.
    2.  **Add Import:** Add `CLI_CONTEXT_SETTINGS` to the existing import from `config`.
    3.  **Modify `Typer` Instantiation:** Add the `context_settings` argument to the `app` definition.

    **Target Code Snippet:**
    ```python
    # ... other imports
    from ..config import get_config_dir, CLI_CONTEXT_SETTINGS

    app = typer.Typer(
        help="List files in context",
        context_settings=CLI_CONTEXT_SETTINGS,
    )
    ```

*   **Step 3.5: Modify `ai_context_manager/commands/remove_cmd.py`**
    1.  **Action:** Open `ai_context_manager/commands/remove_cmd.py`.
    2.  **Add Import:** Add `CLI_CONTEXT_SETTINGS` to the existing import from `config`.
    3.  **Modify `Typer` Instantiation:** Add the `context_settings` argument to the `app` definition.

    **Target Code Snippet:**
    ```python
    # ... other imports
    from ..config import get_config_dir, CLI_CONTEXT_SETTINGS

    app = typer.Typer(
        help="Remove files from context",
        context_settings=CLI_CONTEXT_SETTINGS,
    )
    ```

---

## Phase 4: Verification

This phase involves running the CLI with the new `-h` flag to confirm that the changes work as expected at all levels.

*   **Step 4.1: Verify Top-Level Help**
    1.  **Action:** In the terminal, run `ai-context-manager -h`.
    2.  **Expected Outcome:** The command should exit with code 0 and display the main help message for the application.

*   **Step 4.2: Verify Subcommand Group Help**
    1.  **Action:** In the terminal, run `ai-context-manager export -h`.
    2.  **Expected Outcome:** The command should exit with code 0 and display the help message for the `export` command group, listing subcommands like `export`, `formats`, and `models`.
    3.  **Action:** In the terminal, run `ai-context-manager profile -h`.
    4.  **Expected Outcome:** The command should exit with code 0 and display the help message for the `profile` command group, listing subcommands like `create`, `list`, `show`, etc.

*   **Step 4.3: Verify Specific Subcommand Help**
    1.  **Action:** In the terminal, run `ai-context-manager export export -h`.
    2.  **Expected Outcome:** The command should exit with code 0 and display the help message specifically for the `export` command, showing all its options (`--output`, `--profile`, etc.).

---

## Phase 5: Final Review

*   **Step 5.1: Review Changes**
    1.  **Action:** Review the diff of all modified files.
    2.  **Verify:**
        *   The `context_settings=CLI_CONTEXT_SETTINGS` argument has been correctly added to all `typer.Typer` instances.
        *   The necessary imports for `CLI_CONTEXT_SETTINGS` have been added without introducing style issues.
        *   No other code has been inadvertently modified.

This concludes the implementation plan. Upon successful completion of all phases, the task will be complete.

