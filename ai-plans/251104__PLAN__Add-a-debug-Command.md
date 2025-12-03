Excellent. Here is a detailed, multi-phased implementation plan in Markdown format, designed to be executed by an AI coding agent.

### Project: Add a `debug` Command to AI Context Manager

**Objective:** Implement a new `aicontext debug from-trace` command that parses a stack trace from standard input, identifies the relevant local files, adds them to the session context, and optionally exports a complete debugging context for an AI.

---

### Phase 1: Foundational Scaffolding and CLI Integration

**Goal:** Create the necessary files and integrate the new `debug` command into the existing CLI structure, making it discoverable but not yet functional.

1.  **Create New Command File:**
    *   Create a new file: `ai_context_manager/commands/debug_cmd.py`.
    *   Inside this file, set up the basic Typer application structure.

    ```python
    # ai_context_manager/commands/debug_cmd.py
    import typer
    from rich.console import Console
    from ..config import CLI_CONTEXT_SETTINGS

    app = typer.Typer(help="Create a debug context from a stack trace.", context_settings=CLI_CONTEXT_SETTINGS)
    console = Console()

    @app.command()
    def from_trace():
        """
        Parses a stack trace from stdin to create a debug context.
        (This is a placeholder implementation).
        """
        console.print("[yellow]Debug command is not yet implemented.[/yellow]")
    ```

2.  **Integrate into Main CLI:**
    *   Modify `ai_context_manager/cli.py` to import and register the new `debug_app`.

    ```python
    # In ai_context_manager/cli.py

    # ... other imports
    from ai_context_manager.commands.debug_cmd import app as debug_app # Add this

    # ...
    # In the list of command imports:
    from ai_context_manager.commands import (
        # ... existing commands
        debug_cmd
    )

    # ...
    # At the end of the `add_typer` block:
    app.add_typer(debug_app, name="debug", help="Create context from a stack trace")
    ```

3.  **Create Test File:**
    *   Create a new test file: `tests/commands/test_debug_cmd.py`.
    *   Add a simple test to verify that the command is registered correctly and shows up in the help text.

    ```python
    # tests/commands/test_debug_cmd.py
    from typer.testing import CliRunner
    from ai_context_manager.cli import app

    runner = CliRunner()

    def test_debug_command_exists():
        """Test that the 'debug' command is registered."""
        result = runner.invoke(app, ["debug", "--help"])
        assert result.exit_code == 0
        assert "Create a debug context from a stack trace" in result.output
        assert "from-trace" in result.output
    ```

4.  **Verification:**
    *   Run `poetry run pytest tests/commands/test_debug_cmd.py`. The test should pass.
    *   Run `poetry run aicontext --help`. The `debug` command should be listed.

---

### Phase 2: Core Logic - Parsing and File Resolution

**Goal:** Implement the primary functionality of reading from `stdin`, parsing file paths, and resolving them locally.

1.  **Implement `stdin` Reading:**
    *   In `ai_context_manager/commands/debug_cmd.py`, modify `from_trace` to read from `sys.stdin`.
    *   Add a check using `sys.stdin.isatty()` to guide the user to pipe input if they run it directly.

2.  **Develop Path Parsing Logic:**
    *   Implement a regular expression to identify file paths in the piped-in text. The regex should be robust enough to handle different formats, such as:
        *   `/path/to/file.py:123`
        *   `at /path/to/another/file.php:45`
        *   `in /www/vendor/some/file.php line 130`
    *   A good starting point for the pattern is `r'[/\w\-\.\_]+?\.(php|py|js|ts|java|rb|go|cs)'`. This can be refined.
    *   Extract a unique set of file paths from the trace.

3.  **Implement File Resolution:**
    *   Add a mandatory `--base-path` option to the `from_trace` command, which specifies the local project root.
    *   For each path extracted from the trace, implement a search mechanism within the `--base-path` to find the corresponding local file. The strategy of matching the end of the path (e.g., `src/utils/file.php`) is effective for mapping container paths to local paths.
    *   Maintain two lists: `resolved_files` and `unresolved_files`.

4.  **Update Session Context:**
    *   Import `load_context` and `save_context` from `add_cmd.py`.
    *   Take the list of `resolved_files` and merge it with the existing session context, ensuring no duplicates.
    *   Save the updated context.

5.  **Add User Feedback:**
    *   Print clear messages to the console:
        *   The number of file paths found in the trace.
        *   A list of successfully resolved files being added to the context (use green color).
        *   A warning list of any paths that could not be resolved locally (use yellow color).

6.  **Write Unit Tests:**
    *   In `tests/commands/test_debug_cmd.py`, add tests for:
        *   Parsing different formats of stack traces.
        *   Correctly resolving file paths against a mock project structure.
        *   Handling cases where no files can be resolved.
        *   Verifying that the `context.yaml` file is updated correctly.

---

### Phase 3: Direct Export Functionality

**Goal:** Add the `--output` option to allow for a streamlined, one-shot debugging workflow.

1.  **Add CLI Options:**
    *   Add the optional `--output` and `--format` arguments to the `from_trace` command in `debug_cmd.py`.

2.  **Implement Export Logic:**
    *   If the `--output` option is provided, trigger the export process.
    *   Create a temporary, in-memory `Profile` object using the list of `resolved_files`.
    *   Instantiate the `ContextExporter` with this temporary profile.
    *   **Crucially**, prepend the original stack trace to the exported content. The final file should have a "Original Error Trace" section at the top.
    *   Write the combined content to the file specified by `--output`.

3.  **Add User Feedback:**
    *   Print messages indicating that the export is happening and confirm when the file has been written successfully.

4.  **Write Integration Tests:**
    *   Add an integration test that simulates the full workflow:
        1.  Create a mock stack trace file.
        2.  Use `CliRunner` to pipe this file into the `debug from-trace` command with the `--base-path` and `--output` options.
        3.  Assert that the output file is created.
        4.  Read the output file and verify that it contains both the original stack trace and the content of the resolved source files.

---

### Phase 4: Documentation and Final Polish

**Goal:** Ensure the new feature is easy to understand and use by updating all relevant user-facing documentation.

1.  **Update README.md:**
    *   Add a new major section titled "Debugging Workflow with `aicontext debug`".
    *   Provide a clear, concise example of the primary use case: `cat crash.log | aicontext debug from-trace --base-path /path/to/project -o debug_context.md`.
    *   Explain the benefit: automatically gathering all relevant files from a backtrace for AI analysis.
    *   Update the "Full Command Reference" section to include `aicontext debug from-trace` and all its options (`--base-path`, `--output`, `--format`).

2.  **Create Detailed Documentation (Optional but Recommended):**
    *   Create a new file `docs/debug.md`.
    *   In this file, provide more detail on how the command works, the types of stack traces it can parse, and advanced usage tips.

3.  **Review Console Output:**
    *   Perform a final review of all console messages generated by the command. Ensure they are clear, helpful, and consistently formatted using `rich`. Check for clarity in both success and error scenarios.

4.  **Code Cleanup:**
    *   Add docstrings and type hints to all new functions in `ai_context_manager/commands/debug_cmd.py`.
    *   Ensure the code adheres to the project's style conventions.

By following these phases, the AI coding agent can systematically build, test, and document the new `debug` command, resulting in a robust and valuable feature for the `ai-context-manager` tool.

