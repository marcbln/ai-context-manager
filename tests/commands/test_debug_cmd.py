from typer.testing import CliRunner
from pathlib import Path
import yaml

from ai_context_manager.cli import app
from ai_context_manager.config import get_config_dir

runner = CliRunner()


def test_debug_command_exists():
    """Test that the 'debug' command is registered and shows subcommands."""
    result = runner.invoke(app, ["debug", "--help"])
    assert result.exit_code == 0
    assert "Create a debug context from a stack trace" in result.output
    assert "from-trace" in result.output


def test_from_trace_requires_input(tmp_path: Path, monkeypatch):
    """Invoking without stdin should error with helpful message."""
    config_dir = tmp_path / ".config"
    get_config_dir.cache_clear()
    monkeypatch.setattr("ai_context_manager.config.get_config_dir", lambda: config_dir)

    result = runner.invoke(app, ["debug", "from-trace", "--base-path", str(tmp_path)], input="")
    assert result.exit_code != 0
    assert "Empty input" in result.output or "No input received" in result.output


def test_from_trace_parses_and_resolves(tmp_path: Path, monkeypatch):
    """Parse typical stack trace paths and resolve them under base-path, updating context."""
    # Setup config dir
    config_dir = tmp_path / ".config"
    get_config_dir.cache_clear()
    monkeypatch.setattr("ai_context_manager.config.get_config_dir", lambda: config_dir)

    # Create a mock project structure
    src_dir = tmp_path / "app" / "src" / "utils"
    src_dir.mkdir(parents=True)
    file_a = src_dir / "a.py"
    file_a.write_text("print('a')\n")

    app_dir = tmp_path / "app"
    file_main = app_dir / "main.py"
    file_main.write_text("print('main')\n")

    # Simulated stack trace text with different formats
    trace = """
Traceback (most recent call last):
  File "/container/root/app/src/utils/a.py", line 12, in <module>
    from app.main import run
  at /container/root/app/main.py:34
"""

    result = runner.invoke(
        app,
        ["debug", "from-trace", "--base-path", str(tmp_path)],
        input=trace,
    )

    assert result.exit_code == 0
    # Context file should contain both resolved absolute paths
    context_file = config_dir / "context.yaml"
    assert context_file.exists()
    context = yaml.safe_load(context_file.read_text())
    files = context.get("files", [])
    assert str(file_a.resolve()) in files
    assert str(file_main.resolve()) in files


def test_from_trace_reports_unresolved(tmp_path: Path, monkeypatch):
    """Unmatched paths should be reported as unresolved."""
    config_dir = tmp_path / ".config"
    get_config_dir.cache_clear()
    monkeypatch.setattr("ai_context_manager.config.get_config_dir", lambda: config_dir)

    # Only create one file so the other stays unresolved
    created = tmp_path / "lib" / "b.py"
    created.parent.mkdir(parents=True)
    created.write_text("print('b')\n")

    trace = "in /service/lib/b.py line 9\n" \
            "in /service/missing/c.py line 3\n"

    result = runner.invoke(
        app,
        ["debug", "from-trace", "--base-path", str(tmp_path)],
        input=trace,
    )

    assert result.exit_code == 0
    assert "Unresolved paths" in result.output
    assert "missing/c.py" in result.output


def test_from_trace_with_output_markdown_includes_original_trace(tmp_path: Path, monkeypatch):
    """When --output is given, exported markdown should include Original Error Trace section."""
    config_dir = tmp_path / ".config"
    get_config_dir.cache_clear()
    monkeypatch.setattr("ai_context_manager.config.get_config_dir", lambda: config_dir)

    # Create files
    d = tmp_path / "src"
    d.mkdir()
    f = d / "x.py"
    f.write_text("print('x')\n")

    trace = "/workspace/src/x.py:123\nValueError: boom\n"
    out = tmp_path / "debug_context.md"

    result = runner.invoke(
        app,
        [
            "debug",
            "from-trace",
            "--base-path",
            str(tmp_path),
            "--output",
            str(out),
            "--format",
            "markdown",
        ],
        input=trace,
    )

    assert result.exit_code == 0
    assert out.exists()
    content = out.read_text()
    assert "Original Error Trace" in content
    assert "x.py:123" in content
    # Also contains exported file content section from exporter
    assert "File Contents" in content or "files" in content
