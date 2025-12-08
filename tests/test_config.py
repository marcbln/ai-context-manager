"""Tests for the configuration module."""

import tempfile
import json
import os
from pathlib import Path
import pytest

from ai_context_manager.config import Config


class TestConfig:
    """Test cases for the Config class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        
        # Create test config file
        self.config_file = self.test_dir / "test_config.json"
        self.create_test_config()
        
        # Create config instance
        self.config = Config(str(self.config_file))
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def create_test_config(self):
        """Create a test configuration file."""
        config_data = {
            "project_name": "Test Project",
            "version": "1.0.0",
            "description": "A test project for configuration testing",
            "author": "Test Author",
            "email": "test@example.com",
            "export": {
                "format": "markdown",
                "include_metadata": True,
                "compress_output": False,
                "max_file_size": 10485760,
                "exclude_patterns": ["*.pyc", "__pycache__/*", ".git/*"]
            },
            "selector": {
                "default_extensions": [".py", ".js", ".md", ".txt"],
                "max_depth": 10,
                "follow_symlinks": False,
                "include_hidden": False
            },
            "token_counter": {
                "encoding": "cl100k_base",
                "show_details": True
            },
            "custom_field": "custom_value",
            "nested": {
                "level1": {
                    "level2": {
                        "value": "deep_value"
                    }
                }
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def test_config_initialization(self):
        """Test Config initialization."""
        config = Config(str(self.config_file))
        assert config.config_path == str(self.config_file)
        assert config.data is not None
        assert isinstance(config.data, dict)
    
    def test_config_initialization_default(self):
        """Test Config initialization with default path."""
        config = Config()
        assert config.config_path.endswith("config.json")
        assert config.data is not None
    
    def test_get_simple_value(self):
        """Test getting simple configuration values."""
        assert self.config.get("project_name") == "Test Project"
        assert self.config.get("version") == "1.0.0"
        assert self.config.get("description") == "A test project for configuration testing"
        assert self.config.get("author") == "Test Author"
    
    def test_get_nested_value(self):
        """Test getting nested configuration values."""
        assert self.config.get("export.format") == "markdown"
        assert self.config.get("export.include_metadata") is True
        assert self.config.get("export.compress_output") is False
        assert self.config.get("export.max_file_size") == 10485760
    
    def test_get_deep_nested_value(self):
        """Test getting deeply nested configuration values."""
        assert self.config.get("nested.level1.level2.value") == "deep_value"
    
    def test_get_with_default(self):
        """Test getting values with default fallback."""
        assert self.config.get("nonexistent", "default") == "default"
        assert self.config.get("export.nonexistent", "default") == "default"
        assert self.config.get("nested.level1.nonexistent", "default") == "default"
    
    def test_get_without_default(self):
        """Test getting non-existent values without default."""
        assert self.config.get("nonexistent") is None
        assert self.config.get("export.nonexistent") is None
        assert self.config.get("nested.level1.nonexistent") is None
    
    def test_set_simple_value(self):
        """Test setting simple configuration values."""
        self.config.set("new_key", "new_value")
        assert self.config.get("new_key") == "new_value"
        
        self.config.set("project_name", "Updated Project")
        assert self.config.get("project_name") == "Updated Project"
    
    def test_set_nested_value(self):
        """Test setting nested configuration values."""
        self.config.set("export.new_key", "new_value")
        assert self.config.get("export.new_key") == "new_value"
        
        self.config.set("export.format", "json")
        assert self.config.get("export.format") == "json"
    
    def test_set_deep_nested_value(self):
        """Test setting deeply nested configuration values."""
        self.config.set("new.nested.level.value", "deep_new_value")
        assert self.config.get("new.nested.level.value") == "deep_new_value"
    
    def test_set_overwrite_nested_structure(self):
        """Test overwriting nested structure."""
        self.config.set("export", {"new_format": "xml", "compression": True})
        assert self.config.get("export.new_format") == "xml"
        assert self.config.get("export.compression") is True
        assert self.config.get("export.format") is None  # Old value should be gone
    
    def test_has_key(self):
        """Test checking if key exists."""
        assert self.config.has("project_name") is True
        assert self.config.has("export.format") is True
        assert self.config.has("nested.level1.level2.value") is True
        assert self.config.has("nonexistent") is False
        assert self.config.has("export.nonexistent") is False
    
    def test_remove_key(self):
        """Test removing configuration keys."""
        # Remove simple key
        self.config.remove("custom_field")
        assert self.config.get("custom_field") is None
        
        # Remove nested key
        self.config.remove("export.format")
        assert self.config.get("export.format") is None
        
        # Remove deep nested key
        self.config.remove("nested.level1.level2.value")
        assert self.config.get("nested.level1.level2.value") is None
    
    def test_remove_nonexistent_key(self):
        """Test removing non-existent key."""
        # Should not raise exception
        self.config.remove("nonexistent")
        self.config.remove("export.nonexistent")
    
    def test_save_configuration(self):
        """Test saving configuration to file."""
        # Modify configuration
        self.config.set("new_key", "new_value")
        self.config.set("export.format", "xml")
        
        # Save configuration
        self.config.save()
        
        # Load configuration from file
        with open(self.config_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["new_key"] == "new_value"
        assert saved_data["export"]["format"] == "xml"
    
    def test_save_configuration_new_file(self):
        """Test saving configuration to new file."""
        new_config_file = self.test_dir / "new_config.json"
        
        # Create new config
        config = Config()
        config.set("test_key", "test_value")
        
        # Save to new file
        config.config_path = str(new_config_file)
        config.save()
        
        # Verify file exists and contains correct data
        assert new_config_file.exists()
        with open(new_config_file, 'r') as f:
            saved_data = json.load(f)
        assert saved_data["test_key"] == "test_value"
    
    def test_load_configuration(self):
        """Test loading configuration from file."""
        # Create new config file
        new_config_file = self.test_dir / "load_test.json"
        test_data = {"test_key": "test_value", "nested": {"key": "value"}}
        
        with open(new_config_file, 'w') as f:
            json.dump(test_data, f)
        
        # Load configuration
        config = Config(str(new_config_file))
        assert config.get("test_key") == "test_value"
        assert config.get("nested.key") == "value"
    
    def test_load_nonexistent_file(self):
        """Test loading non-existent configuration file."""
        nonexistent_file = self.test_dir / "nonexistent.json"
        
        # Should create new empty config
        config = Config(str(nonexistent_file))
        assert config.data != {}
        assert config.get("project_name") is not None
    
    def test_load_invalid_json(self):
        """Test loading invalid JSON file."""
        invalid_file = self.test_dir / "invalid.json"
        invalid_file.write_text("{ invalid json }")
        
        # Should handle gracefully
        try:
            config = Config(str(invalid_file))
            # Either load empty config or raise meaningful exception
            assert isinstance(config.data, dict)
        except Exception as e:
            # Should raise meaningful exception
            assert "json" in str(e).lower() or "parse" in str(e).lower()
    
