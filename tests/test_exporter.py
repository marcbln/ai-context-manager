"""Tests for the exporter module."""

import tempfile
import json
import os
from pathlib import Path
import pytest

from ai_context_manager.core.exporter import Exporter
from ai_context_manager.config import Config


class TestExporter:
    """Test cases for the Exporter class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        
        # Create test files
        self.create_test_files()
        
        # Create test config
        self.config = Config()
        self.config.set("project_name", "Test Project")
        self.config.set("version", "1.0.0")
        self.config.set("description", "A test project")
        
        # Create exporter instance
        self.exporter = Exporter(self.config)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def create_test_files(self):
        """Create test files for export testing."""
        # Create source directory structure
        src_dir = self.test_dir / "src"
        src_dir.mkdir()
        
        # Create Python files
        main_py = src_dir / "main.py"
        main_py.write_text('''#!/usr/bin/env python3
"""Main module for the test project."""

def main():
    """Main entry point."""
    print("Hello, World!")
    return 0

if __name__ == "__main__":
    main()
''')
        
        utils_py = src_dir / "utils.py"
        utils_py.write_text('''"""Utility functions."""

def helper_function():
    """A helper function."""
    return "helper"

class HelperClass:
    """A helper class."""
    
    def method(self):
        """A method."""
        return "method"
''')
        
        # Create markdown files
        readme_md = self.test_dir / "README.md"
        readme_md.write_text('''# Test Project

This is a test project for the AI Context Manager.

## Features
- Feature 1
- Feature 2

## Usage
```python
from test_project import main
main()
```
''')
        
        # Create JSON config
        config_json = self.test_dir / "config.json"
        config_json.write_text('''{
  "name": "test-project",
  "version": "1.0.0",
  "dependencies": {
    "python": ">=3.8"
  }
}''')
        
        # Create subdirectories
        tests_dir = self.test_dir / "tests"
        tests_dir.mkdir()
        
        test_file = tests_dir / "test_main.py"
        test_file.write_text('''import unittest
from src.main import main

class TestMain(unittest.TestCase):
    def test_main(self):
        self.assertEqual(main(), 0)

if __name__ == "__main__":
    unittest.main()
''')
    
    def test_exporter_initialization(self):
        """Test Exporter initialization."""
        assert self.exporter.config == self.config
        assert self.exporter.project_name == "Test Project"
        assert self.exporter.version == "1.0.0"
    
    def test_export_markdown_format(self):
        """Test exporting in markdown format."""
        output_file = self.test_dir / "output.md"
        
        # Collect files to export
        files_to_export = [
            str(self.test_dir / "src" / "main.py"),
            str(self.test_dir / "src" / "utils.py"),
            str(self.test_dir / "README.md")
        ]
        
        # Export to markdown
        self.exporter.export_markdown(files_to_export, str(output_file))
        
        # Verify output file exists
        assert output_file.exists()
        
        # Read and verify content
        content = output_file.read_text()
        assert "# Test Project" in content
        assert "## File: src/main.py" in content
        assert "## File: src/utils.py" in content
        assert "## File: README.md" in content
        assert 'def main():' in content
        assert 'class HelperClass:' in content
    
    def test_export_json_format(self):
        """Test exporting in JSON format."""
        output_file = self.test_dir / "output.json"
        
        # Collect files to export
        files_to_export = [
            str(self.test_dir / "src" / "main.py"),
            str(self.test_dir / "README.md")
        ]
        
        # Export to JSON
        self.exporter.export_json(files_to_export, str(output_file))
        
        # Verify output file exists
        assert output_file.exists()
        
        # Read and parse JSON
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        # Verify structure
        assert "metadata" in data
        assert "files" in data
        assert data["metadata"]["project_name"] == "Test Project"
        assert data["metadata"]["version"] == "1.0.0"
        assert len(data["files"]) == 2
        
        # Verify file content
        main_file = next(f for f in data["files"] if f["path"].endswith("main.py"))
        assert "def main():" in main_file["content"]
        assert main_file["language"] == "python"
    
    def test_export_xml_format(self):
        """Test exporting in XML format."""
        output_file = self.test_dir / "output.xml"
        
        # Collect files to export
        files_to_export = [
            str(self.test_dir / "src" / "main.py"),
            str(self.test_dir / "README.md")
        ]
        
        # Export to XML
        self.exporter.export_xml(files_to_export, str(output_file))
        
        # Verify output file exists
        assert output_file.exists()
        
        # Read and verify content
        content = output_file.read_text()
        assert '<?xml version="1.0" encoding="utf-8"?>' in content
        assert '<project name="Test Project"' in content
        assert '<file path=' in content
        assert 'def main():' in content
    
    def test_export_empty_file_list(self):
        """Test exporting with empty file list."""
        output_file = self.test_dir / "empty_output.md"
        
        # Export empty list
        self.exporter.export_markdown([], str(output_file))
        
        # Verify output file exists
        assert output_file.exists()
        
        # Read and verify content
        content = output_file.read_text()
        assert "# Test Project" in content
        assert "## Files" in content
    
    def test_export_single_file(self):
        """Test exporting single file."""
        output_file = self.test_dir / "single_file.md"
        
        # Export single file
        file_to_export = str(self.test_dir / "src" / "main.py")
        self.exporter.export_markdown([file_to_export], str(output_file))
        
        # Verify output
        content = output_file.read_text()
        assert "## File: src/main.py" in content
        assert 'def main():' in content
        assert "README.md" not in content
    
    def test_export_with_metadata(self):
        """Test exporting with metadata enabled."""
        self.config.set("export.include_metadata", True)
        
        output_file = self.test_dir / "with_metadata.md"
        
        files_to_export = [str(self.test_dir / "src" / "main.py")]
        self.exporter.export_markdown(files_to_export, str(output_file))
        
        content = output_file.read_text()
        assert "## Metadata" in content
        assert "Project: Test Project" in content
        assert "Version: 1.0.0" in content
        assert "Total Files: 1" in content
    
    def test_export_without_metadata(self):
        """Test exporting without metadata."""
        self.config.set("export.include_metadata", False)
        
        output_file = self.test_dir / "without_metadata.md"
        
        files_to_export = [str(self.test_dir / "src" / "main.py")]
        self.exporter.export_markdown(files_to_export, str(output_file))
        
        content = output_file.read_text()
        assert "## Metadata" not in content
    
    def test_export_file_language_detection(self):
        """Test automatic language detection for files."""
        files_to_export = [
            str(self.test_dir / "src" / "main.py"),
            str(self.test_dir / "README.md"),
            str(self.test_dir / "config.json")
        ]
        
        output_file = self.test_dir / "languages.json"
        self.exporter.export_json(files_to_export, str(output_file))
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        # Check language detection
        files = {f["path"]: f for f in data["files"]}
        assert files["src/main.py"]["language"] == "python"
        assert files["README.md"]["language"] == "markdown"
        assert files["config.json"]["language"] == "json"
    
    def test_export_binary_file_handling(self):
        """Test handling of binary files."""
        # Create a binary file
        binary_file = self.test_dir / "binary.dat"
        binary_file.write_bytes(b'\x00\x01\x02\x03\x04\x05')
        
        output_file = self.test_dir / "binary_test.md"
        
        # Try to export binary file
        self.exporter.export_markdown([str(binary_file)], str(output_file))
        
        # Should handle gracefully (either skip or include placeholder)
        content = output_file.read_text()
        assert "binary.dat" in content
    
    def test_export_large_file_handling(self):
        """Test handling of large files."""
        # Create a large text file
        large_file = self.test_dir / "large.txt"
        large_content = "This is a test line.\n" * 1000
        large_file.write_text(large_content)
        
        output_file = self.test_dir / "large_test.md"
        
        # Export large file
        self.exporter.export_markdown([str(large_file)], str(output_file))
        
        # Verify it was exported
        content = output_file.read_text()
        assert "large.txt" in content
        assert "This is a test line." in content
    
    def test_export_nested_directory_structure(self):
        """Test exporting files from nested directories."""
        # Create nested structure
        deep_dir = self.test_dir / "src" / "utils" / "helpers"
        deep_dir.mkdir(parents=True)
        
        helper_file = deep_dir / "deep_helper.py"
        helper_file.write_text('def deep_helper():\n    return "deep"')
        
        output_file = self.test_dir / "nested_test.md"
        
        files_to_export = [
            str(helper_file),
            str(self.test_dir / "src" / "main.py")
        ]
        
        self.exporter.export_markdown(files_to_export, str(output_file))
        
        content = output_file.read_text()
        assert "src/utils/helpers/deep_helper.py" in content
        assert "src/main.py" in content
    
    def test_export_file_size_calculation(self):
        """Test file size calculation in exports."""
        files_to_export = [
            str(self.test_dir / "src" / "main.py"),
            str(self.test_dir / "README.md")
        ]
        
        output_file = self.test_dir / "sizes.json"
        self.exporter.export_json(files_to_export, str(output_file))
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        # Check that sizes are included
        for file_info in data["files"]:
            assert "size" in file_info
            assert isinstance(file_info["size"], int)
            assert file_info["size"] > 0
    
    def test_export_relative_paths(self):
        """Test handling of relative paths."""
        # Change to test directory
        original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        try:
            files_to_export = [
                "src/main.py",
                "README.md"
            ]
            
            output_file = "relative_test.md"
            self.exporter.export_markdown(files_to_export, output_file)
            
            assert Path(output_file).exists()
            content = Path(output_file).read_text()
            assert "src/main.py" in content
            
        finally:
            os.chdir(original_cwd)
    
    def test_export_special_characters_in_content(self):
        """Test handling special characters in file content."""
        special_file = self.test_dir / "special.txt"
        special_content = '''
Special characters: !@#$%^&*()_+-=[]{}|;':",./<>?
Unicode: 世界 🌍 Café résumé
Code: `print("Hello")`
HTML: <div>Test</div>
Markdown: **bold** *italic*
'''
        special_file.write_text(special_content)
        
        output_file = self.test_dir / "special_test.md"
        self.exporter.export_markdown([str(special_file)], str(output_file))
        
        content = output_file.read_text()
        assert "Special characters:" in content
        assert "世界" in content
        assert "🌍" in content
    
    def test_export_compression_disabled(self):
        """Test export without compression."""
        self.config.set("export.compress_output", False)
        
        output_file = self.test_dir / "uncompressed.md"
        files_to_export = [str(self.test_dir / "src" / "main.py")]
        
        self.exporter.export_markdown(files_to_export, str(output_file))
        
        # Should create regular file
        assert output_file.exists()
        assert not output_file.with_suffix(".md.gz").exists()
    
    def test_export_file_ordering(self):
        """Test file ordering in exports."""
        files_to_export = [
            str(self.test_dir / "src" / "utils.py"),
            str(self.test_dir / "README.md"),
            str(self.test_dir / "src" / "main.py")
        ]
        
        output_file = self.test_dir / "ordering_test.md"
        self.exporter.export_markdown(files_to_export, str(output_file))
        
        content = output_file.read_text()
        
        # Check that files appear in the specified order
        utils_pos = content.find("src/utils.py")
        readme_pos = content.find("README.md")
        main_pos = content.find("src/main.py")
        
        assert utils_pos < readme_pos < main_pos
    
    def test_export_duplicate_files(self):
        """Test handling duplicate files in list."""
        files_to_export = [
            str(self.test_dir / "src" / "main.py"),
            str(self.test_dir / "src" / "main.py"),  # Duplicate
            str(self.test_dir / "README.md")
        ]
        
        output_file = self.test_dir / "duplicates_test.md"
        self.exporter.export_markdown(files_to_export, str(output_file))
        
        content = output_file.read_text()
        
        # Count occurrences of main.py
        main_count = content.count("## File: src/main.py")
        assert main_count == 1  # Should deduplicate
    
    def test_export_nonexistent_files(self):
        """Test handling non-existent files."""
        files_to_export = [
            str(self.test_dir / "src" / "main.py"),
            str(self.test_dir / "nonexistent.py"),
            str(self.test_dir / "README.md")
        ]
        
        output_file = self.test_dir / "missing_test.md"
        self.exporter.export_markdown(files_to_export, str(output_file))
        
        content = output_file.read_text()
        
        # Should include existing files
        assert "src/main.py" in content
        assert "README.md" in content
        
        # Should handle missing file gracefully
        assert "nonexistent.py" not in content or "File not found" in content
    
    def test_export_empty_files(self):
        """Test handling empty files."""
        empty_file = self.test_dir / "empty.py"
        empty_file.write_text("")
        
        output_file = self.test_dir / "empty_file_test.md"
        self.exporter.export_markdown([str(empty_file)], str(output_file))
        
        content = output_file.read_text()
        assert "empty.py" in content
        # Should handle empty content gracefully
    
    def test_export_with_custom_metadata(self):
        """Test exporting with custom metadata fields."""
        self.config.set("custom_field", "custom_value")
        
        output_file = self.test_dir / "custom_metadata.json"
        files_to_export = [str(self.test_dir / "src" / "main.py")]
        
        self.exporter.export_json(files_to_export, str(output_file))
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        # Check if custom metadata is included
        assert "metadata" in data
        assert data["metadata"]["project_name"] == "Test Project"