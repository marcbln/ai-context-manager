#!/usr/bin/env python3
"""Example demonstrating the Selector class usage."""

import sys
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_context_manager.core.profile import Profile, PathEntry
from ai_context_manager.core.selector import Selector


def main():
    """Demonstrate Selector class functionality."""
    
    # Create a sample profile
    base_path = Path(__file__).parent.parent
    
    profile = Profile(
        name="example_profile",
        created=datetime.now(),
        modified=datetime.now(),
        base_path=base_path,
        paths=[
            PathEntry(path=base_path / "ai_context_manager", is_directory=True, recursive=True),
            PathEntry(path=base_path / "tests", is_directory=True, recursive=True),
        ],
        exclude_patterns=[
            "*.pyc",
            "__pycache__/*",
            "*.egg-info/*",
            ".git/*",
            ".pytest_cache/*",
            "htmlcov/*",
            ".coverage",
            "*.log"
        ],
        include_metadata=True
    )
    
    # Create selector
    selector = Selector(profile)
    
    # Validate profile
    issues = selector.validate_profile()
    if issues:
        print("Profile validation issues:")
        for issue in issues:
            print(f"  - {issue}")
        return
    
    # Select files
    print("Selecting files...")
    files = selector.select_files(
        max_file_size=102400,  # 100KB
        include_binary=False,
        include_patterns=["*.py", "*.md", "*.txt", "*.json", "*.yaml", "*.yml"]
    )
    
    # Get summary
    summary = selector.get_summary(files)
    
    # Display results
    print(f"\nSelected {summary['total_files']} files")
    print(f"Total size: {summary['total_size_human']}")
    print(f"Total lines: {summary['total_lines']}")
    
    print("\nLanguages found:")
    for lang, count in summary['languages'].items():
        print(f"  {lang}: {count} files")
    
    print("\nLargest file:")
    if summary['largest_file']:
        print(f"  {summary['largest_file']['path']} ({summary['largest_file']['size_human']})")
    
    print("\nSmallest file:")
    if summary['smallest_file']:
        print(f"  {summary['smallest_file']['path']} ({summary['smallest_file']['size_human']})")
    
    # Show first few files
    print("\nFirst 10 files:")
    for file_path in files[:10]:
        info = selector.get_file_info(file_path)
        print(f"  {info['path']} ({info['size_human']}, {info['lines']} lines)")


if __name__ == "__main__":
    main()