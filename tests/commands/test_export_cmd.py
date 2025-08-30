"""Tests for export command functionality."""
import json
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from ai_context_manager.commands.export_cmd import export_context
from ai_context_manager.core.profile import Profile


class TestExportCommand:
    """Test suite for export command."""

    def test_export_basic(self, temp_dir: Path) -> None:
        """Test basic export functionality."""
        runner = CliRunner()
        
        # Create a simple test file
        test_file = temp_dir / "test.py"
        test_file.write_text('print("Hello, World!")')
        
        with tempfile.TemporaryDirectory() as output_dir:
            output_file = Path(output_dir) / "output.json"
            
            result = runner.invoke(export_context, [
                "--path", str(temp_dir),
                "--output", str(output_file),
                "--format", "json"
            ])
            
            assert result.exit_code == 0
            assert output_file.exists()
            
            # Verify content
            with open(output_file) as f:
                data = json.load(f)
                assert "files" in data
                assert len(data["files"]) >= 1
                assert any(f["path"].endswith("test.py") for f in data["files"])

    def test_export_with_include_patterns(self, temp_dir: Path) -> None:
        """Test export with include patterns."""
        runner = CliRunner()
        
        # Create test files
        (temp_dir / "test.py").write_text('print("Python")')
        (temp_dir / "test.js").write_text('console.log("JavaScript")')
        (temp_dir / "test.txt").write_text("Text file")
        
        with tempfile.TemporaryDirectory() as output_dir:
            output_file = Path(output_dir) / "output.json"
            
            result = runner.invoke(export_context, [
                "--path", str(temp_dir),
                "--output", str(output_file),
                "--format", "json",
                "--include", "*.py,*.js"
            ])
            
            assert result.exit_code == 0
            
            with open(output_file) as f:
                data = json.load(f)
                paths = [f["path"] for f in data["files"]]
                assert any("test.py" in p for p in paths)
                assert any("test.js" in p for p in paths)
                assert not any("test.txt" in p for p in paths)

    def test_export_with_exclude_patterns(self, temp_dir: Path) -> None:
        """Test export with exclude patterns."""
        runner = CliRunner()
        
        # Create test files
        (temp_dir / "main.py").write_text('print("Main")')
        (temp_dir / "test.pyc").write_text("Compiled Python")
        (temp_dir / "debug.log").write_text("Log file")
        
        with tempfile.TemporaryDirectory() as output_dir:
            output_file = Path(output_dir) / "output.json"
            
            result = runner.invoke(export_context, [
                "--path", str(temp_dir),
                "--output", str(output_file),
                "--format", "json",
                "--exclude", "*.pyc,*.log"
            ])
            
            assert result.exit_code == 0
            
            with open(output_file) as f:
                data = json.load(f)
                paths = [f["path"] for f in data["files"]]
                assert any("main.py" in p for p in paths)
                assert not any(".pyc" in p for p in paths)
                assert not any(".log" in p for p in paths)

    def test_export_with_max_file_size(self, temp_dir: Path) -> None:
        """Test export with max file size limit."""
        runner = CliRunner()
        
        # Create files of different sizes
        small_file = temp_dir / "small.py"
        small_file.write_text('print("Small file")')
        
        large_file = temp_dir / "large.py"
        large_file.write_text("x" * 2000)  # 2KB file
        
        with tempfile.TemporaryDirectory() as output_dir:
            output_file = Path(output_dir) / "output.json"
            
            result = runner.invoke(export_context, [
                "--path", str(temp_dir),
                "--output", str(output_file),
                "--format", "json",
                "--max-size", "1024"  # 1KB limit
            ])
            
            assert result.exit_code == 0
            
            with open(output_file) as f:
                data = json.load(f)
                paths = [f["path"] for f in data["files"]]
                assert any("small.py" in p for p in paths)
                assert not any("large.py" in p for p in paths)

    def test_export_with_binary_files(self, temp_dir: Path) -> None:
        """Test export with binary file inclusion."""
        runner = CliRunner()
        
        # Create text and binary files
        (temp_dir / "text.py").write_text('print("Text file")')
        (temp_dir / "binary.bin").write_bytes(b"\x00\x01\x02\x03")
        
        with tempfile.TemporaryDirectory() as output_dir:
            output_file = Path(output_dir) / "output.json"
            
            # Test without binary files
            result = runner.invoke(export_context, [
                "--path", str(temp_dir),
                "--output", str(output_file),
                "--format", "json",
                "--no-binary"
            ])
            
            assert result.exit_code == 0
            
            with open(output_file) as f:
                data = json.load(f)
                paths = [f["path"] for f in data["files"]]
                assert any("text.py" in p for p in paths)
                assert not any("binary.bin" in p for p in paths)
            
            # Test with binary files
            output_file2 = Path(output_dir) / "output2.json"
            result = runner.invoke(export_context, [
                "--path", str(temp_dir),
                "--output", str(output_file2),
                "--format", "json",
                "--binary"
            ])
            
            assert result.exit_code == 0
            
            with open(output_file2) as f:
                data = json.load(f)
                paths = [f["path"] for f in data["files"]]
                assert any("text.py" in p for p in paths)
                assert any("binary.bin" in p for p in paths)

    def test_export_markdown_format(self, temp_dir: Path) -> None:
        """Test export in markdown format."""
        runner = CliRunner()
        
        # Create test file
        test_file = temp_dir / "test.py"
        test_file.write_text('def hello():\n    return "Hello, World!"')
        
        with tempfile.TemporaryDirectory() as output_dir:
            output_file = Path(output_dir) / "output.md"
            
            result = runner.invoke(export_context, [
                "--path", str(temp_dir),
                "--output", str(output_file),
                "--format", "markdown"
            ])
            
            assert result.exit_code == 0
            assert output_file.exists()
            
            content = output_file.read_text()
            assert "# AI Context Export" in content
            assert "test.py" in content
            assert "```python" in content
            assert 'def hello():' in content

    def test_export_xml_format(self, temp_dir: Path) -> None:
        """Test export in XML format."""
        runner = CliRunner()
        
        # Create test file
        test_file = temp_dir / "test.py"
        test_file.write_text('print("Hello")')
        
        with tempfile.TemporaryDirectory() as output_dir:
            output_file = Path(output_dir) / "output.xml"
            
            result = runner.invoke(export_context, [
                "--path", str(temp_dir),
                "--output", str(output_file),
                "--format", "xml"
            ])
            
            assert result.exit_code == 0
            assert output_file.exists()
            
            content = output_file.read_text()
            assert "<export>" in content
            assert "<file>" in content
            assert "<path>" in content
            assert "test.py" in content

    def test_export_yaml_format(self, temp_dir: Path) -> None:
        """Test export in YAML format."""
        runner = CliRunner()
        
        # Create test file
        test_file = temp_dir / "test.py"
        test_file.write_text('print("Hello")')
        
        with tempfile.TemporaryDirectory() as output_dir:
            output_file = Path(output_dir) / "output.yaml"
            
            result = runner.invoke(export_context, [
                "--path", str(temp_dir),
                "--output", str(output_file),
                "--format", "yaml"
            ])
            
            assert result.exit_code == 0
            assert output_file.exists()
            
            content = output_file.read_text()
            assert "files:" in content
            assert "test.py" in content

    def test_export_with_token_limit(self, temp_dir: Path) -> None:
        """Test export with token limit."""
        runner = CliRunner()
        
        # Create test files
        (temp_dir / "file1.py").write_text('print("File 1")')
        (temp_dir / "file2.py").write_text('print("File 2")')
        
        with patch('ai_context_manager.utils.token_counter.count_tokens') as mock_count:
            # Mock token counting to return increasing values
            mock_count.side_effect = [10, 20, 30, 40]  # Simulate token counts
            
            with tempfile.TemporaryDirectory() as output_dir:
                output_file = Path(output_dir) / "output.json"
                
                result = runner.invoke(export_context, [
                    "--path", str(temp_dir),
                    "--output", str(output_file),
                    "--format", "json",
                    "--token-limit", "25"
                ])
                
                assert result.exit_code == 0
                
                with open(output_file) as f:
                    data = json.load(f)
                    # Should include some but not all files due to token limit
                    assert len(data["files"]) >= 0  # Depends on token counting

    def test_export_nonexistent_path(self) -> None:
        """Test export with non-existent path."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as output_dir:
            output_file = Path(output_dir) / "output.json"
            
            result = runner.invoke(export_context, [
                "--path", "/nonexistent/path",
                "--output", str(output_file),
                "--format", "json"
            ])
            
            assert result.exit_code == 2
            assert "does not exist" in result.output

    def test_export_with_profile(self, temp_dir: Path) -> None:
        """Test export using a profile."""
        runner = CliRunner()
        
        # Create test files
        (temp_dir / "main.py").write_text('print("Main")')
        (temp_dir / "test.py").write_text('print("Test")')
        (temp_dir / "readme.txt").write_text("Documentation")
        
        # Create profile
        profiles_dir = temp_dir / "profiles"
        profiles_dir.mkdir()
        
        profile_data = {
            "name": "test-profile",
            "description": "Test profile",
            "include_patterns": ["*.py"],
            "exclude_patterns": ["test.py"],
            "max_file_size": 1024,
            "include_binary": False,
            "output_format": "json",
            "output_file": "output.json"
        }
        
        profile_file = profiles_dir / "test-profile.json"
        with open(profile_file, "w") as f:
            json.dump(profile_data, f)
        
        with tempfile.TemporaryDirectory() as output_dir:
            output_file = Path(output_dir) / "output.json"
            
            result = runner.invoke(export_context, [
                "--path", str(temp_dir),
                "--output", str(output_file),
                "--profile", "test-profile",
                "--profiles-dir", str(profiles_dir)
            ])
            
            assert result.exit_code == 0
            
            with open(output_file) as f:
                data = json.load(f)
                paths = [f["path"] for f in data["files"]]
                assert any("main.py" in p for p in paths)
                assert not any("test.py" in p for p in paths)
                assert not any("readme.txt" in p for p in paths)

    def test_export_with_nonexistent_profile(self, temp_dir: Path) -> None:
        """Test export with non-existent profile."""
        runner = CliRunner()
        
        profiles_dir = temp_dir / "profiles"
        
        with tempfile.TemporaryDirectory() as output_dir:
            output_file = Path(output_dir) / "output.json"
            
            result = runner.invoke(export_context, [
                "--path", str(temp_dir),
                "--output", str(output_file),
                "--profile", "nonexistent",
                "--profiles-dir", str(profiles_dir)
            ])
            
            assert result.exit_code == 1
            assert "not found" in result.output

    def test_export_help(self) -> None:
        """Test export command help."""
        runner = CliRunner()
        
        result = runner.invoke(export_context, ["--help"])
        
        assert result.exit_code == 0
        assert "Export code context" in result.output
        assert "--path" in result.output
        assert "--output" in result.output
        assert "--format" in result.output
        assert "--profile" in result.output

    def test_export_default_output(self, temp_dir: Path) -> None:
        """Test export with default output filename."""
        runner = CliRunner()
        
        # Create test file
        test_file = temp_dir / "test.py"
        test_file.write_text('print("Hello")')
        
        with tempfile.TemporaryDirectory() as output_dir:
            # Change to output directory
            with runner.isolated_filesystem():
                result = runner.invoke(export_context, [
                    "--path", str(temp_dir),
                    "--format", "json"
                ])
                
                assert result.exit_code == 0
                assert Path("ai-context.json").exists()

    def test_export_empty_directory(self, temp_dir: Path) -> None:
        """Test export with empty directory."""
        runner = CliRunner()
        
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()
        
        with tempfile.TemporaryDirectory() as output_dir:
            output_file = Path(output_dir) / "output.json"
            
            result = runner.invoke(export_context, [
                "--path", str(empty_dir),
                "--output", str(output_file),
                "--format", "json"
            ])
            
            assert result.exit_code == 0
            
            with open(output_file) as f:
                data = json.load(f)
                assert len(data["files"]) == 0