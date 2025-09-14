from pathlib import Path
import yaml
from typer.testing import CliRunner

from ai_context_manager.cli import app
from ai_context_manager.config import get_config_dir

runner = CliRunner()

def test_import_directory(tmp_path: Path, monkeypatch):
    """Test importing a directory structure."""
    config_dir = tmp_path / ".config"
    get_config_dir.cache_clear()
    monkeypatch.setattr("ai_context_manager.config.get_config_dir", lambda: config_dir)
    
    # Create a project structure to import
    project_dir = tmp_path / "my_project"
    src_dir = project_dir / "src"
    src_dir.mkdir(parents=True)
    (src_dir / "main.py").touch()
    (project_dir / "README.md").touch()
    
    result = runner.invoke(app, ["import", "directory", str(project_dir), "--base-path", str(project_dir)])
    
    assert result.exit_code == 0
    assert "Added 2 new file(s) to context" in result.output
    
    context_file = config_dir / "context.yaml"
    with open(context_file, 'r') as f:
        context = yaml.safe_load(f)
    
    # Paths should be relative to the specified base_path
    expected_files = sorted(["src/main.py", "README.md"])
    assert sorted(context["files"]) == expected_files