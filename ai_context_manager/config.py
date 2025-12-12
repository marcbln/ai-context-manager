"""Configuration management for AI Context Manager."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union
from functools import lru_cache


class Config:
    """Configuration management class for AI Context Manager.
    
    This class provides a unified interface for managing configuration settings
    with support for nested keys, file persistence, and various data types.
    
    Features:
    - JSON-based configuration storage
    - Nested key access with dot notation
    - Automatic file creation and backup
    - Dictionary-like interface (__getitem__, __setitem__, etc.)
    - Type-safe getters with defaults
    - Unicode support
    
    Example:
        >>> config = Config("config.json")
        >>> config.set("project.name", "My Project")
        >>> print(config.get("project.name"))
        My Project
    """
    
    def __init__(self, config_path: Optional[str] = None) -> None:
        """Initialize configuration from file or create default.
        
        Args:
            config_path: Path to configuration file. If None, uses default.
        """
        if config_path is None:
            config_path = str(Path.cwd() / "config.json")
        
        self.config_path = config_path
        self.data: Dict[str, Any] = {}
        
        # Load existing configuration or create default
        if os.path.exists(self.config_path):
            self.load()
        else:
            self.create_default()
    
    def load(self) -> None:
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            # Create backup of corrupted file and create default
            backup_path = f"{self.config_path}.backup"
            try:
                import shutil
                shutil.copy2(self.config_path, backup_path)
            except IOError:
                pass  # Ignore backup errors
            
            self.create_default()
    
    def save(self) -> None:
        """Save configuration to JSON file."""
        # Ensure directory exists
        Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Write with backup
        temp_path = f"{self.config_path}.tmp"
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        
        # Atomic rename
        os.replace(temp_path, self.config_path)
    
    def create_default(self) -> None:
        """Create default configuration."""
        self.data = {
            "project_name": "AI Context Manager Project",
            "version": "1.0.0",
            "description": "A project managed by AI Context Manager",
            "author": "",
            "email": "",
            "export": {
                "format": "markdown",
                "include_metadata": True,
                "compress_output": False,
                "max_file_size": 10485760,
                "exclude_patterns": [
                    "*.pyc",
                    "__pycache__/*",
                    ".git/*",
                    "node_modules/*",
                    ".venv/*",
                    "venv/*",
                    "*.egg-info/*",
                    "dist/*",
                    "build/*"
                ]
            },
            "selector": {
                "default_extensions": [".py", ".js", ".ts", ".md", ".txt", ".json", ".yaml", ".yml"],
                "max_depth": 10,
                "follow_symlinks": False,
                "include_hidden": False
            },
            "token_counter": {
                "encoding": "cl100k_base",
                "show_details": True
            },
            "ai": {
                "openai_api_key": "",
                "model": "gpt-4-turbo",
                "embedding_model": "text-embedding-3-small",
                "qdrant_url": "http://localhost:6333",
                "collection_name": "ai_context_manager_docs"
            },
        }
        self.save()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with dot notation support.
        
        Args:
            key: Configuration key (supports dot notation for nested keys)
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.data
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value with dot notation support.
        
        Args:
            key: Configuration key (supports dot notation for nested keys)
            value: Value to set
        """
        keys = key.split('.')
        data = self.data
        
        # Navigate to parent of target key
        for k in keys[:-1]:
            if k not in data or not isinstance(data[k], dict):
                data[k] = {}
            data = data[k]
        
        # Set the value
        data[keys[-1]] = value
    
    def has(self, key: str) -> bool:
        """Check if configuration key exists.
        
        Args:
            key: Configuration key (supports dot notation)
            
        Returns:
            True if key exists, False otherwise
        """
        return self.get(key) is not None
    
    def remove(self, key: str) -> None:
        """Remove configuration key.
        
        Args:
            key: Configuration key (supports dot notation)
        """
        keys = key.split('.')
        data = self.data
        
        # Navigate to parent of target key
        for k in keys[:-1]:
            if k not in data or not isinstance(data[k], dict):
                return  # Key doesn't exist
            data = data[k]
        
        # Remove the key
        if keys[-1] in data:
            del data[keys[-1]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of configuration
        """
        return self.data.copy()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], config_path: Optional[str] = None) -> 'Config':
        """Create configuration from dictionary.
        
        Args:
            data: Configuration data
            config_path: Path to save configuration
            
        Returns:
            Config instance
        """
        config = cls(config_path)
        config.data = data.copy()
        config.save()
        return config
    
    def copy(self) -> 'Config':
        """Create a copy of the configuration.
        
        Returns:
            New Config instance with same data
        """
        new_config = Config.__new__(Config)
        new_config.config_path = self.config_path
        new_config.data = self.data.copy()
        return new_config
    
    def backup(self, backup_path: Optional[str] = None) -> str:
        """Create backup of configuration file.
        
        Args:
            backup_path: Custom backup path. If None, uses timestamp.
            
        Returns:
            Path to backup file
        """
        import datetime
        
        if backup_path is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.config_path}.backup.{timestamp}"
        
        import shutil
        shutil.copy2(self.config_path, backup_path)
        return backup_path
    
    # Dictionary-like interface
    def __getitem__(self, key: str) -> Any:
        """Get value using bracket notation."""
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Set value using bracket notation."""
        self.set(key, value)
    
    def __delitem__(self, key: str) -> None:
        """Delete key using del operator."""
        if not self.has(key):
            raise KeyError(key)
        self.remove(key)
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists using 'in' operator."""
        return self.has(key)
    
    def __iter__(self):
        """Iterate over top-level keys."""
        return iter(self.data)
    
    def __len__(self) -> int:
        """Get number of top-level keys."""
        return len(self.data)
    
    def __str__(self) -> str:
        """String representation of configuration."""
        return json.dumps(self.data, indent=2, ensure_ascii=False)
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Config(config_path='{self.config_path}')"
    
    def __eq__(self, other) -> bool:
        """Check equality with another Config instance."""
        if not isinstance(other, Config):
            return False
        return self.data == other.data


# Default configuration constants
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


@lru_cache(maxsize=None)
def get_config_dir() -> Path:
    """Get the XDG-compliant configuration directory for AI Context Manager.
    
    This function determines the appropriate configuration directory based on
    the XDG Base Directory Specification and platform-specific conventions.
    
    Returns:
        Path: The absolute path to the configuration directory, creating it if necessary.
        
    Platform-specific behavior:
        - Linux/macOS: ~/.config/ai-context-manager/
        - Windows: %LOCALAPPDATA%/ai-context-manager/
        - If XDG_CONFIG_HOME is set, uses that instead of ~/.config/
    """
    import platform
    
    # Check for XDG_CONFIG_HOME environment variable
    xdg_config_home = os.getenv("XDG_CONFIG_HOME")
    
    if xdg_config_home:
        config_dir = Path(xdg_config_home) / "ai-context-manager"
    else:
        # Platform-specific handling
        system = platform.system()
        
        if system == "Windows":
            # Use LOCALAPPDATA on Windows
            local_app_data = os.getenv("LOCALAPPDATA")
            if local_app_data:
                config_dir = Path(local_app_data) / "ai-context-manager"
            else:
                # Fallback to home directory
                config_dir = Path.home() / "AppData" / "Local" / "ai-context-manager"
        else:
            # Linux/macOS and other Unix-like systems
            config_dir = Path.home() / ".config" / "ai-context-manager"
    
    # Ensure the directory exists
    config_dir.mkdir(parents=True, exist_ok=True)
    
    return config_dir