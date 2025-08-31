"""Tests for the profile command functionality."""

import tempfile
import json
from pathlib import Path
import pytest

from ai_context_manager.commands.profile_cmd import ProfileCommand


class TestProfileCommand:
    """Test cases for the ProfileCommand class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        
        # Create test files
        self.create_test_files()
        
        # Create profile command
        self.profile_cmd = ProfileCommand(str(self.test_dir))
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def create_test_files(self):
        """Create test files for profile testing."""
        # Create directory structure
        (self.test_dir / "src").mkdir()
        (self.test_dir / "tests").mkdir()
        (self.test_dir / "docs").mkdir()
        
        # Create Python files
        (self.test_dir / "src" / "main.py").write_text('''
import os
import sys

def main():
    print("Hello, World!")
    return 0

if __name__ == "__main__":
    main()
''')
        
        (self.test_dir / "src" / "utils.py").write_text('''
import json
from typing import List, Dict

def process_data(data: List[Dict]) -> List[Dict]:
    """Process data with type hints."""
    return [item for item in data if item.get('active', False)]

def helper_function():
    """A helper function."""
    return "helper"
''')
        
        (self.test_dir / "tests" / "test_main.py").write_text('''
import pytest
from src.main import main

def test_main():
    assert main() == 0

@pytest.mark.parametrize("input,expected", [(1, 1), (2, 2)])
def test_param(input, expected):
    assert input == expected
''')
        
        # Create other files
        (self.test_dir / "README.md").write_text('''
# Test Project

This is a test project for profiling.

## Features
- Python code
- Tests
- Documentation
''')
        
        (self.test_dir / "requirements.txt").write_text('''
pytest>=7.0.0
black>=22.0.0
mypy>=0.991
''')
        
        (self.test_dir / "docs" / "api.md").write_text('''
# API Documentation

## Functions
- main()
- process_data()
- helper_function()
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
''')
        
        (self.test_dir / ".gitignore").write_text('''
__pycache__/
*.pyc
.env
venv/
''')
    
    def test_profile_command_initialization(self):
        """Test ProfileCommand initialization."""
        assert self.profile_cmd.root_path == str(self.test_dir)
    
    def test_profile_command_with_custom_config(self):
        """Test ProfileCommand with custom configuration."""
        config = {
            "include_patterns": ["*.py", "*.md"],
            "exclude_patterns": ["__pycache__", "*.pyc"],
            "max_file_size": 1000000
        }
        
        profile_cmd = ProfileCommand(str(self.test_dir), config=config)
        assert profile_cmd.config == config
    
    def test_generate_profile(self):
        """Test generating a project profile."""
        profile = self.profile_cmd.generate_profile()
        
        assert isinstance(profile, dict)
        assert "metadata" in profile
        assert "summary" in profile
        assert "files" in profile
        assert "structure" in profile
        assert "languages" in profile
    
    def test_profile_metadata(self):
        """Test profile metadata."""
        profile = self.profile_cmd.generate_profile()
        
        metadata = profile["metadata"]
        assert "project_name" in metadata
        assert "root_path" in metadata
        assert "generated_at" in metadata
        assert "total_files" in metadata
        assert "total_size" in metadata
    
    def test_profile_summary(self):
        """Test profile summary."""
        profile = self.profile_cmd.generate_profile()
        
        summary = profile["summary"]
        assert "total_files" in summary
        assert "total_directories" in summary
        assert "total_size" in summary
        assert "file_types" in summary
        assert "languages" in summary
    
    def test_profile_files(self):
        """Test profile files information."""
        profile = self.profile_cmd.generate_profile()
        
        files = profile["files"]
        assert isinstance(files, list)
        assert len(files) > 0
        
        # Check file details
        for file_info in files:
            assert "path" in file_info
            assert "size" in file_info
            assert "type" in file_info
            assert "language" in file_info
    
    def test_profile_structure(self):
        """Test profile directory structure."""
        profile = self.profile_cmd.generate_profile()
        
        structure = profile["structure"]
        assert isinstance(structure, dict)
        assert "type" in structure
        assert "name" in structure
        assert "children" in structure
    
    def test_profile_languages(self):
        """Test profile language analysis."""
        profile = self.profile_cmd.generate_profile()
        
        languages = profile["languages"]
        assert isinstance(languages, dict)
        
        # Should have Python files
        assert "Python" in languages
        python_info = languages["Python"]
        assert "files" in python_info
        assert "lines" in python_info
        assert "size" in python_info
    
    def test_profile_with_include_patterns(self):
        """Test profile with include patterns."""
        config = {
            "include_patterns": ["*.py"],
            "exclude_patterns": []
        }
        
        profile_cmd = ProfileCommand(str(self.test_dir), config=config)
        profile = profile_cmd.generate_profile()
        
        # Should only include Python files
        files = profile["files"]
        python_files = [f for f in files if f["type"] == "Python"]
        non_python_files = [f for f in files if f["type"] != "Python"]
        
        assert len(python_files) > 0
        assert len(non_python_files) == 0
    
    def test_profile_with_exclude_patterns(self):
        """Test profile with exclude patterns."""
        config = {
            "include_patterns": ["*"],
            "exclude_patterns": ["*.pyc", "__pycache__", ".git*"]
        }
        
        profile_cmd = ProfileCommand(str(self.test_dir), config=config)
        profile = profile_cmd.generate_profile()
        
        # Should not include excluded files
        files = profile["files"]
        file_paths = [f["path"] for f in files]
        
        assert not any(".git" in path for path in file_paths)
        assert not any(".pyc" in path for path in file_paths)
    
    def test_profile_with_max_file_size(self):
        """Test profile with maximum file size."""
        # Create a large file
        large_file = self.test_dir / "large.py"
        large_file.write_text("x" * 10000)
        
        config = {
            "include_patterns": ["*"],
            "exclude_patterns": [],
            "max_file_size": 1000
        }
        
        profile_cmd = ProfileCommand(str(self.test_dir), config=config)
        profile = profile_cmd.generate_profile()
        
        # Large file should be excluded
        files = profile["files"]
        large_files = [f for f in files if f["path"].endswith("large.py")]
        assert len(large_files) == 0
    
    def test_profile_empty_directory(self):
        """Test profile with empty directory."""
        empty_dir = self.test_dir / "empty"
        empty_dir.mkdir()
        
        profile_cmd = ProfileCommand(str(empty_dir))
        profile = profile_cmd.generate_profile()
        
        assert profile["summary"]["total_files"] == 0
        assert profile["summary"]["total_directories"] == 1
        assert len(profile["files"]) == 0
    
    def test_profile_nonexistent_directory(self):
        """Test profile with nonexistent directory."""
        nonexistent_dir = self.test_dir / "nonexistent"
        
        with pytest.raises(FileNotFoundError):
            profile_cmd = ProfileCommand(str(nonexistent_dir))
            profile_cmd.generate_profile()
    
    def test_profile_save_to_file(self):
        """Test saving profile to file."""
        output_file = self.test_dir / "profile.json"
        
        self.profile_cmd.save_profile(str(output_file))
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            profile = json.load(f)
        
        assert isinstance(profile, dict)
        assert "metadata" in profile
    
    def test_profile_save_to_markdown(self):
        """Test saving profile to markdown file."""
        output_file = self.test_dir / "profile.md"
        
        self.profile_cmd.save_profile(str(output_file), format="markdown")
        
        assert output_file.exists()
        
        content = output_file.read_text()
        assert "# Project Profile" in content
        assert "## Summary" in content
    
    def test_profile_save_to_text(self):
        """Test saving profile to text file."""
        output_file = self.test_dir / "profile.txt"
        
        self.profile_cmd.save_profile(str(output_file), format="text")
        
        assert output_file.exists()
        
        content = output_file.read_text()
        assert "Project Profile" in content
        assert "Summary:" in content
    
    def test_profile_with_token_counting(self):
        """Test profile with token counting."""
        config = {
            "include_patterns": ["*.py", "*.md"],
            "exclude_patterns": [],
            "include_token_count": True
        }
        
        profile_cmd = ProfileCommand(str(self.test_dir), config=config)
        profile = profile_cmd.generate_profile()
        
        # Check if token counts are included
        files = profile["files"]
        for file_info in files:
            if file_info["type"] in ["Python", "Markdown"]:
                assert "tokens" in file_info
                assert isinstance(file_info["tokens"], int)
                assert file_info["tokens"] >= 0
    
    def test_profile_nested_directories(self):
        """Test profile with nested directory structure."""
        # Create deeply nested structure
        deep_dir = self.test_dir / "src" / "level1" / "level2" / "level3"
        deep_dir.mkdir(parents=True)
        (deep_dir / "deep.py").write_text('print("Deep file")')
        
        profile = self.profile_cmd.generate_profile()
        
        # Check structure includes nested directories
        structure = profile["structure"]
        assert "children" in structure
        
        # Navigate through structure
        src_child = next(c for c in structure["children"] if c["name"] == "src")
        level1_child = next(c for c in src_child["children"] if c["name"] == "level1")
        level2_child = next(c for c in level1_child["children"] if c["name"] == "level2")
        level3_child = next(c for c in level2_child["children"] if c["name"] == "level3")
        
        deep_file = next(c for c in level3_child["children"] if c["name"] == "deep.py")
        assert deep_file["type"] == "file"
    
    def test_profile_hidden_files(self):
        """Test profile with hidden files."""
        # Create hidden files
        (self.test_dir / ".hidden.py").write_text('print("hidden")')
        (self.test_dir / ".env.local").write_text("LOCAL_VAR=test")
        
        config = {
            "include_patterns": ["*", ".*"],
            "exclude_patterns": []
        }
        
        profile_cmd = ProfileCommand(str(self.test_dir), config=config)
        profile = profile_cmd.generate_profile()
        
        files = profile["files"]
        file_paths = [f["path"] for f in files]
        
        assert any(".hidden.py" in path for path in file_paths)
        assert any(".env.local" in path for path in file_paths)
    
    def test_profile_binary_files(self):
        """Test profile with binary files."""
        # Create binary file
        (self.test_dir / "data.bin").write_bytes(b"binary data")
        
        config = {
            "include_patterns": ["*"],
            "exclude_patterns": [],
            "include_binary": True
        }
        
        profile_cmd = ProfileCommand(str(self.test_dir), config=config)
        profile = profile_cmd.generate_profile()
        
        files = profile["files"]
        binary_files = [f for f in files if f["type"] == "Binary"]
        assert len(binary_files) > 0
    
    def test_profile_file_type_detection(self):
        """Test file type detection in profile."""
        # Create files with various extensions
        extensions = [".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".cfg"]
        
        for ext in extensions:
            (self.test_dir / f"test{ext}").write_text(f"Content for {ext}")
        
        profile = self.profile_cmd.generate_profile()
        
        languages = profile["languages"]
        expected_types = ["Python", "Markdown", "Text", "JSON", "YAML", "TOML", "INI"]
        
        for expected in expected_types:
            if expected in languages:
                assert languages[expected]["files"] > 0
    
    def test_profile_size_calculation(self):
        """Test size calculation in profile."""
        # Create files with known sizes
        small_file = self.test_dir / "small.txt"
        small_file.write_text("small")
        
        large_file = self.test_dir / "large.txt"
        large_file.write_text("large content here")
        
        profile = self.profile_cmd.generate_profile()
        
        files = profile["files"]
        small_info = next(f for f in files if f["path"].endswith("small.txt"))
        large_info = next(f for f in files if f["path"].endswith("large.txt"))
        
        assert small_info["size"] == 5
        assert large_info["size"] == 18
    
    def test_profile_line_counting(self):
        """Test line counting in profile."""
        # Create file with known line count
        lines_file = self.test_dir / "lines.py"
        lines_file.write_text('''line1
line2
line3
line4
line5''')
        
        profile = self.profile_cmd.generate_profile()
        
        files = profile["files"]
        lines_info = next(f for f in files if f["path"].endswith("lines.py"))
        
        assert lines_info["lines"] == 5
    
    def test_profile_consistency(self):
        """Test profile consistency across multiple runs."""
        profile1 = self.profile_cmd.generate_profile()
        profile2 = self.profile_cmd.generate_profile()
        
        # Key metrics should be consistent
        assert profile1["summary"]["total_files"] == profile2["summary"]["total_files"]
        assert profile1["summary"]["total_size"] == profile2["summary"]["total_size"]
        assert profile1["summary"]["total_directories"] == profile2["summary"]["total_directories"]
    
    def test_profile_with_unicode_content(self):
        """Test profile with Unicode content."""
        unicode_file = self.test_dir / "unicode.py"
        unicode_file.write_text('''# -*- coding: utf-8 -*-
print("Hello 世界! 🌍")
print("Привет мир!")
print("مرحبا بالعالم!")
''')
        
        profile = self.profile_cmd.generate_profile()
        
        files = profile["files"]
        unicode_info = next(f for f in files if f["path"].endswith("unicode.py"))
        
        assert unicode_info["type"] == "Python"
        assert unicode_info["size"] > 0
    
    def test_profile_performance(self):
        """Test profile generation performance."""
        import time
        
        # Create many small files
        for i in range(100):
            (self.test_dir / f"file_{i}.py").write_text(f'print("file {i}")')
        
        start_time = time.time()
        profile = self.profile_cmd.generate_profile()
        end_time = time.time()
        
        assert profile["summary"]["total_files"] >= 100
        # Should complete within reasonable time (adjust threshold as needed)
        assert (end_time - start_time) < 5.0