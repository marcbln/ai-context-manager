"""Integration tests for AI Context Manager."""

import tempfile
from pathlib import Path
import pytest
from click.testing import CliRunner

from ai_context_manager.cli import cli
from ai_context_manager.core.profile_manager import ProfileManager
from ai_context_manager.core.exporter import Exporter
from ai_context_manager.core.selector import FileSelector


class TestIntegration:
    """Integration tests combining multiple components."""
    
    def test_full_workflow(self, temp_config_dir, temp_project_dir):
        """Test complete workflow from profile creation to export."""
        runner = CliRunner()
        
        # Step 1: Create a profile
        result = runner.invoke(cli, [
            "profile",
            "create",
            "integration-test",
            "--include", "*.py",
            "--include", "*.md",
            "--exclude", "__pycache__/*",
            "--exclude", "*.pyc",
            "--max-size", "102400",
            "--config-dir", str(temp_config_dir)
        ])
        assert result.exit_code == 0
        
        # Step 2: Verify profile was created
        manager = ProfileManager(config_dir=temp_config_dir)
        assert manager.profile_exists("integration-test")
        
        # Step 3: Export using the profile
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = Path(tmp_dir) / "output.md"
            
            result = runner.invoke(cli, [
                "export",
                str(output_file),
                "--profile", "integration-test",
                "--config-dir", str(temp_config_dir)
            ])
            assert result.exit_code == 0
            
            # Verify output
            assert output_file.exists()
            content = output_file.read_text()
            assert "# Project Context" in content
            assert "main.py" in content
            assert "utils.py" in content
            assert "README.md" in content
            assert "__pycache__" not in content
    
    def test_profile_workflow_with_description(self, temp_config_dir, temp_project_dir):
        """Test profile creation with description."""
        runner = CliRunner()
        
        result = runner.invoke(cli, [
            "profile",
            "create",
            "desc-test",
            "--include", "*.py",
            "--description", "Test profile with description",
            "--config-dir", str(temp_config_dir)
        ])
        assert result.exit_code == 0
        
        # Verify description is saved
        manager = ProfileManager(config_dir=temp_config_dir)
        profile = manager.get_profile("desc-test")
        assert profile["description"] == "Test profile with description"
    
    def test_export_with_token_counting(self, temp_config_dir, mock_project_with_large_files):
        """Test export with token counting enabled."""
        runner = CliRunner()
        
        # Create profile
        result = runner.invoke(cli, [
            "profile",
            "create",
            "large-file-test",
            "--include", "*.py",
            "--max-size", "100000",  # 100KB limit
            "--config-dir", str(temp_config_dir)
        ])
        assert result.exit_code == 0
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = Path(tmp_dir) / "output.md"
            result = runner.invoke(cli, [
                "export",
                str(output_file),
                "--profile", "large-file-test",
                "--project-dir", str(mock_project_with_large_files),
                "--config-dir", str(temp_config_dir)
            ])
            assert result.exit_code == 0
            
            content = output_file.read_text()
            assert "small.py" in content
            assert "medium.py" in content
            # huge.py (~200KB) should be excluded
            assert "huge.py" not in content or "excluded" in content.lower()
    
    def test_nested_directory_structure(self, temp_config_dir, mock_project_with_nested_structure):
        """Test handling of nested directory structures."""
        runner = CliRunner()
        
        # Create profile
        runner.invoke(cli, [
            "profile",
            "create",
            "nested-test",
            "--include", "*.py",
            "--include", "*.json",
            "--exclude", ".DS_Store",
            "--config-dir", str(temp_config_dir)
        ])
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = Path(tmp_dir) / "output.md"
            result = runner.invoke(cli, [
                "export",
                str(output_file),
                "--profile", "nested-test",
                "--project-dir", str(mock_project_with_nested_structure),
                "--config-dir", str(temp_config_dir)
            ])
            assert result.exit_code == 0
            
            content = output_file.read_text()
            assert "main.py" in content
            assert "config.json" in content
            assert "module.py" in content
            assert "helper.py" in content
            assert "deep.py" in content
            assert "temp.tmp" not in content
            assert ".DS_Store" not in content
    
    def test_verbose_output_integration(self, temp_config_dir, temp_project_dir):
        """Test verbose output shows detailed information."""
        runner = CliRunner()
        
        # Create profile
        runner.invoke(cli, [
            "profile",
            "create",
            "verbose-test",
            "--include", "*.py",
            "--config-dir", str(temp_config_dir)
        ])
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = Path(tmp_dir) / "output.md"
            result = runner.invoke(cli, [
                "export",
                str(output_file),
                "--profile", "verbose-test",
                "--verbose",
                "--project-dir", str(temp_project_dir),
                "--config-dir", str(temp_config_dir)
            ])
            assert result.exit_code == 0
            
            # Check that verbose output contains processing information
            output = result.output
            assert "Processing" in output or "Including" in output or "Found" in output
    
    def test_binary_file_exclusion(self, temp_config_dir, mock_project_with_binary_files):
        """Test that binary files are properly excluded."""
        runner = CliRunner()
        
        # Create profile
        runner.invoke(cli, [
            "profile",
            "create",
            "binary-test",
            "--include", "*",
            "--config-dir", str(temp_config_dir)
        ])
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = Path(tmp_dir) / "output.md"
            result = runner.invoke(cli, [
                "export",
                str(output_file),
                "--profile", "binary-test",
                "--project-dir", str(mock_project_with_binary_files),
                "--config-dir", str(temp_config_dir)
            ])
            assert result.exit_code == 0
            
            content = output_file.read_text()
            assert "text.py" in content
            assert "readme.md" in content
            # Binary files should be excluded
            assert "image.png" not in content
            assert "data.bin" not in content
    
    def test_different_output_formats(self, temp_config_dir, temp_project_dir):
        """Test export with different output formats."""
        runner = CliRunner()
        
        # Create profile
        runner.invoke(cli, [
            "profile",
            "create",
            "format-test",
            "--include", "*.py",
            "--config-dir", str(temp_config_dir)
        ])
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Test JSON format
            json_file = Path(tmp_dir) / "output.json"
            result = runner.invoke(cli, [
                "export",
                str(json_file),
                "--profile", "format-test",
                "--format", "json",
                "--project-dir", str(temp_project_dir),
                "--config-dir", str(temp_config_dir)
            ])
            assert result.exit_code == 0
            assert json_file.exists()
            
            # Test XML format
            xml_file = Path(tmp_dir) / "output.xml"
            result = runner.invoke(cli, [
                "export",
                str(xml_file),
                "--profile", "format-test",
                "--format", "xml",
                "--project-dir", str(temp_project_dir),
                "--config-dir", str(temp_config_dir)
            ])
            assert result.exit_code == 0
            assert xml_file.exists()
    
    def test_dry_run_mode(self, temp_config_dir, temp_project_dir):
        """Test dry run mode doesn't create files."""
        runner = CliRunner()
        
        # Create profile
        runner.invoke(cli, [
            "profile",
            "create",
            "dry-run-test",
            "--include", "*.py",
            "--config-dir", str(temp_config_dir)
        ])
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = Path(tmp_dir) / "output.md"
            result = runner.invoke(cli, [
                "export",
                str(output_file),
                "--profile", "dry-run-test",
                "--dry-run",
                "--project-dir", str(temp_project_dir),
                "--config-dir", str(temp_config_dir)
            ])
            assert result.exit_code == 0
            assert not output_file.exists()
            assert "main.py" in result.output
            assert "utils.py" in result.output
    
    def test_profile_update_workflow(self, temp_config_dir, temp_project_dir):
        """Test updating an existing profile."""
        runner = CliRunner()
        
        # Create initial profile
        runner.invoke(cli, [
            "profile",
            "create",
            "update-test",
            "--include", "*.py",
            "--exclude", "*.tmp",
            "--config-dir", str(temp_config_dir)
        ])
        
        # Update profile
        result = runner.invoke(cli, [
            "profile",
            "create",
            "update-test",
            "--include", "*.py",
            "--include", "*.md",
            "--exclude", "*.tmp",
            "--exclude", "*.log",
            "--force",
            "--config-dir", str(temp_config_dir)
        ])
        assert result.exit_code == 0
        
        # Verify update
        manager = ProfileManager(config_dir=temp_config_dir)
        profile = manager.get_profile("update-test")
        assert "*.md" in profile["include_patterns"]
        assert "*.log" in profile["exclude_patterns"]
    
    def test_complex_pattern_matching(self, temp_config_dir, mock_project_with_nested_structure):
        """Test complex pattern matching scenarios."""
        runner = CliRunner()
        
        # Create profile with specific patterns
        runner.invoke(cli, [
            "profile",
            "create",
            "complex-patterns",
            "--include", "**/*.py",
            "--include", "**/*.json",
            "--exclude", "**/test_*",
            "--exclude", "**/*_test.py",
            "--config-dir", str(temp_config_dir)
        ])
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = Path(tmp_dir) / "output.md"
            result = runner.invoke(cli, [
                "export",
                str(output_file),
                "--profile", "complex-patterns",
                "--project-dir", str(mock_project_with_nested_structure),
                "--config-dir", str(temp_config_dir)
            ])
            assert result.exit_code == 0
            
            content = output_file.read_text()
            assert "main.py" in content
            assert "config.json" in content
            assert "module.py" in content
            assert "helper.py" in content
            assert "deep.py" in content