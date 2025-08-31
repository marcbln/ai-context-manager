"""Tests for the CLI interface."""

import tempfile
import json
from pathlib import Path
import pytest
from click.testing import CliRunner

from ai_context_manager.cli import cli


class TestCLI:
    """Test cases for the CLI interface."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        
        # Create test project structure
        self.create_test_project()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def create_test_project(self):
        """Create a test project structure."""
        # Create directories
        (self.test_dir / "src").mkdir()
        (self.test_dir / "tests").mkdir()
        (self.test_dir / "docs").mkdir()
        
        # Create Python files
        (self.test_dir / "src" / "main.py").write_text('''
def main():
    """Main function."""
    print("Hello, World!")
    return 0

if __name__ == "__main__":
    main()
''')
        
        (self.test_dir / "src" / "utils.py").write_text('''
def helper(name):
    """Helper function."""
    return f"Hello, {name}!"
''')
        
        (self.test_dir / "tests" / "test_main.py").write_text('''
import pytest
from src.main import main

def test_main():
    assert main() == 0
''')
        
        # Create other files
        (self.test_dir / "README.md").write_text('''
# Test Project

This is a test project.
''')
        
        (self.test_dir / "requirements.txt").write_text('''
pytest>=7.0.0
''')
    
    def test_cli_help(self):
        """Test CLI help command."""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "AI Context Manager CLI" in result.output
    
    def test_export_command_help(self):
        """Test export command help."""
        result = self.runner.invoke(cli, ['export', '--help'])
        assert result.exit_code == 0
        assert "Export project files" in result.output
    
    def test_export_command_basic(self):
        """Test basic export command."""
        with self.runner.isolated_filesystem():
            # Copy test project
            import shutil
            shutil.copytree(str(self.test_dir), "test_project")
            
            result = self.runner.invoke(cli, [
                'export',
                '--path', 'test_project',
                '--output', 'export.md',
                '--format', 'markdown'
            ])
            
            assert result.exit_code == 0
            assert Path('export.md').exists()
            
            content = Path('export.md').read_text()
            assert "# Project Export" in content
            assert "src/main.py" in content
    
    def test_export_command_json_format(self):
        """Test export command with JSON format."""
        with self.runner.isolated_filesystem():
            shutil.copytree(str(self.test_dir), "test_project")
            
            result = self.runner.invoke(cli, [
                'export',
                '--path', 'test_project',
                '--output', 'export.json',
                '--format', 'json'
            ])
            
            assert result.exit_code == 0
            assert Path('export.json').exists()
            
            with open('export.json', 'r') as f:
                data = json.load(f)
            
            assert "files" in data
            assert isinstance(data["files"], list)
    
    def test_export_command_with_include_patterns(self):
        """Test export command with include patterns."""
        with self.runner.isolated_filesystem():
            shutil.copytree(str(self.test_dir), "test_project")
            
            result = self.runner.invoke(cli, [
                'export',
                '--path', 'test_project',
                '--output', 'export.md',
                '--format', 'markdown',
                '--include', '*.py'
            ])
            
            assert result.exit_code == 0
            
            content = Path('export.md').read_text()
            assert "src/main.py" in content
            assert "README.md" not in content
    
    def test_export_command_with_exclude_patterns(self):
        """Test export command with exclude patterns."""
        with self.runner.isolated_filesystem():
            shutil.copytree(str(self.test_dir), "test_project")
            
            result = self.runner.invoke(cli, [
                'export',
                '--path', 'test_project',
                '--output', 'export.md',
                '--format', 'markdown',
                '--exclude', 'tests/*'
            ])
            
            assert result.exit_code == 0
            
            content = Path('export.md').read_text()
            assert "src/main.py" in content
            assert "tests/test_main.py" not in content
    
    def test_export_command_with_token_counting(self):
        """Test export command with token counting."""
        with self.runner.isolated_filesystem():
            shutil.copytree(str(self.test_dir), "test_project")
            
            result = self.runner.invoke(cli, [
                'export',
                '--path', 'test_project',
                '--output', 'export.json',
                '--format', 'json',
                '--tokens'
            ])
            
            assert result.exit_code == 0
            
            with open('export.json', 'r') as f:
                data = json.load(f)
            
            # Check that token counts are included
            for file_info in data["files"]:
                if file_info["type"] == "Python":
                    assert "tokens" in file_info
                    assert isinstance(file_info["tokens"], int)
    
    def test_export_command_with_project_name(self):
        """Test export command with custom project name."""
        with self.runner.isolated_filesystem():
            shutil.copytree(str(self.test_dir), "test_project")
            
            result = self.runner.invoke(cli, [
                'export',
                '--path', 'test_project',
                '--output', 'export.json',
                '--format', 'json',
                '--name', 'My Custom Project'
            ])
            
            assert result.exit_code == 0
            
            with open('export.json', 'r') as f:
                data = json.load(f)
            
            assert data["project_name"] == "My Custom Project"
    
    def test_export_command_default_path(self):
        """Test export command with default path."""
        with self.runner.isolated_filesystem():
            # Create project in current directory
            Path('main.py').write_text('print("Hello")')
            Path('README.md').write_text('# Test')
            
            result = self.runner.invoke(cli, [
                'export',
                '--output', 'export.md'
            ])
            
            assert result.exit_code == 0
            assert Path('export.md').exists()
            
            content = Path('export.md').read_text()
            assert "main.py" in content
            assert "README.md" in content
    
    def test_export_command_invalid_format(self):
        """Test export command with invalid format."""
        with self.runner.isolated_filesystem():
            shutil.copytree(str(self.test_dir), "test_project")
            
            result = self.runner.invoke(cli, [
                'export',
                '--path', 'test_project',
                '--output', 'export.txt',
                '--format', 'invalid'
            ])
            
            assert result.exit_code != 0
            assert "Invalid format" in result.output or "invalid" in result.output.lower()
    
    def test_export_command_nonexistent_path(self):
        """Test export command with nonexistent path."""
        result = self.runner.invoke(cli, [
            'export',
            '--path', 'nonexistent',
            '--output', 'export.md'
        ])
        
        assert result.exit_code != 0
    
    def test_export_command_empty_directory(self):
        """Test export command with empty directory."""
        with self.runner.isolated_filesystem():
            Path('empty').mkdir()
            
            result = self.runner.invoke(cli, [
                'export',
                '--path', 'empty',
                '--output', 'export.md'
            ])
            
            assert result.exit_code == 0
            assert Path('export.md').exists()
    
    def test_export_command_verbose(self):
        """Test export command with verbose output."""
        with self.runner.isolated_filesystem():
            shutil.copytree(str(self.test_dir), "test_project")
            
            result = self.runner.invoke(cli, [
                'export',
                '--path', 'test_project',
                '--output', 'export.md',
                '--verbose'
            ])
            
            assert result.exit_code == 0
            # Should show processing information
            assert "Processing" in result.output or "Exporting" in result.output
    
    def test_export_command_multiple_include_patterns(self):
        """Test export command with multiple include patterns."""
        with self.runner.isolated_filesystem():
            shutil.copytree(str(self.test_dir), "test_project")
            
            result = self.runner.invoke(cli, [
                'export',
                '--path', 'test_project',
                '--output', 'export.md',
                '--include', '*.py',
                '--include', '*.md'
            ])
            
            assert result.exit_code == 0
            
            content = Path('export.md').read_text()
            assert "src/main.py" in content
            assert "README.md" in content
            assert "requirements.txt" not in content
    
    def test_export_command_multiple_exclude_patterns(self):
        """Test export command with multiple exclude patterns."""
        with self.runner.isolated_filesystem():
            shutil.copytree(str(self.test_dir), "test_project")
            
            result = self.runner.invoke(cli, [
                'export',
                '--path', 'test_project',
                '--output', 'export.md',
                '--exclude', 'tests/*',
                '--exclude', 'docs/*'
            ])
            
            assert result.exit_code == 0
            
            content = Path('export.md').read_text()
            assert "src/main.py" in content
            assert "tests/test_main.py" not in content
            assert "docs/" not in content
    
    def test_export_command_nested_directories(self):
        """Test export command with nested directories."""
        with self.runner.isolated_filesystem():
            # Create nested structure
            Path('project/src/deep/nested').mkdir(parents=True)
            Path('project/src/deep/nested/file.py').write_text('print("deep")')
            
            result = self.runner.invoke(cli, [
                'export',
                '--path', 'project',
                '--output', 'export.md'
            ])
            
            assert result.exit_code == 0
            
            content = Path('export.md').read_text()
            assert "src/deep/nested/file.py" in content
    
    def test_export_command_performance(self):
        """Test export command performance with many files."""
        import time
        
        with self.runner.isolated_filesystem():
            # Create many files
            Path('large_project').mkdir()
            for i in range(100):
                Path(f'large_project/file_{i}.py').write_text(f'def func_{i}(): return {i}')
            
            start_time = time.time()
            result = self.runner.invoke(cli, [
                'export',
                '--path', 'large_project',
                '--output', 'export.md'
            ])
            end_time = time.time()
            
            assert result.exit_code == 0
            assert Path('export.md').exists()
            # Should complete within reasonable time
            assert (end_time - start_time) < 10.0
    
    def test_export_command_output_directory_creation(self):
        """Test export command creates output directory if needed."""
        with self.runner.isolated_filesystem():
            shutil.copytree(str(self.test_dir), "test_project")
            
            result = self.runner.invoke(cli, [
                'export',
                '--path', 'test_project',
                '--output', 'output/export.md'
            ])
            
            assert result.exit_code == 0
            assert Path('output/export.md').exists()
    
    def test_export_command_file_content_preservation(self):
        """Test that file content is preserved correctly in export."""
        with self.runner.isolated_filesystem():
            shutil.copytree(str(self.test_dir), "test_project")
            
            result = self.runner.invoke(cli, [
                'export',
                '--path', 'test_project',
                '--output', 'export.md'
            ])
            
            assert result.exit_code == 0
            
            content = Path('export.md').read_text()
            
            # Check that actual code content is included
            assert 'def main():' in content
            assert 'print("Hello, World!")' in content
            assert 'return 0' in content
    
    def test_export_command_json_structure(self):
        """Test JSON export structure."""
        with self.runner.isolated_filesystem():
            shutil.copytree(str(self.test_dir), "test_project")
            
            result = self.runner.invoke(cli, [
                'export',
                '--path', 'test_project',
                '--output', 'export.json',
                '--format', 'json'
            ])
            
            assert result.exit_code == 0
            
            with open('export.json', 'r') as f:
                data = json.load(f)
            
            # Check required fields
            assert "project_name" in data
            assert "export_date" in data
            assert "files" in data
            assert isinstance(data["files"], list)
            
            # Check file structure
            for file_info in data["files"]:
                assert "path" in file_info
                assert "type" in file_info
                assert "content" in file_info
                assert isinstance(file_info["content"], str)
    
    def test_export_command_error_handling(self):
        """Test error handling in export command."""
        with self.runner.isolated_filesystem():
            # Try to export a file instead of directory
            Path('not_a_dir.txt').write_text('test')
            
            result = self.runner.invoke(cli, [
                'export',
                '--path', 'not_a_dir.txt',
                '--output', 'export.md'
            ])
            
            assert result.exit_code != 0