"""Pytest configuration and fixtures."""

import tempfile
from pathlib import Path
import pytest

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

@pytest.fixture
def sample_files(temp_dir):
    """Create a dictionary of sample files for testing."""
    files = {}
    
    # Python file
    main_py = temp_dir / "main.py"
    main_py.write_text('print("Hello, World!")\n')
    files["main_py"] = main_py
    
    # Markdown file
    readme_md = temp_dir / "README.md"
    readme_md.write_text("# Test Project")
    files["readme_md"] = readme_md
    
    # Binary file
    binary_file = temp_dir / "test.bin"
    binary_file.write_bytes(b"\x00\x01\x02\x03")
    files["binary_file"] = binary_file
    
    # Large file
    large_file = temp_dir / "large.txt"
    large_file.write_text("x" * 2000)
    files["large_file"] = large_file
    
    # Utilities file
    utils_py = temp_dir / "utils.py"
    utils_py.write_text("def helper(): pass")
    files["utils_py"] = utils_py
    
    return files
