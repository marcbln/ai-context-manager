# AI Context Manager

Export codebases for AI analysis with intelligent file selection and format support.

## Features

- **Intelligent File Selection**: Automatically select relevant files based on patterns and size limits
- **Multiple Export Formats**: Support for Markdown, JSON, XML, and YAML
- **Profile Management**: Create and manage different export profiles for various project types
- **Token Counting**: Check token limits for different AI models
- **Flexible Filtering**: Include/exclude files with glob patterns
- **Binary File Handling**: Option to include or exclude binary files
- **Dry Run Mode**: Preview what would be exported without creating files

## Installation

```bash
pip install ai-context-manager
```

For YAML support:
```bash
pip install ai-context-manager[yaml]
```

## Quick Start

### 1. Create a Profile

```bash
# Create a basic profile
ai-context profile create my-project

# Create with specific patterns
ai-context profile create python-project --include "*.py" --exclude "__pycache__/*"
```

### 2. Export Files

```bash
# Export to markdown
ai-context export output.md --profile my-project

# Export to JSON with size limit
ai-context export output.json --profile my-project --format json --max-size 50000

# Dry run to see what would be exported
ai-context export output.md --profile my-project --dry-run --verbose
```

## Usage

### Profile Management

```bash
# List all profiles
ai-context profile list

# Show profile details
ai-context profile show my-project

# Edit profile interactively
ai-context profile edit my-project

# Delete profile
ai-context profile delete my-project
```

### Export Options

```bash
ai-context export [OPTIONS] OUTPUT

Options:
  --profile, -p TEXT      Profile name to use [required]
  --format, -f TEXT       Export format: markdown, json, xml, yaml [default: markdown]
  --max-size, -s INTEGER  Maximum file size in bytes [default: 102400]
  --include-binary, -b    Include binary files
  --model, -m TEXT        AI model for token limit checking [default: gpt-4]
  --dry-run               Show what would be exported without creating file
  --verbose, -v           Show detailed information
```

### Available Formats

- **markdown**: GitHub-flavored markdown with code blocks
- **json**: Structured JSON format with metadata
- **xml**: XML format with hierarchical structure
- **yaml**: YAML format with human-readable structure

### AI Model Limits

Check token limits for different AI models:

```bash
ai-context export models
```

## Configuration

Profiles are stored in `~/.ai-context-manager/profiles/` as JSON files. Each profile contains:

- **include_patterns**: List of glob patterns to include
- **exclude_patterns**: List of glob patterns to exclude
- **max_file_size**: Maximum file size in bytes
- **include_binary**: Whether to include binary files

## Examples

### Python Project

```bash
# Create profile for Python project
ai-context profile create python-app \
  --include "*.py" \
  --include "*.md" \
  --include "*.txt" \
  --include "*.json" \
  --include "*.yaml" \
  --include "*.yml" \
  --exclude "__pycache__/*" \
  --exclude "*.pyc" \
  --exclude ".git/*" \
  --exclude ".pytest_cache/*" \
  --exclude "venv/*" \
  --exclude ".venv/*"

# Export to markdown
ai-context export python-context.md --profile python-app
```

### Web Development Project

```bash
# Create profile for web project
ai-context profile create web-app \
  --include "*.js" \
  --include "*.ts" \
  --include "*.jsx" \
  --include "*.tsx" \
  --include "*.html" \
  --include "*.css" \
  --include "*.scss" \
  --include "*.json" \
  --include "*.md" \
  --exclude "node_modules/*" \
  --exclude "dist/*" \
  --exclude "build/*" \
  --exclude ".git/*"

# Export with token limit check for GPT-4
ai-context export web-context.md --profile web-app --model gpt-4
```

### Documentation Export

```bash
# Create profile for documentation
ai-context profile create docs \
  --include "*.md" \
  --include "*.rst" \
  --include "*.txt" \
  --exclude "node_modules/*" \
  --exclude ".git/*"

# Export to JSON for processing
ai-context export docs.json --profile docs --format json
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/ai-context-manager/ai-context-manager.git
cd ai-context-manager
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black ai_context_manager/
isort ai_context_manager/
```

## License

MIT License - see LICENSE file for details.