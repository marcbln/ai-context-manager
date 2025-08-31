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
        config.save(str(new_config_file))
        
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
        assert config.data == {}
    
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
    
    def test_get_all_keys(self):
        """Test getting all configuration keys."""
        keys = self.config.get_all_keys()
        
        assert isinstance(keys, list)
        assert "project_name" in keys
        assert "version" in keys
        assert "export.format" in keys
        assert "export.include_metadata" in keys
        assert "nested.level1.level2.value" in keys
    
    def test_get_all_keys_flat(self):
        """Test getting all keys in flat format."""
        keys = self.config.get_all_keys(flat=True)
        
        assert isinstance(keys, list)
        assert "project_name" in keys
        assert "export.format" in keys
        assert "nested.level1.level2.value" in keys
    
    def test_get_all_keys_nested(self):
        """Test getting all keys in nested format."""
        keys = self.config.get_all_keys(flat=False)
        
        assert isinstance(keys, dict)
        assert "project_name" in keys
        assert "export" in keys
        assert isinstance(keys["export"], dict)
        assert "format" in keys["export"]
    
    def test_update_configuration(self):
        """Test updating configuration with dictionary."""
        updates = {
            "project_name": "Updated Project",
            "version": "2.0.0",
            "export": {
                "format": "yaml",
                "new_option": True
            },
            "new_section": {
                "key1": "value1",
                "key2": "value2"
            }
        }
        
        self.config.update(updates)
        
        assert self.config.get("project_name") == "Updated Project"
        assert self.config.get("version") == "2.0.0"
        assert self.config.get("export.format") == "yaml"
        assert self.config.get("export.new_option") is True
        assert self.config.get("new_section.key1") == "value1"
    
    def test_merge_configuration(self):
        """Test merging configuration with dictionary."""
        merge_data = {
            "export": {
                "format": "xml",
                "new_key": "new_value"
            },
            "new_key": "new_value"
        }
        
        # Original format should be preserved
        original_format = self.config.get("export.format")
        
        self.config.merge(merge_data)
        
        # New values should be added
        assert self.config.get("export.new_key") == "new_value"
        assert self.config.get("new_key") == "new_value"
        
        # Existing values should be updated
        assert self.config.get("export.format") == "xml"
    
    def test_reset_configuration(self):
        """Test resetting configuration to empty state."""
        self.config.reset()
        
        assert self.config.data == {}
        assert self.config.get("project_name") is None
        assert self.config.get("export") is None
    
    def test_save_configuration_backup(self):
        """Test saving configuration with backup."""
        backup_file = self.test_dir / "backup.json"
        
        # Create backup
        self.config.backup(str(backup_file))
        
        # Verify backup file exists
        assert backup_file.exists()
        
        # Verify backup contains original data
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        
        assert backup_data["project_name"] == "Test Project"
        assert backup_data["export"]["format"] == "markdown"
    
    def test_configuration_to_dict(self):
        """Test converting configuration to dictionary."""
        config_dict = self.config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert config_dict["project_name"] == "Test Project"
        assert config_dict["export"]["format"] == "markdown"
        assert config_dict["nested"]["level1"]["level2"]["value"] == "deep_value"
    
    def test_configuration_from_dict(self):
        """Test creating configuration from dictionary."""
        test_dict = {
            "project_name": "From Dict",
            "version": "3.0.0",
            "export": {
                "format": "custom"
            }
        }
        
        config = Config.from_dict(test_dict)
        assert config.get("project_name") == "From Dict"
        assert config.get("version") == "3.0.0"
        assert config.get("export.format") == "custom"
    
    def test_configuration_str_representation(self):
        """Test string representation of configuration."""
        str_repr = str(self.config)
        
        assert isinstance(str_repr, str)
        assert "Test Project" in str_repr
        assert "1.0.0" in str_repr
    
    def test_configuration_repr(self):
        """Test repr of configuration."""
        repr_str = repr(self.config)
        
        assert isinstance(repr_str, str)
        assert "Config" in repr_str
        assert str(self.config_file) in repr_str
    
    def test_configuration_iteration(self):
        """Test iterating over configuration."""
        keys = list(self.config)
        
        assert isinstance(keys, list)
        assert "project_name" in keys
        assert "version" in keys
        assert "export" in keys
    
    def test_configuration_length(self):
        """Test getting length of configuration."""
        length = len(self.config)
        
        assert isinstance(length, int)
        assert length > 0
    
    def test_configuration_contains(self):
        """Test checking if key exists using 'in' operator."""
        assert "project_name" in self.config
        assert "export.format" in self.config
        assert "nested.level1.level2.value" in self.config
        assert "nonexistent" not in self.config
    
    def test_configuration_getitem(self):
        """Test getting values using bracket notation."""
        assert self.config["project_name"] == "Test Project"
        assert self.config["export.format"] == "markdown"
        assert self.config["nested.level1.level2.value"] == "deep_value"
    
    def test_configuration_setitem(self):
        """Test setting values using bracket notation."""
        self.config["new_key"] = "new_value"
        assert self.config["new_key"] == "new_value"
        
        self.config["export.format"] = "json"
        assert self.config["export.format"] == "json"
    
    def test_configuration_delitem(self):
        """Test deleting keys using del operator."""
        # Add test key
        self.config["test_key"] = "test_value"
        assert self.config["test_key"] == "test_value"
        
        # Delete key
        del self.config["test_key"]
        assert "test_key" not in self.config
    
    def test_configuration_delitem_nonexistent(self):
        """Test deleting non-existent key."""
        with pytest.raises(KeyError):
            del self.config["nonexistent_key"]
    
    def test_configuration_equality(self):
        """Test configuration equality."""
        config1 = Config(str(self.config_file))
        config2 = Config(str(self.config_file))
        
        assert config1 == config2
        
        # Modify one config
        config1.set("new_key", "new_value")
        assert config1 != config2
    
    def test_configuration_copy(self):
        """Test configuration copying."""
        config_copy = self.config.copy()
        
        assert config_copy is not self.config
        assert config_copy.data == self.config.data
        
        # Modify copy
        config_copy.set("new_key", "new_value")
        assert self.config.get("new_key") is None
    
    def test_configuration_with_unicode(self):
        """Test configuration with Unicode characters."""
        unicode_config = {
            "project_name": "测试项目",
            "description": "这是一个测试项目",
            "emoji": "🚀🎯",
            "special_chars": "áéíóú ñ € £ ¥"
        }
        
        config_file = self.test_dir / "unicode_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(unicode_config, f, ensure_ascii=False)
        
        config = Config(str(config_file))
        
        assert config.get("project_name") == "测试项目"
        assert config.get("description") == "这是一个测试项目"
        assert config.get("emoji") == "🚀🎯"
        assert config.get("special_chars") == "áéíóú ñ € £ ¥"
    
    def test_configuration_from_dict(self):
        """Test creating configuration from dictionary."""
        test_dict = {
            "project_name": "From Dict",
            "version": "3.0.0",
            "export": {
                "format": "custom"
            }
        }
        
        config = Config.from_dict(test_dict)
        assert config.get("project_name") == "From Dict"
        assert config.get("version") == "3.0.0"
        assert config.get("export.format") == "custom"
    
    def test_configuration_str_representation(self):
        """Test string representation of configuration."""
        str_repr = str(self.config)
        
        assert isinstance(str_repr, str)
        assert "Test Project" in str_repr
        assert "1.0.0" in str_repr
    
    def test_configuration_repr(self):
        """Test repr of configuration."""
        repr_str = repr(self.config)
        
        assert isinstance(repr_str, str)
        assert "Config" in repr_str
        assert str(self.config_file) in repr_str
    
    def test_configuration_iteration(self):
        """Test iterating over configuration."""
        keys = list(self.config)
        
        assert isinstance(keys, list)
        assert "project_name" in keys
        assert "version" in keys
        assert "export" in keys
    
    def test_configuration_length(self):
        """Test getting length of configuration."""
        length = len(self.config)
        
        assert isinstance(length, int)
        assert length > 0
    
    def test_configuration_contains(self):
        """Test checking if key exists using 'in' operator."""
        assert "project_name" in self.config
        assert "export.format" in self.config
        assert "nested.level1.level2.value" in self.config
        assert "nonexistent" not in self.config
    
    def test_configuration_getitem(self):
        """Test getting values using bracket notation."""
        assert self.config["project_name"] == "Test Project"
        assert self.config["export.format"] == "markdown"
        assert self.config["nested.level1.level2.value"] == "deep_value"
    
    def test_configuration_setitem(self):
        """Test setting values using bracket notation."""
        self.config["new_key"] = "new_value"
        assert self.config["new_key"] == "new_value"
        
        self.config["export.format"] = "json"
        assert self.config["export.format"] == "json"
    
    def test_configuration_delitem(self):
        """Test deleting keys using del operator."""
        # Add test key
        self.config["test_key"] = "test_value"
        assert self.config["test_key"] == "test_value"
        
        # Delete key
        del self.config["test_key"]
        assert "test_key" not in self.config
    
    def test_configuration_delitem_nonexistent(self):
        """Test deleting non-existent key."""
        with pytest.raises(KeyError):
            del self.config["nonexistent_key"]
    
    def test_configuration_equality(self):
        """Test configuration equality."""
        config1 = Config(str(self.config_file))
        config2 = Config(str(self.config_file))
        
        assert config1 == config2
        
        # Modify one config
        config1.set("new_key", "new_value")
        assert config1 != config2
    
    def test_configuration_copy(self):
        """Test configuration copying."""
        config_copy = self.config.copy()
        
        assert config_copy is not self.config
        assert config_copy.data == self.config.data
        
        # Modify copy
        config_copy.set("new_key", "new_value")
        assert self.config.get("new_key") is None
    
    def test_configuration_with_unicode(self):
        """Test configuration with Unicode characters."""
        unicode_config = {
            "project_name": "测试项目",
            "description": "这是一个测试项目",
            "emoji": "🚀🎯",
            "special_chars": "áéíóú ñ € £ ¥"
        }
        
        config_file = self.test_dir / "unicode_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(unicode_config, f, ensure_ascii=False)
        
        config = Config(str(config_file))
        
        assert config.get("project_name") == "测试项目"
        assert config.get("description") == "这是一个测试项目"
        assert config.get("emoji") == "🚀🎯"
        assert config.get("special_chars") == "áéíóú ñ € £ ¥"
