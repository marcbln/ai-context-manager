"""Tests for the Selector class."""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from ai_context_manager.core.profile import Profile, PathEntry
from ai_context_manager.core.selector import Selector


class TestSelector:
    """Test cases for Selector class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory with test files."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create directory structure
        (temp_dir / "src").mkdir()
        (temp_dir / "tests").mkdir()
        (temp_dir / "docs").mkdir()
        (temp_dir / "build").mkdir()
        
        # Create test files
        (temp_dir / "src" / "main.py").write_text("print('hello world')")
        (temp_dir / "src" / "utils.py").write_text("def helper(): pass")
        (temp_dir / "tests" / "test_main.py").write_text("def test_main(): pass")
        (temp_dir / "docs" / "README.md").write_text("# Project")
        (temp_dir / "build" / "output.bin").write_bytes(b"\x00\x01\x02\x03")
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def simple_profile(self, temp_dir):
        """Create a simple profile for testing."""
        return Profile(
            name="test_profile",
            created=datetime.now(),
            modified=datetime.now(),
            base_path=temp_dir,
            paths=[
                PathEntry(path=temp_dir / "src", is_directory=True, recursive=True),
                PathEntry(path=temp_dir / "docs", is_directory=True, recursive=False),
            ],
            exclude_patterns=["*.pyc", "__pycache__/*", "build/*"],
            include_metadata=True
        )
    
    def test_init(self, simple_profile):
        """Test Selector initialization."""
        selector = Selector(simple_profile)
        assert selector.profile == simple_profile
        assert selector._spec is not None
    
    def test_init_no_exclude_patterns(self, temp_dir):
        """Test Selector initialization with no exclude patterns."""
        profile = Profile(
            name="test_profile",
            created=datetime.now(),
            modified=datetime.now(),
            base_path=temp_dir,
            paths=[PathEntry(path=temp_dir, is_directory=True, recursive=True)],
            exclude_patterns=[],
            include_metadata=True
        )
        selector = Selector(profile)
        assert selector._spec is None
    
    def test_get_all_files(self, simple_profile, temp_dir):
        """Test collecting all files from profile paths."""
        selector = Selector(simple_profile)
        files = selector.get_all_files()
        
        expected_files = {
            temp_dir / "src" / "main.py",
            temp_dir / "src" / "utils.py",
            temp_dir / "docs" / "README.md"
        }
        
        assert len(files) == 3
        assert set(files) == expected_files
    
    def test_filter_files_exclude_patterns(self, simple_profile, temp_dir):
        """Test filtering files with exclude patterns."""
        selector = Selector(simple_profile)
        
        # Add a file that should be excluded
        (temp_dir / "src" / "temp.pyc").write_text("compiled")
        
        all_files = selector.get_all_files()
        filtered = selector.filter_files(all_files)
        
        # Should exclude the .pyc file
        assert len(filtered) == 3
        assert temp_dir / "src" / "temp.pyc" not in filtered
    
    def test_filter_files_max_size(self, simple_profile, temp_dir):
        """Test filtering files by max size."""
        selector = Selector(simple_profile)
        
        # Create a large file
        large_file = temp_dir / "src" / "large.py"
        large_file.write_text("x" * 200000)  # 200KB
        
        all_files = selector.get_all_files()
        filtered = selector.filter_files(all_files, max_file_size=102400)  # 100KB
        
        # Should exclude the large file
        assert large_file not in filtered
        assert len(filtered) == 3
    
    def test_filter_files_include_binary(self, simple_profile, temp_dir):
        """Test filtering files with binary inclusion."""
        selector = Selector(simple_profile)
        
        # Add binary file to one of the included directories
        binary_file = temp_dir / "src" / "data.bin"
        binary_file.write_bytes(b"\x00\x01\x02\x03")
        
        all_files = selector.get_all_files()
        
        # Without binary inclusion
        filtered_no_binary = selector.filter_files(all_files, include_binary=False)
        assert binary_file not in filtered_no_binary
        
        # With binary inclusion
        filtered_with_binary = selector.filter_files(all_files, include_binary=True)
        assert binary_file in filtered_with_binary
    
    def test_filter_files_include_patterns(self, simple_profile, temp_dir):
        """Test filtering files with include patterns."""
        selector = Selector(simple_profile)
        
        all_files = selector.get_all_files()
        filtered = selector.filter_files(all_files, include_patterns=["*.py"])
        
        # Should only include Python files
        assert len(filtered) == 2
        assert all(f.suffix == ".py" for f in filtered)
    
    def test_select_files(self, simple_profile):
        """Test the main select_files method."""
        selector = Selector(simple_profile)
        files = selector.select_files()
        
        assert len(files) == 3
        assert all(f.exists() for f in files)
    
    def test_get_file_info(self, simple_profile, temp_dir):
        """Test getting file information."""
        selector = Selector(simple_profile)
        file_path = temp_dir / "src" / "main.py"
        
        info = selector.get_file_info(file_path)
        
        assert info["path"] == str(file_path)
        assert info["name"] == "main.py"
        assert info["extension"] == ".py"
        assert info["lines"] == 1
        assert info["is_text"] is True
    
    def test_get_files_by_language(self, simple_profile):
        """Test filtering files by language."""
        selector = Selector(simple_profile)
        all_files = selector.get_all_files()
        
        python_files = selector.get_files_by_language(all_files, ["python"])
        assert len(python_files) == 2
        
        markdown_files = selector.get_files_by_language(all_files, ["markdown"])
        assert len(markdown_files) == 1
    
    def test_get_summary(self, simple_profile):
        """Test getting summary statistics."""
        selector = Selector(simple_profile)
        files = selector.select_files()
        
        summary = selector.get_summary(files)
        
        assert summary["total_files"] == 3
        assert summary["total_size"] > 0
        assert "python" in summary["languages"]
        assert "markdown" in summary["languages"]
        assert summary["largest_file"] is not None
        assert summary["smallest_file"] is not None
    
    def test_validate_profile_valid(self, simple_profile):
        """Test profile validation with valid profile."""
        selector = Selector(simple_profile)
        issues = selector.validate_profile()
        
        assert len(issues) == 0
    
    def test_validate_profile_invalid_paths(self, temp_dir):
        """Test profile validation with invalid paths."""
        profile = Profile(
            name="test_profile",
            created=datetime.now(),
            modified=datetime.now(),
            base_path=temp_dir,
            paths=[
                PathEntry(path=temp_dir / "nonexistent", is_directory=True, recursive=True),
                PathEntry(path=temp_dir / "also_nonexistent", is_directory=False, recursive=False),
            ],
            exclude_patterns=[],
            include_metadata=True
        )
        
        selector = Selector(profile)
        issues = selector.validate_profile()
        
        assert len(issues) == 2
        assert any("nonexistent" in issue for issue in issues)
    
    def test_validate_profile_duplicate_paths(self, temp_dir):
        """Test profile validation with duplicate paths."""
        profile = Profile(
            name="test_profile",
            created=datetime.now(),
            modified=datetime.now(),
            base_path=temp_dir,
            paths=[
                PathEntry(path=temp_dir / "src", is_directory=True, recursive=True),
                PathEntry(path=temp_dir / "src", is_directory=True, recursive=True),  # Duplicate
            ],
            exclude_patterns=[],
            include_metadata=True
        )
        
        selector = Selector(profile)
        issues = selector.validate_profile()
        
        assert len(issues) == 1
        assert "Duplicate path" in issues[0]
    
    def test_nonexistent_path_entry(self, temp_dir):
        """Test handling of non-existent path entries."""
        profile = Profile(
            name="test_profile",
            created=datetime.now(),
            modified=datetime.now(),
            base_path=temp_dir,
            paths=[
                PathEntry(path=temp_dir / "nonexistent", is_directory=True, recursive=True),
            ],
            exclude_patterns=[],
            include_metadata=True
        )
        
        selector = Selector(profile)
        files = selector.get_all_files()
        
        assert len(files) == 0
    
    def test_empty_profile(self, temp_dir):
        """Test handling of empty profile."""
        profile = Profile(
            name="test_profile",
            created=datetime.now(),
            modified=datetime.now(),
            base_path=temp_dir,
            paths=[],
            exclude_patterns=[],
            include_metadata=True
        )
        
        selector = Selector(profile)
        files = selector.get_all_files()
        
        assert len(files) == 0
    
    def test_single_file_entry(self, temp_dir):
        """Test handling of single file path entries."""
        profile = Profile(
            name="test_profile",
            created=datetime.now(),
            modified=datetime.now(),
            base_path=temp_dir,
            paths=[
                PathEntry(path=temp_dir / "src" / "main.py", is_directory=False, recursive=False),
            ],
            exclude_patterns=[],
            include_metadata=True
        )
        
        selector = Selector(profile)
        files = selector.get_all_files()
        
        assert len(files) == 1
        assert files[0] == temp_dir / "src" / "main.py"
    
    def test_non_recursive_directory(self, temp_dir):
        """Test non-recursive directory handling."""
        # Create nested structure
        (temp_dir / "src" / "nested").mkdir()
        (temp_dir / "src" / "nested" / "deep.py").write_text("deep")
        
        profile = Profile(
            name="test_profile",
            created=datetime.now(),
            modified=datetime.now(),
            base_path=temp_dir,
            paths=[
                PathEntry(path=temp_dir / "src", is_directory=True, recursive=False),
            ],
            exclude_patterns=[],
            include_metadata=True
        )
        
        selector = Selector(profile)
        files = selector.get_all_files()
        
        # Should only get files directly in src/, not in nested/
        assert len(files) == 2  # main.py and utils.py
        assert temp_dir / "src" / "nested" / "deep.py" not in files