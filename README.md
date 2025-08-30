# AI Context Manager

A command-line tool for managing and exporting file selections as AI context.

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd ai-context-manager

# Install using uv
uv pip install -e ".[dev]"
```

## Usage

### Initialize
```bash
aicontext init
```

### Add files to context
```bash
# Add specific files
aicontext add files file1.py file2.py

# Add directories recursively
aicontext add files src/ --recursive

# Add with pattern matching
aicontext add files src/ --recursive --pattern "*.py"

# Exclude certain files
aicontext add files src/ --recursive --exclude "test_*"
```

### List context files
```bash
aicontext list
```

### Remove files from context
```bash
aicontext remove file1.py
aicontext remove --all
```

### Export context
```bash
# Export to markdown
aicontext export markdown output.md

# Export to JSON
aicontext export json output.json

# Export to XML
aicontext export xml output.xml

# Export with profile
aicontext export markdown output.md --profile python-dev
aicontext export json output.json --profile web-dev
```

### Manage profiles
```bash
# Create a profile
aicontext profile create python-dev --description "Python development profile"

# Configure profile settings
aicontext profile set python-dev file_extensions py,md,txt
aicontext profile set python-dev max_file_size 100000
aicontext profile set python-dev include_metadata false

# List profiles
aicontext profile list

# Show profile details
aicontext profile show python-dev

# Delete a profile
aicontext profile delete python-dev
```

### Profile Configuration

Profiles allow you to filter and customize exports based on specific needs:

- **file_extensions**: Comma-separated list of file extensions to include
- **max_file_size**: Maximum file size in bytes to include
- **include_metadata**: Whether to include metadata in exports (default: true)

Example profile configuration:
```bash
# Create a web development profile
aicontext profile create web-dev --description "Web development files"
aicontext profile set web-dev file_extensions js,ts,html,css,json,md
aicontext profile set web-dev max_file_size 50000
aicontext profile set web-dev include_metadata true
```

## Configuration

Configuration is stored in `~/.ai-context-manager/`:
- `context.yaml`: Contains the list of files in context
- `profiles/`: Directory for export profiles

## Development

```bash
# Install development dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Format code
ruff format
ruff check --fix
```

## License

MIT License