from pathlib import Path
import yaml
from typer.testing import CliRunner

from ai_context_manager.cli import app
from ai_context_manager.config import get_config_dir

runner = CliRunner()

def test_add_single_file(tmp_path: Path, monkeypatch):
    """Test adding a single file to the context."""
    config_dir = tmp_path / ".config"
    get_config_dir.cache_clear()
    monkeypatch.setattr("ai_context_manager.config.get_config_dir", lambda: config_dir)
    
    file1 = tmp_path / "file1.txt"
    file1.touch()
    
    result = runner.invoke(app, ["add", "files", str(file1)])
    
    assert result.exit_code == 0
    assert "Added 1 new file(s) to context" in result.output
    
    context_file = config_dir / "context.yaml"
    with open(context_file, 'r') as f:
        context = yaml.safe_load(f)
    
    assert context["files"] == [str(file1.resolve())]

def test_add_directory_recursively(tmp_path: Path, monkeypatch):
    """Test adding a directory recursively."""
    config_dir = tmp_path / ".config"
    get_config_dir.cache_clear()
    monkeypatch.setattr("ai_context_manager.config.get_config_dir", lambda: config_dir)

    dir1 = tmp_path / "dir1"
    dir1.mkdir()
    file1 = dir1 / "file1.txt"
    file1.touch()
    
    subdir = dir1 / "subdir"
    subdir.mkdir()
    file2 = subdir / "file2.txt"
    file2.touch()
    
    result = runner.invoke(app, ["add", "files", str(dir1), "-r"])
    
    assert result.exit_code == 0
    assert "Added 2 new file(s) to context" in result.output
    
    context_file = config_dir / "context.yaml"
    with open(context_file, 'r') as f:
        context = yaml.safe_load(f)
    
    expected_files = sorted([str(file1.resolve()), str(file2.resolve())])
    assert sorted(context["files"]) == expected_files

def test_add_nonexistent_path(tmp_path: Path, monkeypatch):
    """Test adding a path that does not exist."""
    config_dir = tmp_path / ".config"
    get_config_dir.cache_clear()
    monkeypatch.setattr("ai_context_manager.config.get_config_dir", lambda: config_dir)

    result = runner.invoke(app, ["add", "files", "nonexistent/path"])
    
    assert result.exit_code == 0
    assert "Warning: Path does not exist" in result.output
    
    context_file = config_dir / "context.yaml"
    assert not context_file.exists()