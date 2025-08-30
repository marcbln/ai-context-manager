"""Tests for file utilities."""
import os
import stat
from pathlib import Path

import pytest

from ai_context_manager.utils.file_utils import (
    collect_files,
    filter_files_by_patterns,
    get_file_size,
    get_file_info,
    is_binary_file,
    is_text_file,
    read_file_content,
    should_include_file,
)


class TestFileUtils:
    """Test suite for file utilities."""

    def test_get_file_size(self, sample_files: dict[str, Path]) -> None:
        """Test getting file sizes."""
        assert get_file_size(sample_files["main_py"]) > 0
        assert get_file_size(sample_files["large_file"]) == 2000
        assert get_file_size(sample_files["binary_file"]) == 4

    def test_get_file_size_nonexistent(self, temp_dir: Path) -> None:
        """Test getting size of non-existent file."""
        nonexistent = temp_dir / "nonexistent.txt"
        assert get_file_size(nonexistent) == 0

    def test_is_binary_file(self, sample_files: dict[str, Path]) -> None:
        """Test binary file detection."""
        assert not is_binary_file(sample_files["main_py"])
        assert not is_binary_file(sample_files["readme_md"])
        assert is_binary_file(sample_files["binary_file"])

    def test_is_binary_file_nonexistent(self, temp_dir: Path) -> None:
        """Test binary detection for non-existent file."""
        nonexistent = temp_dir / "nonexistent.bin"
        assert is_binary_file(nonexistent) is True  # Default to binary for safety

    def test_read_file_content_text(self, sample_files: dict[str, Path]) -> None:
        """Test reading text file content."""
        content = read_file_content(sample_files["main_py"])
        assert content == 'print("Hello, World!")\n'
        assert isinstance(content, str)

    def test_read_file_content_binary(self, sample_files: dict[str, Path]) -> None:
        """Test reading binary file content."""
        content = read_file_content(sample_files["binary_file"])
        assert content == ""  # Binary files should return empty string

    def test_read_file_content_nonexistent(self, temp_dir: Path) -> None:
        """Test reading non-existent file."""
        nonexistent = temp_dir / "nonexistent.txt"
        content = read_file_content(nonexistent)
        assert content == ""

    def test_read_file_content_empty(self, temp_dir: Path) -> None:
        """Test reading empty file."""
        empty_file = temp_dir / "empty.txt"
        empty_file.touch()
        content = read_file_content(empty_file)
        assert content == ""

    def test_should_include_file_basic(self, sample_files: dict[str, Path]) -> None:
        """Test basic file inclusion logic."""
        # Include Python files
        assert should_include_file(
            sample_files["main_py"],
            include_patterns=["*.py"],
            exclude_patterns=[],
        )

        # Exclude by pattern
        assert not should_include_file(
            sample_files["main_py"],
            include_patterns=["*.py"],
            exclude_patterns=["main.py"],
        )

        # Include all files when no patterns specified
        assert should_include_file(
            sample_files["large_file"],
            include_patterns=None,
            exclude_patterns=[],
        )

        # Exclude by pattern
        assert not should_include_file(
            sample_files["main_py"],
            include_patterns=None,
            exclude_patterns=["*.py"],
        )

    def test_should_include_file_nonexistent(self, temp_dir: Path) -> None:
        """Test inclusion logic for non-existent file."""
        nonexistent = temp_dir / "nonexistent.txt"
        assert not should_include_file(
            nonexistent,
            include_patterns=["*.txt"],
            exclude_patterns=[],
        )

    def test_filter_files_by_patterns(self, sample_files: dict[str, Path]) -> None:
        """Test filtering files by patterns."""
        all_files = list(sample_files.values())
        
        # Include only Python files
        python_files = filter_files_by_patterns(
            all_files,
            include_patterns=["*.py"],
            exclude_patterns=[],
        )
        assert len(python_files) >= 2  # main.py and utils.py
        assert all(f.suffix == ".py" for f in python_files)

        # Exclude specific files
        filtered = filter_files_by_patterns(
            all_files,
            include_patterns=["*"],
            exclude_patterns=["main.py", "utils.py"],
        )
        assert sample_files["main_py"] not in filtered
        assert sample_files["utils_py"] not in filtered

        # Complex patterns
        markdown_files = filter_files_by_patterns(
            all_files,
            include_patterns=["*.md"],
            exclude_patterns=[],
        )
        assert sample_files["readme_md"] in markdown_files

    def test_filter_files_by_patterns_empty(self) -> None:
        """Test filtering empty file list."""
        result = filter_files_by_patterns(
            [],
            include_patterns=["*"],
            exclude_patterns=[],
        )
        assert result == []

    def test_collect_files_basic(self, temp_dir: Path) -> None:
        """Test basic file collection."""
        # Create test files
        (temp_dir / "file1.txt").write_text("test1")
        (temp_dir / "file2.py").write_text("test2")
        
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("test3")
        
        files = collect_files(temp_dir)
        
        assert len(files) >= 3
        assert any(f.name == "file1.txt" for f in files)
        assert any(f.name == "file2.py" for f in files)
        assert any(f.name == "file3.txt" for f in files)

    def test_collect_files_empty_directory(self, temp_dir: Path) -> None:
        """Test collecting files from empty directory."""
        files = collect_files(temp_dir)
        assert files == []

    def test_collect_files_nonexistent_directory(self, temp_dir: Path) -> None:
        """Test collecting files from non-existent directory."""
        nonexistent = temp_dir / "nonexistent"
        files = collect_files(nonexistent)
        assert files == []

    def test_collect_files_with_symlinks(self, temp_dir: Path) -> None:
        """Test collecting files with symbolic links."""
        # Create a file and symlink
        target_file = temp_dir / "target.txt"
        target_file.write_text("target content")
        
        symlink_file = temp_dir / "link.txt"
        try:
            symlink_file.symlink_to(target_file)
        except OSError:
            pytest.skip("Symbolic links not supported on this system")
        
        files = collect_files(temp_dir)
        
        # Should include both target and symlink
        assert target_file in files
        assert symlink_file in files

    def test_should_include_file_permission_denied(self, temp_dir: Path) -> None:
        """Test handling permission denied scenarios."""
        restricted_file = temp_dir / "restricted.txt"
        restricted_file.write_text("restricted content")
        
        # Make file unreadable (skip on Windows)
        if os.name != "nt":
            try:
                os.chmod(restricted_file, 0o000)
                assert not should_include_file(
                    restricted_file,
                    include_patterns=["*.txt"],
                    exclude_patterns=[],
                )
            finally:
                # Restore permissions for cleanup
                os.chmod(restricted_file, 0o644)

    def test_filter_files_by_patterns_case_sensitivity(self, temp_dir: Path) -> None:
        """Test case sensitivity in pattern matching."""
        file1 = temp_dir / "test.py"
        file1.write_text("test")
        file2 = temp_dir / "TEST.PY"
        file2.write_text("TEST")
        
        files = [file1, file2]
        
        # Case-sensitive patterns
        filtered = filter_files_by_patterns(
            files,
            include_patterns=["*.py"],
            exclude_patterns=[],
        )
        assert file1 in filtered
        assert file2 not in filtered  # Should not match due to case

    def test_complex_pattern_matching(self, temp_dir: Path) -> None:
        """Test complex pattern matching scenarios."""
        # Create nested structure
        src_dir = temp_dir / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("main")
        
        tests_dir = temp_dir / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_main.py").write_text("test")
        
        # Test recursive patterns
        files = collect_files(temp_dir)
        py_files = filter_files_by_patterns(
            files,
            include_patterns=["**/*.py"],
            exclude_patterns=[],
        )
        
        assert len(py_files) >= 2
        assert any("main.py" in str(f) for f in py_files)
        assert any("test_main.py" in str(f) for f in py_files)

    def test_is_text_file(self, sample_files: dict[str, Path]) -> None:
        """Test text file detection."""
        assert is_text_file(sample_files["main_py"])
        assert is_text_file(sample_files["readme_md"])
        assert not is_text_file(sample_files["binary_file"])

    def test_is_text_file_nonexistent(self, temp_dir: Path) -> None:
        """Test text detection for non-existent file."""
        nonexistent = temp_dir / "nonexistent.txt"
        assert is_text_file(nonexistent) is False

    def test_get_file_info(self, sample_files: dict[str, Path]) -> None:
        """Test getting comprehensive file information."""
        info = get_file_info(sample_files["main_py"])
        
        assert info["path"] == str(sample_files["main_py"])
        assert info["size"] > 0
        assert info["lines"] == 1  # Single line file
        assert info["is_text"] is True
        assert info["exists"] is True
        assert info["modified"] > 0
        assert info["created"] > 0

    def test_get_file_info_nonexistent(self, temp_dir: Path) -> None:
        """Test getting file info for non-existent file."""
        nonexistent = temp_dir / "nonexistent.txt"
        info = get_file_info(nonexistent)
        
        assert info["path"] == str(nonexistent)
        assert info["size"] == 0
        assert info["lines"] == 0
        assert info["is_text"] is False
        assert info["exists"] is False
        assert info["modified"] == 0
        assert info["created"] == 0

    def test_get_file_info_binary(self, sample_files: dict[str, Path]) -> None:
        """Test getting file info for binary file."""
        info = get_file_info(sample_files["binary_file"])
        
        assert info["path"] == str(sample_files["binary_file"])
        assert info["size"] == 4
        assert info["lines"] == 0  # Binary files have 0 lines
        assert info["is_text"] is False
        assert info["exists"] is True