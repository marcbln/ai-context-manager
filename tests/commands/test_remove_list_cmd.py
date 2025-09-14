from pathlib import Path
import yaml
from typer.testing import CliRunner

from ai_context_manager.cli import app
from ai_context_manager.config import get_config_dir

runner = CliRunner()

def setup_context(config_dir: Path, files_to_add: list):
    """Helper to set up a context.yaml file."""
    context_file = config_dir / "context.yaml"
    resolved_files = [str(Path(f).resolve()) for f in files_to_add]
    with open(context_file, 'w') as f:
        yaml.dump({"files": resolved_files}, f)
    return resolved_files

def test_list_and_remove_files(tmp_path: Path, monkeypatch):
    """Test listing files and then removing one."""
    config_dir = tmp_path / ".config"
    get_config_dir.cache_clear()
    monkeypatch.setattr("ai_context_manager.config.get_config_dir", lambda: config_dir)
    
    file1 = tmp_path / "file1.txt"
    file1.touch()
    file2 = tmp_path / "file2.py"
    file2.touch()
    
    # Setup context with two files
    setup_context(config_dir, [file1, file2])
    
    # Test 'list'
    result = runner.invoke(app, ["list", "files"])
    assert result.exit_code == 0
    assert str(file1.resolve()) in result.output
    assert str(file2.resolve()) in result.output
    
    # Test 'remove'
    result = runner.invoke(app, ["remove", "files", str(file1)])
    assert result.exit_code == 0
    assert f"- {file1.resolve()}" in result.output
    
    # List again to confirm removal
    result = runner.invoke(app, ["list", "files"])
    assert result.exit_code == 0
    assert str(file1.resolve()) not in result.output
    assert str(file2.resolve()) in result.output

def test_remove_all_files(tmp_path: Path, monkeypatch):
    """Test removing all files with the --all flag."""
    config_dir = tmp_path / ".config"
    get_config_dir.cache_clear()
    monkeypatch.setattr("ai_context_manager.config.get_config_dir", lambda: config_dir)
    
    (tmp_path / "file1.txt").touch()
    (tmp_path / "file2.py").touch()
    setup_context(config_dir, [tmp_path / "file1.txt", tmp_path / "file2.py"])
    
    result = runner.invoke(app, ["remove", "files", "--all"])
    assert result.exit_code == 0
    assert "Removed all 2 files from context" in result.output

    # List to confirm it's empty
    result = runner.invoke(app, ["list", "files"])
    assert "No files in context" in result.output