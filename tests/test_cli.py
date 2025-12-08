"""Tests for the main CLI entry point."""
from typer.testing import CliRunner
from ai_context_manager.cli import app

def test_version():
    """Test that version command works."""
    runner = CliRunner()
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "AI Context Manager v0.2.0" in result.output

def test_help():
    """Test that help command works."""
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Visual Context Manager" in result.output
    assert "select" in result.output
    assert "export" in result.output
    assert "generate" in result.output
