"""Configuration for AI Context Manager."""

from pathlib import Path

# Default configuration
DEFAULT_CONFIG_DIR = Path.home() / ".ai-context-manager"
DEFAULT_PROFILE_PATH = DEFAULT_CONFIG_DIR / "profile.json"
DEFAULT_OUTPUT_PATH = Path.cwd() / "context.md"

# File size limits
DEFAULT_MAX_FILE_SIZE = 102400  # 100KB
MAX_TOTAL_SIZE = 10485760  # 10MB

# Language extensions mapping
LANGUAGE_EXTENSIONS = {
    "python": [".py", ".pyx", ".pxd", ".pyi"],
    "javascript": [".js", ".jsx", ".mjs", ".cjs"],
    "typescript": [".ts", ".tsx", ".mts", ".cts"],
    "java": [".java"],
    "c": [".c", ".h"],
    "cpp": [".cpp", ".cxx", ".cc", ".hpp", ".hxx", ".hh"],
    "csharp": [".cs"],
    "go": [".go"],
    "rust": [".rs"],
    "ruby": [".rb"],
    "php": [".php"],
    "html": [".html", ".htm"],
    "css": [".css", ".scss", ".sass", ".less"],
    "json": [".json"],
    "yaml": [".yml", ".yaml"],
    "xml": [".xml"],
    "markdown": [".md", ".markdown"],
    "sql": [".sql"],
    "shell": [".sh", ".bash", ".zsh"],
    "dockerfile": ["Dockerfile", ".dockerfile"],
    "makefile": ["Makefile", "makefile"],
}

# Default include/exclude patterns
DEFAULT_INCLUDE_PATTERNS = ["*"]
DEFAULT_EXCLUDE_PATTERNS = [
    ".*",  # Hidden files
    "__pycache__/*",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".git/*",
    ".svn/*",
    ".hg/*",
    "node_modules/*",
    ".venv/*",
    "venv/*",
    "*.egg-info/*",
    "dist/*",
    "build/*",
    "*.so",
    "*.dylib",
    "*.dll",
    "*.exe",
    "*.bin",
    "*.dat",
    "*.db",
    "*.sqlite",
    "*.log",
    "*.tmp",
    "*.temp",
    "*.cache",
    "*.lock",
    "*.pid",
    "*.sock",
]

# Output formats
SUPPORTED_OUTPUT_FORMATS = ["markdown", "json", "xml"]

# Token counting configuration
TOKEN_ESTIMATION_RATIO = 0.75  # Rough estimate: 1 token ≈ 0.75 words
CHARS_PER_TOKEN = 4  # Rough estimate: 1 token ≈ 4 characters

# CLI configuration
CLI_CONTEXT_SETTINGS = {
    "help_option_names": ["-h", "--help"],
    "max_content_width": 120,
}