# tests/commands/test_generate_cmd.py

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml
from typer.testing import CliRunner

from ai_context_manager.cli import app

runner = CliRunner()


def test_generate_repomix_success(tmp_path: Path) -> None:
    """Repomix command runs when selection and binary exist."""

    selection_file = tmp_path / "selection.yaml"
    data = {
        "basePath": str(tmp_path),
        "include": ["main.py", "src"],
    }
    with selection_file.open("w") as f:
        yaml.dump(data, f)

    # Create dummy files/dirs so validation logic passes
    (tmp_path / "src").mkdir()
    (tmp_path / "main.py").touch()

    # Create expected output file because the command now checks for it
    output_file = tmp_path / "context.xml"
    output_file.touch()

    with patch("shutil.which", return_value="/usr/bin/repomix"), patch(
            "subprocess.run", return_value=MagicMock(returncode=0, stderr="")
    ) as mock_run:
        result = runner.invoke(
            app,
            [
                "generate",
                "repomix",
                str(selection_file),
                "--output",
                str(output_file),
            ],
        )

    assert result.exit_code == 0
    assert "Success! Context generated" in result.output

    args, kwargs = mock_run.call_args
    cmd = args[0]
    assert any("main.py" in part for part in cmd)
    assert any("src/**" in part for part in cmd)
    assert kwargs["cwd"] == Path(str(tmp_path))


def test_generate_missing_binary(tmp_path: Path) -> None:
    """Gracefully errors when repomix binary missing."""

    selection_file = tmp_path / "selection.yaml"
    selection_file.touch()

    with patch("shutil.which", return_value=None):
        result = runner.invoke(app, ["generate", "repomix", str(selection_file)])

    assert result.exit_code == 1
    assert "Error: 'repomix' not found" in result.output


def test_generate_repomix_default_output_and_copy(tmp_path: Path) -> None:
    """Test generation with default temp output and clipboard flag."""

    selection_file = tmp_path / "selection.yaml"
    data = {
        "basePath": str(tmp_path),
        "include": ["main.py"],
    }
    with selection_file.open("w") as f:
        yaml.dump(data, f)

    (tmp_path / "main.py").touch()

    # Mock tempfile.gettempdir to ensure we know where the file is expected
    # and mock the creation of that file so validation passes
    with patch("tempfile.gettempdir", return_value=str(tmp_path)):
        expected_output = tmp_path / "acm__selection.xml"

        # Define side effect to create file when repomix 'runs'
        def create_output(*args, **kwargs):
            expected_output.touch()
            return MagicMock(returncode=0, stderr="")

        with patch("shutil.which", side_effect=lambda x: "/usr/bin/xclip" if x == "xclip" else "/usr/bin/repomix"), \
                patch("subprocess.run", side_effect=create_output) as mock_run:
            result = runner.invoke(
                app,
                [
                    "generate",
                    "repomix",
                    str(selection_file),
                    "--copy",
                ],
            )

    assert result.exit_code == 0
    assert "Success!" in result.output
    assert "File URI copied to clipboard" in result.output

    # Verify calls
    # 1. Repomix call
    repomix_call = mock_run.call_args_list[0]
    cmd_list = repomix_call[0][0]
    assert any(part == "repomix" or part.endswith("/repomix") for part in cmd_list)

    # Check that output path is in temp directory (which we mocked to tmp_path)
    output_arg_index = cmd_list.index("--output") + 1
    output_path = cmd_list[output_arg_index]
    assert str(tmp_path) in output_path
    assert "acm__selection.xml" in output_path

    # 2. Clipboard call
    clipboard_call = mock_run.call_args_list[1]
    clip_cmd = clipboard_call[0][0]
    assert clip_cmd == ["xclip", "-selection", "clipboard", "-t", "text/uri-list"]


def test_generate_multiple_selection_files(tmp_path: Path) -> None:
    """Merges patterns from multiple selection files relative to first base path."""

    root = tmp_path
    sel1 = root / "sel1.yaml"
    sel2 = root / "sel2.yaml"

    data1 = {
        "basePath": str(root),
        "include": ["main.py"],
    }
    data2 = {
        "basePath": str(root),
        "include": ["docs"],
    }

    with sel1.open("w") as f:
        yaml.dump(data1, f)
    with sel2.open("w") as f:
        yaml.dump(data2, f)

    (root / "main.py").touch()
    docs_dir = root / "docs"
    docs_dir.mkdir()

    output_file = root / "merged.xml"
    output_file.touch()

    with patch("shutil.which", return_value="/usr/bin/repomix"), patch(
        "subprocess.run", return_value=MagicMock(returncode=0, stderr="")
    ) as mock_run:
        result = runner.invoke(
            app,
            [
                "generate",
                "repomix",
                str(sel1),
                str(sel2),
                "--output",
                str(output_file),
            ],
        )

    assert result.exit_code == 0
    assert "Success! Context generated" in result.output

    args, kwargs = mock_run.call_args
    cmd = args[0]
    include_idx = cmd.index("--include") + 1
    include_arg = cmd[include_idx]

    assert "main.py" in include_arg
    assert "docs/**" in include_arg
    assert kwargs["cwd"] == Path(str(root))


def test_generate_multidoc_prints_metadata(tmp_path: Path) -> None:
    """Supports multi-document YAML and prints metadata to console."""

    selection_file = tmp_path / "selection.yaml"
    meta_doc = {
        "description": "Docs context",
        "createdAt": "2025-12-10",
        "createdBy": "tester",
    }
    content_doc = {
        "content": {
            "basePath": str(tmp_path),
            "include": ["main.py"],
        }
    }
    selection_file.write_text(
        "---\n"
        + yaml.safe_dump(meta_doc, sort_keys=False)
        + "---\n"
        + yaml.safe_dump(content_doc, sort_keys=False),
        encoding="utf-8",
    )

    (tmp_path / "main.py").touch()
    output_file = tmp_path / "context.xml"

    def create_output(*args, **kwargs):
        output_file.touch()
        return MagicMock(returncode=0, stderr="")

    with patch("shutil.which", return_value="/usr/bin/repomix"), patch(
        "subprocess.run", side_effect=create_output
    ):
        result = runner.invoke(
            app,
            [
                "generate",
                "repomix",
                str(selection_file),
                "--output",
                str(output_file),
            ],
        )

    assert result.exit_code == 0
    output_text = result.output
    assert "Processing: selection.yaml" in output_text
    assert "Description: Docs context" in output_text
    assert "Created:     2025-12-10 by tester" in output_text


def test_generate_prints_related_tags(tmp_path: Path) -> None:
    """Ensure relatedTags are parsed and printed."""

    selection_file = tmp_path / "related.yaml"
    selection_content = """---
meta:
  description: "Main Dashboard"
  createdAt: "2025-12-15"
  createdBy: "Tester"
  updatedAt: "2025-12-15"
  updatedBy: "Tester"
  documentType: "CONTEXT_DEFINITION"
  tags: ["dashboard"]
  relatedTags: ["dashboard-cards", "api-docs"]
content:
  basePath: "."
  include:
    - "README.md"
"""
    selection_file.write_text(selection_content, encoding="utf-8")
    (tmp_path / "README.md").write_text("content", encoding="utf-8")

    output_file = tmp_path / "context.txt"

    with patch("shutil.which", return_value="/usr/bin/repomix"), patch(
        "subprocess.run", return_value=MagicMock(returncode=0, stderr="")
    ) as mock_run:
        result = runner.invoke(
            app,
            [
                "generate",
                "repomix",
                str(selection_file),
                "--output",
                str(output_file),
            ],
        )

    assert result.exit_code == 0
    assert "See Also:    dashboard-cards, api-docs" in result.output


def test_count_files_and_folders():
    """Test the file/folder counting logic."""
    from ai_context_manager.commands.generate_cmd import _count_files_and_folders
    from pathlib import Path
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        
        # Create test structure
        test_file = base / "test.txt"
        test_file.write_text("content")
        
        test_dir = base / "subdir"
        test_dir.mkdir()
        
        # Test counting
        file_count, folder_count = _count_files_and_folders(["test.txt", "subdir"], base)
        assert file_count == 1
        assert folder_count == 1
        
        # Test non-existent paths (should be ignored)
        file_count, folder_count = _count_files_and_folders(["nonexistent.txt"], base)
        assert file_count == 0
        assert folder_count == 0


def test_generate_repomix_shows_counts(capsys, tmp_path):
    """Test that generate repomix shows file/folder counts."""
    from ai_context_manager.cli import app
    from typer.testing import CliRunner
    
    # Create test selection file
    selection_file = tmp_path / "test.yaml"
    selection_content = """---
meta:
  description: "Test selection"
  updatedAt: "2025-12-15"
  updatedBy: "Test User"
---
content:
  basePath: "."
  include:
    - "README.md"
    - "src/"
"""
    selection_file.write_text(selection_content)
    
    # Create mock files
    (tmp_path / "README.md").write_text("# Test")
    (tmp_path / "src").mkdir()
    
    # Create expected output file
    output_file = tmp_path / "context.xml"
    output_file.touch()
    
    # Run command (mock repomix to avoid dependency)
    with patch('shutil.which', return_value="/usr/bin/repomix"), \
         patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stderr = ""
        
        runner = CliRunner()
        result = runner.invoke(app, ["generate", "repomix", str(selection_file), "--output", str(output_file)])
        
        assert result.exit_code == 0
        output_text = result.output
        assert "Files:" in output_text
        assert "Folders:" in output_text
        assert "1" in output_text  # Should show 1 file
        assert "1" in output_text  # Should show 1 folder


def test_generate_repomix_prints_absolute_paths(tmp_path: Path) -> None:
    """Ensure absolute paths and verbose include listings are shown."""

    selection_file = tmp_path / "abs.yaml"
    selection_content = """---
meta:
  description: "Absolute path selection"
---
content:
  basePath: "."
  include:
    - "README.md"
    - "src"
"""
    selection_file.write_text(selection_content)

    readme_file = tmp_path / "README.md"
    readme_file.write_text("# Test")
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    output_file = tmp_path / "context.xml"
    output_file.touch()

    with patch("shutil.which", return_value="/usr/bin/repomix"), patch(
        "subprocess.run", return_value=MagicMock(returncode=0, stderr="")
    ):
        # Non-verbose: should show selection absolute path
        result = runner.invoke(
            app,
            [
                "generate",
                "repomix",
                str(selection_file),
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        abs_path_line = f"[magenta]{selection_file.resolve()}[/magenta]"
        assert abs_path_line in result.output

        # Verbose: should list include entries with folder suffix
        result_verbose = runner.invoke(
            app,
            [
                "generate",
                "repomix",
                str(selection_file),
                "--output",
                str(output_file),
                "--verbose",
            ],
        )

        assert result_verbose.exit_code == 0
        file_line = f"[green]{readme_file.resolve()}[/green]"
        dir_line = f"[cyan]{src_dir.resolve()}/[/cyan]"
        assert file_line in result_verbose.output
        assert dir_line in result_verbose.output