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
