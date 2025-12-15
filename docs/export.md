# Export Documentation

This document provides comprehensive information about the export functionality in AI Context Manager.

## Overview

The export system allows you to export selected files from your codebase into various formats suitable for AI analysis. The system supports multiple output formats and provides extensive customization options.

## Core Components

### ContextExporter Class

The [`ContextExporter`](ai_context_manager/core/exporter.py:1) class is the main component responsible for exporting files. It works with profiles to determine which files to include and handles the actual export process.

#### Basic Usage

```python
from ai_context_manager.core.profile import Profile
from ai_context_manager.core.exporter import ContextExporter

# Create a profile
profile = Profile(
    name="my-project",
    include_patterns=["*.py", "*.md"],
    exclude_patterns=["__pycache__/*", "*.pyc"],
    max_file_size=102400,
    include_binary=False,
)

# Create exporter
exporter = ContextExporter(profile)

# Export to markdown
result = exporter.export_to_file(
    output_path="output.md",
    format="markdown",
    max_file_size=102400,
    include_binary=False,
)
```

## Export Formats

### Markdown Format

The markdown format creates a GitHub-flavored markdown file with the following structure:

```markdown
# AI Context Export

## Summary
- **Total Files**: 5
- **Total Size**: 15.2 KB
- **Total Tokens**: 2,847
- **Export Date**: 2024-01-15 10:30:00 UTC

## File Contents

### src/main.py
```python
def main():
    print("Hello, World!")
```

### README.md
```markdown
# My Project
This is a sample project.
```
```

### JSON Format

The JSON format provides a structured representation with metadata:

```json
{
  "metadata": {
    "export_date": "2024-01-15T10:30:00Z",
    "total_files": 5,
    "total_size": 15520,
    "total_tokens": 2847,
    "format": "json"
  },
  "files": [
    {
      "path": "src/main.py",
      "content": "def main():\n    print(\"Hello, World!\")",
      "size": 45,
      "lines": 3,
      "tokens": 12
    }
  ]
}
```

### XML Format

The XML format provides a hierarchical structure:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ai_context_export>
  <metadata>
    <export_date>2024-01-15T10:30:00Z</export_date>
    <total_files>5</total_files>
    <total_size>15520</total_size>
    <total_tokens>2847</total_tokens>
    <format>xml</format>
  </metadata>
  <files>
    <file>
      <path>src/main.py</path>
      <content><![CDATA[def main():
    print("Hello, World!")]]></content>
      <size>45</size>
      <lines>3</lines>
      <tokens>12</tokens>
    </file>
  </files>
</ai_context_export>
```

### YAML Format

The YAML format provides a human-readable structure:

```yaml
metadata:
  export_date: "2024-01-15T10:30:00Z"
  total_files: 5
  total_size: 15520
  total_tokens: 2847
  format: "yaml"

files:
  - path: "src/main.py"
    content: |
      def main():
          print("Hello, World!")
    size: 45
    lines: 3
    tokens: 12
```

## Configuration Options

### File Selection

The exporter uses the following criteria to select files:

1. **Include Patterns**: Glob patterns for files to include
2. **Exclude Patterns**: Glob patterns for files to exclude
3. **Max File Size**: Maximum file size in bytes
4. **Include Binary**: Whether to include binary files

### Override Options

You can override profile settings during export:

```python
# Override include patterns
result = exporter.export_to_file(
    output_path="output.md",
    format="markdown",
    include_patterns=["*.py"],  # Only Python files
    exclude_patterns=["*test*"],  # Exclude test files
    max_file_size=50000,  # 50KB limit
)
```

## Token Counting

The exporter automatically counts tokens for each file and provides totals. This helps ensure your export stays within AI model limits.

### Supported Models

- **gpt-4**: 8,192 tokens
- **gpt-4-turbo**: 128,000 tokens
- **gpt-3.5-turbo**: 4,096 tokens
- **claude-3-opus**: 200,000 tokens
- **claude-3-sonnet**: 200,000 tokens

## Error Handling

The exporter provides detailed error information:

```python
result = exporter.export_to_file(...)

if not result["success"]:
    print(f"Export failed: {result['message']}")
    if "errors" in result:
        for error in result["errors"]:
            print(f"  - {error}")
```

## Performance Considerations

### Large Projects

For large projects, consider:

1. **Use size limits**: Set appropriate `max_file_size`
2. **Exclude large directories**: Use exclude patterns for `node_modules`, `.git`, etc.
3. **Selective patterns**: Use specific include patterns instead of `*`
4. **Binary files**: Exclude binary files unless necessary

### Memory Usage

The exporter loads all selected files into memory. For very large projects:

1. **Split exports**: Create multiple profiles for different parts
2. **Use size limits**: Limit individual file sizes
3. **Exclude large files**: Use patterns to exclude large files

## CLI Usage

### Basic Export

```bash
# Export using profile
ai-context export output.md --profile my-project

# Export with format
ai-context export output.json --profile my-project --format json

# Export with size limit
ai-context export output.md --profile my-project --max-size 50000
```

### Advanced Options

```bash
# Export with custom patterns
ai-context export output.md \
  --profile my-project \
  --include "*.py" \
  --exclude "*test*" \
  --max-size 100000 \
  --model gpt-4

# Dry run to preview
ai-context export output.md --profile my-project --dry-run --verbose
```

## Examples

### Python Project Export

```python
from ai_context_manager.core.profile import Profile
from ai_context_manager.core.exporter import ContextExporter

# Create Python project profile
profile = Profile(
    name="python-project",
    include_patterns=[
        "*.py",
        "*.md",
        "*.txt",
        "*.json",
        "*.yaml",
        "*.yml",
        "*.cfg",
        "*.ini",
    ],
    exclude_patterns=[
        "__pycache__/*",
        "*.pyc",
        ".git/*",
        ".pytest_cache/*",
        "venv/*",
        ".venv/*",
        "build/*",
        "dist/*",
        "*.egg-info/*",
    ],
    max_file_size=102400,
    include_binary=False,
)

exporter = ContextExporter(profile)
result = exporter.export_to_file(
    "python-context.md",
    format="markdown",
    max_file_size=102400,
)
```

### Web Development Project

```python
profile = Profile(
    name="web-project",
    include_patterns=[
        "*.js",
        "*.ts",
        "*.jsx",
        "*.tsx",
        "*.html",
        "*.css",
        "*.scss",
        "*.sass",
        "*.json",
        "*.md",
        "*.txt",
    ],
    exclude_patterns=[
        "node_modules/*",
        "dist/*",
        "build/*",
        ".git/*",
        "*.min.js",
        "*.min.css",
    ],
    max_file_size=204800,
    include_binary=False,
)
```

## Troubleshooting

### Common Issues

1. **No files selected**: Check include/exclude patterns
2. **Files too large**: Adjust max_file_size or exclude large files
3. **Binary files included**: Set include_binary=False
4. **Token limit exceeded**: Use smaller files or split exports

### Debug Mode

Enable verbose output for debugging:

```bash
ai-context export output.md --profile my-project --verbose
```

This will show:
- Which files were considered
- Why files were excluded
- Token counts for each file
- Total statistics

## Generate Repomix Output

When running `ai-context-manager generate repomix`, the command now displays detailed information about each context definition file, including the resolved absolute path:

```
Processing: dashboard.yaml
  File Path: /home/marc/context-defs/dashboard.yaml
  Description: Dashboard
  Updated:     2025-12-14 by Marc Christenfeldt (Desktop)
  Files:       15
  Folders:     3

Processing: organization-stats.yaml
  File Path: /home/marc/context-defs/organization-stats.yaml
  Description: Organization stats
  Updated:     2025-12-14 by Marc Christenfeldt (Desktop)
  Files:       8
  Folders:     1
```

The file and folder counts represent the number of include entries in each context definition that resolve to existing files and directories on the filesystem. This helps you understand the scope of each context before generation.

### Verbose Mode Output

Passing `--verbose` adds an `Includes` block that lists every resolved path repomix will ingest. Files are printed in green, folders in cyan with a trailing `/` for clarity:

```
Processing: dashboard.yaml
  File Path: /abs/path/dashboard.yaml
  Description: Dashboard
  Files:       2
  Folders:     1
  Includes:
    • /abs/path/datasets/
    • /abs/path/datasets/schema.sql
    • /abs/path/README.md
```

Use verbose output while debugging selections to confirm that paths resolve as expected.