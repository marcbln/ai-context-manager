from pathlib import Path
import yaml
from typer.testing import CliRunner

from ai_context_manager.cli import app
from ai_context_manager.config import get_config_dir

runner = CliRunner()

def test_init_creates_context_file(tmp_path: Path, monkeypatch):
    """Test that `init` creates a new, empty context.yaml file."""
    config_dir = tmp_path / ".config"
    get_config_dir.cache_clear()
    monkeypatch.setattr("ai_context_manager.config.get_config_dir", lambda: config_dir)

    result = runner.invoke(app, ["init"])

    assert result.exit_code == 0
    assert "Initialized empty session context" in result.output

    context_file = config_dir / "context.yaml"
    assert context_file.exists()

    with open(context_file, 'r') as f:
        context = yaml.safe_load(f)
    assert context == {"files": []}

def test_init_overwrite_confirmed(tmp_path: Path, monkeypatch):
    """Test that `init` overwrites an existing context file after confirmation."""
    config_dir = tmp_path / ".config"
    config_dir.mkdir()
    context_file = config_dir / "context.yaml"
    with open(context_file, 'w') as f:
        yaml.dump({"files": ["old_file.txt"]}, f)

    get_config_dir.cache_clear()
    monkeypatch.setattr("ai_context_manager.config.get_config_dir", lambda: config_dir)

    # Simulate user typing "y" and pressing Enter
    result = runner.invoke(app, ["init"], input="y\n")

    assert result.exit_code == 0
    assert "Initialized empty session context" in result.output

    with open(context_file, 'r') as f:
        context = yaml.safe_load(f)
    assert context == {"files": []}

def test_init_overwrite_cancelled(tmp_path: Path, monkeypatch):
    """Test that `init` does not overwrite an existing file if cancelled."""
    config_dir = tmp_path / ".config"
    config_dir.mkdir()
    context_file = config_dir / "context.yaml"
    with open(context_file, 'w') as f:
        yaml.dump({"files": ["old_file.txt"]}, f)

    get_config_dir.cache_clear()
    monkeypatch.setattr("ai_context_manager.config.get_config_dir", lambda: config_dir)

    # Simulate user typing "n" and pressing Enter
    result = runner.invoke(app, ["init"], input="n\n")

    assert result.exit_code == 1  # Aborted
    assert "Initialization cancelled" in result.output

    with open(context_file, 'r') as f:
        context = yaml.safe_load(f)
    assert context == {"files": ["old_file.txt"]} # Should be unchanged