"""Configuration management for AI Context Manager."""
import os
from pathlib import Path
from typing import Optional


class Config:
    """Configuration manager for AI Context Manager."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize configuration.
        
        Args:
            config_dir: Custom configuration directory. If None, uses default.
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / ".ai-context-manager"
        
        self.context_file = self.config_dir / "context.yaml"
        self.profiles_dir = self.config_dir / "profiles"
    
    def init(self) -> None:
        """Initialize configuration directory and files."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        
        # Create default context file if it doesn't exist
        if not self.context_file.exists():
            self.context_file.write_text("files: []\n")