#!/usr/bin/env python3
"""Test script for the import command."""
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "ai_context_manager")))

from ai_context_manager.config import get_config_dir
from ai_context_manager.commands.import_cmd import app

def setup_test_environment():
    """Set up a test environment with a temporary config directory."""
    # Create a temporary directory for config
    temp_dir = tempfile.mkdtemp()
    os.environ["AICONTEXT_CONFIG_DIR"] = temp_dir

    # Create the context.yaml file
    config_dir = Path(temp_dir)
    context_file = config_dir / "context.yaml"

    # Create a sample directory structure
    test_data_dir = config_dir / "test_data"
    test_data_dir.mkdir()

    # Create some test files
    for i in range(3):
        file_path = test_data_dir / f"file{i}.txt"
        with open(file_path, "w") as f:
            f.write(f"Test content for file {i}")

    # Create a subdirectory with more files
    subdir = test_data_dir / "subdir"
    subdir.mkdir()
    for i in range(2):
        file_path = subdir / f"subfile{i}.txt"
        with open(file_path, "w") as f:
            f.write(f"Test content for subfile {i}")

    return temp_dir, test_data_dir

def cleanup(temp_dir):
    """Clean up the test environment."""
    shutil.rmtree(temp_dir)

def test_import_command():
    """Test the import command functionality."""
    temp_dir, test_data_dir = setup_test_environment()
    try:
        # Run the import command
        sys.argv = ["import", "directory", str(test_data_dir), "--recursive"]
        app()

        # Check if files were added to context
        config_dir = Path(os.environ["AICONTEXT_CONFIG_DIR"])
        context_file = config_dir / "context.yaml"

        if not context_file.exists():
            print("Error: context.yaml was not created")
            return False

        # Read the context file
        import yaml
        with open(context_file, "r") as f:
            context = yaml.safe_load(f) or {}

        files = context.get("files", [])
        if not files:
            print("Error: No files were added to context")
            return False

        # Verify all files were added
        expected_files = [
            "test_data/file0.txt",
            "test_data/file1.txt",
            "test_data/file2.txt",
            "test_data/subdir/subfile0.txt",
            "test_data/subdir/subfile1.txt"
        ]

        # Normalize paths for comparison
        files = [str(Path(f).relative_to(config_dir)) for f in files]

        if sorted(files) != sorted(expected_files):
            print(f"Error: Expected files {expected_files}, but got {files}")
            return False

        print("Success: All files were correctly added to context")
        return True

    finally:
        cleanup(temp_dir)

if __name__ == "__main__":
    success = test_import_command()
    sys.exit(0 if success else 1)