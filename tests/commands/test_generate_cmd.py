# tests/commands/test_generate_cmd.py

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
    assert "repomix" in cmd_list

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