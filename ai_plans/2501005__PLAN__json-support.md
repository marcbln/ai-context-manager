### Guiding Principles for Implementation

1.  **Consistency**: Every command that can provide a machine-readable output will use the same flag: `--json`.
2.  **Standard Output (stdout)**: All JSON will be printed to standard output. Human-readable text, progress bars, or warnings should be printed to standard error (`stderr`) when the `--json` flag is active to avoid polluting the JSON output. The `rich` library's `console.log()` or `console.print(..., stderr=True)` is perfect for this.
3.  **Success and Error Structure**:
    *   On success, the JSON will contain the requested data.
    *   On failure, the command should exit with a non-zero status code and print a standardized JSON error object to `stdout`, like:
        ```json
        {
          "success": false,
          "error": "Profile 'xyz' not found."
        }
        ```
4.  **Clean Exit**: Use `raise typer.Exit()` immediately after printing the JSON to ensure no other text is accidentally printed.

---

### Implementation Plan: Command by Command

Here is the breakdown for each command that would benefit from JSON output.

#### 1. List Files in Session (`list_cmd.py`)

*   **File to Modify**: `ai_context_manager/commands/list_cmd.py`
*   **Target Command**: `files()`
*   **Implementation Details**:
    1.  Add a `--json` `typer.Option` to the `files` function.
    2.  If `--json` is true, load the context and create a dictionary containing the file list and a count.
    3.  Use `json.dumps()` to print the dictionary to `stdout` and then exit.

*   **Example CLI Call**:
    ```bash
    aicontext list files --json
    ```

*   **Example JSON Output**:
    ```json
    {
      "file_count": 2,
      "files": [
        "/path/to/project-a/src/main.py",
        "/path/to/project-a/README.md"
      ]
    }
    ```

#### 2. Add Files to Session (`add_cmd.py`)

*   **File to Modify**: `ai_context_manager/commands/add_cmd.py`
*   **Target Command**: `files()`
*   **Implementation Details**:
    1.  Add a `--json` option.
    2.  If `--json` is true, perform the add operation as normal.
    3.  After saving the context, create a JSON object that reports what was added and what the new state of the session context is. This is crucial for a GUI, as it can update its state without making a second call to `list`.

*   **Example CLI Call**:
    ```bash
    aicontext add files src/utils.py --json
    ```

*   **Example JSON Output**:
    ```json
    {
      "success": true,
      "message": "Added 1 new file(s) to context",
      "added_files": [
        "/path/to/project-a/src/utils.py"
      ],
      "context": {
        "file_count": 3,
        "files": [
          "/path/to/project-a/README.md",
          "/path/to/project-a/src/main.py",
          "/path/to/project-a/src/utils.py"
        ]
      }
    }
    ```

#### 3. Remove Files from Session (`remove_cmd.py`)

*   **File to Modify**: `ai_context_manager/commands/remove_cmd.py`
*   **Target Command**: `files()`
*   **Implementation Details**: Similar to the `add` command, the JSON output should confirm what was removed and return the new state of the context.

*   **Example CLI Call**:
    ```bash
    aicontext remove files src/utils.py --json
    ```

*   **Example JSON Output**:
    ```json
    {
      "success": true,
      "message": "Removed 1 file(s) from context",
      "removed_files": [
        "/path/to/project-a/src/utils.py"
      ],
      "context": {
        "file_count": 2,
        "files": [
          "/path/to/project-a/README.md",
          "/path/to/project-a/src/main.py"
        ]
      }
    }
    ```

#### 4. Show Profile Details (`profile_cmd.py`)

*   **File to Modify**: `ai_context_manager/commands/profile_cmd.py`
*   **Target Command**: `show()`
*   **Implementation Details**:
    1.  Add a `--json` option.
    2.  Instead of printing formatted text, use the existing `profile.to_dict()` method and print the result as a JSON string.

*   **Example CLI Call**:
    ```bash
    aicontext profile show project-a-backend --json
    ```

*   **Example JSON Output**:
    ```json
    {
      "name": "project-a-backend",
      "description": "Python backend files for Project A",
      "created": "2025-10-05T15:00:00.000000",
      "modified": "2025-10-05T15:00:00.000000",
      "base_path": "/path/to/project-a",
      "paths": [
        {
          "path": "src/backend/",
          "is_directory": true,
          "recursive": true
        }
      ],
      "exclude_patterns": [],
      "include_metadata": true
    }
    ```

#### 5. Export Context (`export_cmd.py`)

*   **File to Modify**: `ai_context_manager/commands/export_cmd.py`
*   **Target Command**: `export_context()`
*   **Implementation Details**:
    1.  Add a `--json-summary` flag. The name is more specific because the command's primary output is the file itself, not JSON.
    2.  If the flag is present, after the export is successfully completed, print the `result` dictionary from `exporter.export_to_file()` as a JSON string to `stdout`.

*   **Example CLI Call**:
    ```bash
    aicontext export output.md --profile project-a-backend --json-summary
    ```

*   **Example JSON Output (printed to console after file is written)**:
    ```json
    {
      "success": true,
      "message": "Successfully exported 5 files to output.md",
      "output_path": "/path/to/project-a/output.md",
      "files": [
        "/path/to/project-a/src/backend/main.py",
        "/path/to/project-a/src/backend/utils.py"
      ],
      "total_size": 12345,
      "total_size_human": "12.1 KB",
      "total_tokens": 1500
    }
    ```

#### 6. Other Profile Commands (`profile_cmd.py`)

For actions like `create`, `delete`, `update`, and `load`, a simple JSON confirmation is sufficient.

*   **`create`**: Return the newly created profile object.
    *   **Call**: `aicontext profile create my-new-profile ./src --json`
    *   **Output**: A JSON object of the created profile.

*   **`delete`**: Return a success message.
    *   **Call**: `aicontext profile delete my-new-profile --json`
    *   **Output**: `{"success": true, "message": "Profile 'my-new-profile' deleted successfully!"}`

*   **`update`**: Return the updated profile object.
    *   **Call**: `aicontext profile update my-profile --description "new desc" --json`
    *   **Output**: The full JSON object of the updated profile.

*   **`load`**: Return the state of the session context after loading.
    *   **Call**: `aicontext profile load my-profile --json`
    *   **Output**: `{"success": true, "loaded_profile": "my-profile", "context": {"file_count": 5, "files": [...]}}`

### Recommended Roadmap

1.  **Start with the read-only commands**:
    *   Implement `--json` for `profile list`.
    *   Implement `--json` for `profile show`.
    *   Implement `--json` for `list files`.
    These are the easiest wins and provide the core data your GUI will need to display.

2.  **Implement state-changing commands**:
    *   Tackle `add`, `remove`, and `load`, ensuring they return the new context state. This will make your GUI feel responsive and always in sync.

3.  **Implement action/feedback commands**:
    *   Add JSON support to `profile create`, `update`, and `delete`.
    *   Finally, add the `--json-summary` to the `export` command to provide feedback on the export operation.

Following this plan will transform your CLI into a powerful backend, making the development of a TUI or GUI wrapper a much simpler and more robust process.

