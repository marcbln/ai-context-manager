# Selector Class Documentation

The `Selector` class is a core component of the AI Context Manager that handles file selection based on profile configurations. It provides intelligent filtering, validation, and analysis capabilities for selecting files to include in AI context.

## Overview

The `Selector` class integrates with the `Profile` system to:
- Collect files from configured paths
- Apply exclude patterns (gitignore-style)
- Filter by file size, type, and patterns
- Provide detailed file information
- Generate summary statistics
- Validate profile configurations

## Usage

### Basic Usage

```python
from ai_context_manager.core.profile import Profile, PathEntry
from ai_context_manager.core.selector import Selector
from datetime import datetime
from pathlib import Path

# Create a profile
profile = Profile(
    name="my_project",
    created=datetime.now(),
    modified=datetime.now(),
    base_path=Path("/path/to/project"),
    paths=[
        PathEntry(path=Path("/path/to/project/src"), is_directory=True, recursive=True),
        PathEntry(path=Path("/path/to/project/docs"), is_directory=True, recursive=False),
    ],
    exclude_patterns=["*.pyc", "__pycache__/*", "node_modules/*"],
    include_metadata=True
)

# Create selector
selector = Selector(profile)

# Select files
files = selector.select_files(
    max_file_size=102400,  # 100KB
    include_binary=False,
    include_patterns=["*.py", "*.js", "*.md"]
)

# Get summary
summary = selector.get_summary(files)
print(f"Selected {summary['total_files']} files")
```

### Advanced Filtering

```python
# Get all files without filtering
all_files = selector.get_all_files()

# Apply custom filters
filtered = selector.filter_files(
    all_files,
    max_file_size=50000,  # 50KB
    include_binary=True,
    include_patterns=["*.py"],
    exclude_patterns=["test_*"]
)

# Filter by language
python_files = selector.get_files_by_language(filtered, ["python", "javascript"])
```

### File Information

```python
# Get detailed file information
for file_path in files:
    info = selector.get_file_info(file_path)
    print(f"{info['path']}: {info['lines']} lines, {info['size_human']}")
```

### Profile Validation

```python
# Validate profile configuration
issues = selector.validate_profile()
if issues:
    print("Profile issues:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("Profile is valid")
```

## API Reference

### Constructor

```python
Selector(profile: Profile)
```

Creates a new Selector instance with the given profile.

### Methods

#### `get_all_files() -> List[Path]`
Collects all files from the configured paths without any filtering.

#### `filter_files(files: List[Path], **kwargs) -> List[Path]`
Filters a list of files based on various criteria.

**Parameters:**
- `max_file_size`: Maximum file size in bytes
- `include_binary`: Whether to include binary files (default: False)
- `include_patterns`: List of glob patterns to include
- `exclude_patterns`: List of glob patterns to exclude

#### `select_files(**kwargs) -> List[Path]`
Main method that combines collection and filtering.

**Parameters:** Same as `filter_files()`

#### `get_file_info(file_path: Path) -> Dict[str, Any]`
Returns detailed information about a file.

**Returns:**
```python
{
    "path": str,
    "name": str,
    "extension": str,
    "size": int,
    "size_human": str,
    "lines": int,
    "is_text": bool,
    "language": str,
    "modified": datetime
}
```

#### `get_files_by_language(files: List[Path], languages: List[str]) -> List[Path]`
Filters files by programming language.

#### `get_summary(files: List[Path]) -> Dict[str, Any]`
Generates summary statistics for a list of files.

**Returns:**
```python
{
    "total_files": int,
    "total_size": int,
    "total_size_human": str,
    "total_lines": int,
    "languages": Dict[str, int],
    "largest_file": Dict,
    "smallest_file": Dict
}
```

#### `validate_profile() -> List[str]`
Validates the profile configuration and returns a list of issues.

## Configuration Examples

### Python Project
```python
profile = Profile(
    name="python_project",
    base_path=Path("/path/to/project"),
    paths=[
        PathEntry(path=Path("/path/to/project/src"), is_directory=True, recursive=True),
        PathEntry(path=Path("/path/to/project/tests"), is_directory=True, recursive=True),
    ],
    exclude_patterns=[
        "*.pyc",
        "__pycache__/*",
        "*.egg-info/*",
        ".pytest_cache/*",
        "venv/*",
        ".venv/*"
    ]
)
```

### Web Project
```python
profile = Profile(
    name="web_project",
    base_path=Path("/path/to/project"),
    paths=[
        PathEntry(path=Path("/path/to/project/src"), is_directory=True, recursive=True),
        PathEntry(path=Path("/path/to/project/public"), is_directory=True, recursive=True),
    ],
    exclude_patterns=[
        "node_modules/*",
        "dist/*",
        "build/*",
        "*.log",
        ".next/*"
    ]
)
```

### Documentation Project
```python
profile = Profile(
    name="docs_project",
    base_path=Path("/path/to/project"),
    paths=[
        PathEntry(path=Path("/path/to/project/docs"), is_directory=True, recursive=True),
        PathEntry(path=Path("/path/to/project/README.md"), is_directory=False, recursive=False),
    ],
    exclude_patterns=[
        "_build/*",
        ".doctrees/*"
    ]
)
```

## Error Handling

The Selector class includes comprehensive error handling:

- **Non-existent paths**: Gracefully handled with validation
- **Permission errors**: Files without read permissions are skipped
- **Binary file detection**: Automatic detection and filtering
- **Pattern matching**: Robust gitignore-style pattern support

## Performance Considerations

- **Lazy evaluation**: Files are collected and filtered on-demand
- **Efficient filtering**: Uses pathspec for fast pattern matching
- **Memory efficient**: Processes files in chunks rather than loading all content
- **Caching**: File information is cached to avoid repeated disk access

## Integration

The Selector class is designed to work seamlessly with:

- **Profile management**: Full integration with the Profile system
- **Export functionality**: Provides files ready for context export
- **CLI tools**: Used by command-line interface commands
- **Configuration**: Respects all profile settings and patterns

## Testing

Comprehensive test suite available in `tests/test_selector.py` covering:
- Basic functionality
- Edge cases
- Error conditions
- Performance scenarios
- Integration with profiles