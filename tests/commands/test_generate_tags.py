from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml
from typer.testing import CliRunner

from ai_context_manager.cli import app

runner = CliRunner()


def create_mock_yaml(defs_dir: Path, base_path: Path, filename: str, tags: list[str], include: list[str]) -> Path:
    payload = {
        "meta": {
            "tags": tags,
            "description": f"{filename} selection",
        },
        "content": {
            "basePath": str(base_path),
            "include": include,
        },
    }
    file_path = defs_dir / filename
    with file_path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(payload, fh, sort_keys=False)
    return file_path


def test_generate_with_tags_discovers_matching_files(tmp_path: Path) -> None:
    defs_dir = tmp_path / "defs"
    defs_dir.mkdir()

    base_path = tmp_path / "project"
    base_path.mkdir()
    (base_path / "api.py").touch()
    (base_path / "ui.vue").touch()
    (base_path / "core.py").touch()

    create_mock_yaml(defs_dir, base_path, "api.yaml", ["api", "backend"], ["api.py"])
    create_mock_yaml(defs_dir, base_path, "ui.yaml", ["frontend"], ["ui.vue"])
    create_mock_yaml(defs_dir, base_path, "core.yaml", ["api", "core"], ["core.py"])

    output_file = tmp_path / "tagged.xml"
    output_file.touch()

    with patch("shutil.which", return_value="/usr/bin/repomix"), patch(
        "subprocess.run", return_value=MagicMock(returncode=0, stderr="")
    ) as mock_run:
        result = runner.invoke(
            app,
            [
                "generate",
                "repomix",
                "--dir",
                str(defs_dir),
                "--tag",
                "api",
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

    assert "api.py" in include_arg
    assert "core.py" in include_arg
    assert "ui.vue" not in include_arg
    assert kwargs["cwd"] == base_path


def test_generate_tags_no_match(tmp_path: Path) -> None:
    defs_dir = tmp_path / "defs"
    defs_dir.mkdir()
    base_path = tmp_path / "src"
    base_path.mkdir()
    create_mock_yaml(defs_dir, base_path, "stuff.yaml", ["foo"], ["foo.py"])

    result = runner.invoke(
        app,
        [
            "generate",
            "repomix",
            "--dir",
            str(defs_dir),
            "--tag",
            "bar",
        ],
    )

    assert result.exit_code == 1
    assert "No files found" in result.output


def test_generate_dir_without_tags_error(tmp_path: Path) -> None:
    defs_dir = tmp_path / "defs"
    defs_dir.mkdir()

    result = runner.invoke(
        app,
        [
            "generate",
            "repomix",
            "--dir",
            str(defs_dir),
        ],
    )

    assert result.exit_code == 1
    assert "must provide at least one --tag" in result.output


def test_generate_tags_default_output_uses_tags(tmp_path: Path) -> None:
    defs_dir = tmp_path / "defs"
    defs_dir.mkdir()
    base_path = tmp_path / "project"
    base_path.mkdir()
    (base_path / "api.py").touch()

    create_mock_yaml(defs_dir, base_path, "api.yaml", ["api"], ["api.py"])

    expected_output = tmp_path / "acm__context_api.xml"

    def create_output(*args, **kwargs):
        expected_output.touch()
        return MagicMock(returncode=0, stderr="")

    with patch("tempfile.gettempdir", return_value=str(tmp_path)), patch(
        "shutil.which", return_value="/usr/bin/repomix"
    ), patch("subprocess.run", side_effect=create_output) as mock_run:
        result = runner.invoke(
            app,
            [
                "generate",
                "repomix",
                "--dir",
                str(defs_dir),
                "--tag",
                "api",
            ],
        )

    assert result.exit_code == 0
    cmd = mock_run.call_args[0][0]
    output_idx = cmd.index("--output") + 1
    assert cmd[output_idx] == str(expected_output)


def test_list_tags_command(tmp_path: Path) -> None:
    defs_dir = tmp_path / "defs"
    defs_dir.mkdir()
    base_path = tmp_path / "src"

    create_mock_yaml(defs_dir, base_path, "api.yaml", ["api", "backend"], ["api.py"])
    create_mock_yaml(defs_dir, base_path, "ui.yaml", ["frontend", "ui"], ["ui.vue"])
    create_mock_yaml(defs_dir, base_path, "core.yaml", ["api", "core"], ["core.py"])
    create_mock_yaml(defs_dir, base_path, "untagged.yaml", [], ["misc.py"])

    result = runner.invoke(app, ["generate", "tags", "--dir", str(defs_dir)])

    assert result.exit_code == 0
    assert "Available Tags" in result.output
    assert "api" in result.output
    assert "frontend" in result.output
    assert "2" in result.output  # api tag appears twice
    assert "(1 files had no tags)" in result.output


def test_find_files_verbosity(tmp_path: Path) -> None:
    defs_dir = tmp_path / "defs"
    defs_dir.mkdir()
    base_path = tmp_path / "src"
    base_path.mkdir()

    create_mock_yaml(defs_dir, base_path, "api.yaml", ["api"], ["api.py"])
    create_mock_yaml(defs_dir, base_path, "ui.yaml", ["frontend"], ["ui.vue"])

    with patch("shutil.which", return_value="/usr/bin/repomix"), patch("subprocess.run"):
        result = runner.invoke(
            app,
            [
                "generate",
                "repomix",
                "--dir",
                str(defs_dir),
                "--tag",
                "api",
                "-v",
            ],
        )

    assert result.exit_code == 0
    assert "Scanning 2 files" in result.output
    assert "api.yaml: Match" in result.output
    assert "ui.yaml: No match" in result.output
