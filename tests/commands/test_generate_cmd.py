from pathlib import Path
from unittest.mock import MagicMock, patch
import tempfile

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
    
    # Create dummy files/dirs so is_dir() check works
    (tmp_path / "src").mkdir()
    (tmp_path / "main.py").touch()

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
                "context.xml",
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

    # Mock repomix, xclip check, and subprocess for xclip execution
    with patch("shutil.which", side_effect=lambda x: "/usr/bin/xclip" if x == "xclip" else "/usr/bin/repomix"), \
         patch("subprocess.run") as mock_run:
        
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        
        result = runner.invoke(
            app,
            [
                "generate",
                "repomix",
                str(selection_file),
                "--copy", # Enable copy
                # No output flag provided
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
    
    # Check that output path is in temp directory
    output_arg_index = cmd_list.index("--output") + 1
    output_path = cmd_list[output_arg_index]
    assert tempfile.gettempdir() in output_path
    assert "acm__selection.xml" in output_path # based on filename

    # 2. Clipboard call
    clipboard_call = mock_run.call_args_list[1]
    clip_cmd = clipboard_call[0][0]
    assert clip_cmd == ["xclip", "-selection", "clipboard", "-t", "text/uri-list"]
