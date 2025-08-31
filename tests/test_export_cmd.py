"""Tests for the export command functionality."""

import tempfile
import json
from pathlib import Path
import pytest

from ai_context_manager.commands.export_cmd import ExportCommand


class TestExportCommand:
    """Test cases for the ExportCommand class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        
        # Create test files
        self.create_test_files()
        
        # Create export command
        self.export_cmd = ExportCommand(str(self.test_dir))
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def create_test_files(self):
        """Create test files for export testing."""
        # Create directory structure
        (self.test_dir / "src").mkdir()
        (self.test_dir / "tests").mkdir()
        (self.test_dir / "docs").mkdir()
        
        # Create Python files
        (self.test_dir / "src" / "main.py").write_text('''
import os
import sys

def main():
    """Main function."""
    print("Hello, World!")
    return 0

if __name__ == "__main__":
    main()
''')
        
        (self.test_dir / "src" / "utils.py").write_text('''
import json
from typing import List, Dict, Any

def process_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process data with type hints."""
    return [item for item in data if item.get('active', False)]

def helper_function(name: str) -> str:
    """A helper function."""
    return f"Hello, {name}!"
''')
        
        (self.test_dir / "tests" / "test_main.py").write_text('''
import pytest
from src.main import main

def test_main():
    """Test main function."""
    assert main() == 0

@pytest.mark.parametrize("input,expected", [(1, 1), (2, 2)])
def test_param(input, expected):
    """Test parameterized function."""
    assert input == expected
''')
        
        # Create other files
        (self.test_dir / "README.md").write_text('''
# Test Project

This is a test project for export command testing.

## Features
- Python code
- Tests
- Documentation

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```python
from src.main import main
main()
```
''')
        
        (self.test_dir / "requirements.txt").write_text('''
pytest>=7.0.0
black>=22.0.0
mypy>=0.991
ruff>=0.0.0
''')
        
        (self.test_dir / "docs" / "api.md").write_text('''
# API Documentation

## Functions
- `main()`: Main entry point
- `process_data(data)`: Process data
- `helper_function(name)`: Helper function

## Examples
```python
from src.utils import process_data
data = [{"active": True}, {"active": False}]
result = process_data(data)
```
''')
        
        # Create configuration files
        (self.test_dir / "pyproject.toml").write_text('''
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "test-project"
version = "0.1.0"
description = "A test project"
dependencies = ["pytest>=7.0.0"]

[tool.black]
line-length = 88
target-version = ['py38']

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
''')
        
        # Create hidden files
        (self.test_dir / ".env").write_text('''
SECRET_KEY=your-secret-key
DEBUG=true
DATABASE_URL=sqlite:///test.db
''')
        
        (self.test_dir / ".gitignore").write_text('''
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.env
.coverage
htmlcov/
.tox/
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git
.mypy_cache
.pytest_cache
.hypothesis
''')
    
    def test_export_command_initialization(self):
        """Test ExportCommand initialization."""
        assert self.export_cmd.root_path == str(self.test_dir)
    
    def test_export_command_with_custom_config(self):
        """Test ExportCommand with custom configuration."""
        config = {
            "include_patterns": ["*.py", "*.md"],
            "exclude_patterns": ["__pycache__", "*.pyc"],
            "max_file_size": 1000000
        }
        
        export_cmd = ExportCommand(str(self.test_dir), config=config)
        assert export_cmd.config == config
    
    def test_export_to_markdown(self):
        """Test exporting to markdown format."""
        output_file = self.test_dir / "export.md"
        
        self.export_cmd.export(
            output_file=str(output_file),
            format="markdown",
            include_patterns=["*.py", "*.md"],
            exclude_patterns=["__pycache__", "*.pyc"]
        )
        
        assert output_file.exists()
        
        content = output_file.read_text()
        assert "# Project Export" in content
        assert "## File: src/main.py" in content
        assert "## File: README.md" in content
        assert "def main():" in content
    
    def test_export_to_json(self):
        """Test exporting to JSON format."""
        output_file = self.test_dir / "export.json"
        
        self.export_cmd.export(
            output_file=str(output_file),
            format="json",
            include_patterns=["*.py", "*.md"],
            exclude_patterns=["__pycache__", "*.pyc"]
        )
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert "files" in data
        assert "metadata" in data
        assert len(data["files"]) > 0
        
        # Check if expected files are present
        file_paths = [f["path"] for f in data["files"]]
        assert any("main.py" in path for path in file_paths)
        assert any("README.md" in path for path in file_paths)
    
    def test_export_to_text(self):
        """Test exporting to plain text format."""
        output_file = self.test_dir / "export.txt"
        
        self.export_cmd.export(
            output_file=str(output_file),
            format="text",
            include_patterns=["*.py", "*.md"],
            exclude_patterns=["__pycache__", "*.pyc"]
        )
        
        assert output_file.exists()
        
        content = output_file.read_text()
        assert "Project Export" in content
        assert "File: src/main.py" in content
        assert "def main():" in content
    
    def test_export_with_custom_header(self):
        """Test export with custom header."""
        output_file = self.test_dir / "export.md"
        
        self.export_cmd.export(
            output_file=str(output_file),
            format="markdown",
            include_patterns=["*.py"],
            exclude_patterns=["__pycache__", "*.pyc"],
            header="# Custom Export Header"
        )
        
        content = output_file.read_text()
        assert "# Custom Export Header" in content
    
    def test_export_with_include_patterns(self):
        """Test export with custom include patterns."""
        output_file = self.test_dir / "export.md"
        
        self.export_cmd.export(
            output_file=str(output_file),
            format="markdown",
            include_patterns=["*.py"],
            exclude_patterns=[]
        )
        
        content = output_file.read_text()
        assert "main.py" in content
        assert "utils.py" in content
        assert "README.md" not in content
    
    def test_export_with_exclude_patterns(self):
        """Test export with custom exclude patterns."""
        output_file = self.test_dir / "export.md"
        
        self.export_cmd.export(
            output_file=str(output_file),
            format="markdown",
            include_patterns=["*"],
            exclude_patterns=["*.pyc", "__pycache__", ".git*", ".env"]
        )
        
        content = output_file.read_text()
        assert ".env" not in content
    
    def test_export_hidden_files_included(self):
        """Test export explicitly including hidden files."""
        output_file = self.test_dir / "export.md"
        
        self.export_cmd.export(
            output_file=str(output_file),
            format="markdown",
            include_patterns=["*", ".*"],
            exclude_patterns=["__pycache__", "*.pyc"]
        )
        
        content = output_file.read_text()
        assert ".env" in content
    
    def test_export_with_max_file_size(self):
        """Test export with maximum file size."""
        # Create a large file
        large_file = self.test_dir / "large.py"
        large_file.write_text("x" * 10000)
        
        output_file = self.test_dir / "export.md"
        
        self.export_cmd.export(
            output_file=str(output_file),
            format="markdown",
            include_patterns=["*"],
            exclude_patterns=["__pycache__", "*.pyc"],
            max_file_size=1000
        )
        
        content = output_file.read_text()
        assert "large.py" not in content
    
    def test_export_empty_directory(self):
        """Test export with empty directory."""
        empty_dir = self.test_dir / "empty"
        empty_dir.mkdir()
        
        export_cmd = ExportCommand(str(empty_dir))
        output_file = empty_dir / "export.md"
        
        export_cmd.export(
            output_file=str(output_file),
            format="markdown",
            include_patterns=["*"],
            exclude_patterns=[]
        )
        
        assert output_file.exists()
        
        content = output_file.read_text()
        assert "# Project Export" in content
        assert "No files found" in content
    
    def test_export_nonexistent_directory(self):
        """Test export with nonexistent directory."""
        nonexistent_dir = self.test_dir / "nonexistent"
        
        with pytest.raises(FileNotFoundError):
            export_cmd = ExportCommand(str(nonexistent_dir))
            export_cmd.export(
                output_file="export.md",
                format="markdown"
            )
    
    def test_export_overwrite_existing_file(self):
        """Test overwriting existing export file."""
        output_file = self.test_dir / "export.md"
        output_file.write_text("Existing content")
        
        self.export_cmd.export(
            output_file=str(output_file),
            format="markdown",
            include_patterns=["*.py"],
            exclude_patterns=["__pycache__", "*.pyc"]
        )
        
        content = output_file.read_text()
        assert "Existing content" not in content
        assert "main.py" in content
    
    def test_export_relative_paths(self):
        """Test export with relative paths."""
        # Change to test directory
        import os
        original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        try:
            export_cmd = ExportCommand(".")
            
            output_file = "relative_export.md"
            
            export_cmd.export(
                output_file=output_file,
                format="markdown",
                include_patterns=["*.py"],
                exclude_patterns=["__pycache__", "*.pyc"]
            )
            
            assert Path(output_file).exists()
        finally:
            os.chdir(original_cwd)
    
    def test_export_with_metadata(self):
        """Test export with metadata."""
        output_file = self.test_dir / "export.json"
        
        self.export_cmd.export(
            output_file=str(output_file),
            format="json",
            include_patterns=["*.py"],
            exclude_patterns=["__pycache__", "*.pyc"]
        )
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert "metadata" in data
        assert "export_timestamp" in data["metadata"]
        assert "total_files" in data["metadata"]
        assert "total_size" in data["metadata"]
    
    def test_export_binary_files_excluded(self):
        """Test export with binary files excluded."""
        # Create binary file
        (self.test_dir / "data.bin").write_bytes(b"binary data")
        
        output_file = self.test_dir / "export.md"
        
        self.export_cmd.export(
            output_file=str(output_file),
            format="markdown",
            include_patterns=["*"],
            exclude_patterns=["__pycache__", "*.pyc"]
        )
        
        content = output_file.read_text()
        assert "data.bin" not in content
    
    def test_export_binary_files_included(self):
        """Test export with binary files included."""
        # Create binary file
        (self.test_dir / "data.bin").write_bytes(b"binary data")
        
        output_file = self.test_dir / "export.md"
        
        self.export_cmd.export(
            output_file=str(output_file),
            format="markdown",
            include_patterns=["*"],
            exclude_patterns=["__pycache__", "*.pyc"],
            include_binary=True
        )
        
        content = output_file.read_text()
        assert "data.bin" in content
    
    def test_export_unicode_content(self):
        """Test export with Unicode content."""
        unicode_file = self.test_dir / "unicode.py"
        unicode_file.write_text('''
# -*- coding: utf-8 -*-
print("Hello 世界! 🌍")
print("Привет мир!")
print("مرحبا بالعالم!")
print("こんにちは世界！")
''')
        
        output_file = self.test_dir / "export.md"
        
        self.export_cmd.export(
            output_file=str(output_file),
            format="markdown",
            include_patterns=["*.py"],
            exclude_patterns=["__pycache__", "*.pyc"]
        )
        
        content = output_file.read_text()
        assert "unicode.py" in content
        assert "Hello 世界! 🌍" in content
    
    def test_export_performance(self):
        """Test export performance with many files."""
        import time
        
        # Create many small files
        for i in range(100):
            (self.test_dir / f"file_{i}.py").write_text(f'def func_{i}():\n    return {i}')
        
        output_file = self.test_dir / "export.md"
        
        start_time = time.time()
        self.export_cmd.export(
            output_file=str(output_file),
            format="markdown",
            include_patterns=["*.py"],
            exclude_patterns=["__pycache__", "*.pyc"]
        )
        end_time = time.time()
        
        assert output_file.exists()
        # Should complete within reasonable time (adjust threshold as needed)
        assert (end_time - start_time) < 5.0
    
    def test_export_with_token_counting(self):
        """Test export with token counting."""
        output_file = self.test_dir / "export.json"
        
        self.export_cmd.export(
            output_file=str(output_file),
            format="json",
            include_patterns=["*.py", "*.md"],
            exclude_patterns=["__pycache__", "*.pyc"],
            include_token_count=True
        )
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        files = data["files"]
        for file_info in files:
            if file_info["type"] in ["Python", "Markdown"]:
                assert "tokens" in file_info
                assert isinstance(file_info["tokens"], int)
                assert file_info["tokens"] >= 0
    
    def test_export_nested_directories(self):
        """Test export with nested directory structure."""
        # Create deeply nested structure
        deep_dir = self.test_dir / "src" / "level1" / "level2" / "level3"
        deep_dir.mkdir(parents=True)
        (deep_dir / "deep.py").write_text('print("Deep file")')
        
        output_file = self.test_dir / "export.md"
        
        self.export_cmd.export(
            output_file=str(output_file),
            format="markdown",
            include_patterns=["*.py"],
            exclude_patterns=["__pycache__", "*.pyc"]
        )
        
        content = output_file.read_text()
        assert "deep.py" in content
    
    def test_export_file_ordering(self):
        """Test export file ordering."""
        output_file = self.test_dir / "export.md"
        
        self.export_cmd.export(
            output_file=str(output_file),
            format="markdown",
            include_patterns=["*.py"],
            exclude_patterns=["__pycache__", "*.pyc"]
        )
        
        content = output_file.read_text()
        
        # Check that files appear in alphabetical order
        lines = content.split('\n')
        file_sections = [line for line in lines if line.startswith("## File: ")]
        
        # Extract file paths
        file_paths = [line.replace("## File: ", "") for line in file_sections]
        
        # Should be sorted
        assert file_paths == sorted(file_paths)
    
    def test_export_consistency(self):
        """Test export consistency across multiple runs."""
        output_file1 = self.test_dir / "export1.md"
        output_file2 = self.test_dir / "export2.md"
        
        self.export_cmd.export(
            output_file=str(output_file1),
            format="markdown",
            include_patterns=["*.py"],
            exclude_patterns=["__pycache__", "*.pyc"]
        )
        
        self.export_cmd.export(
            output_file=str(output_file2),
            format="markdown",
            include_patterns=["*.py"],
            exclude_patterns=["__pycache__", "*.pyc"]
        )
        
        content1 = output_file1.read_text()
        content2 = output_file2.read_text()
        
        assert content1 == content2