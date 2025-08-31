"""Tests for profile management functionality."""

import tempfile
from pathlib import Path
import pytest

from ai_context_manager.core.profile_manager import ProfileManager


class TestProfileManager:
    """Test cases for ProfileManager."""
    
    def test_create_profile(self, temp_config_dir):
        """Test creating a new profile."""
        manager = ProfileManager(config_dir=temp_config_dir)
        
        profile_data = {
            "name": "test-profile",
            "include_patterns": ["*.py", "*.js"],
            "exclude_patterns": ["__pycache__/*", "*.pyc"],
            "max_file_size": 102400,
            "description": "Test profile"
        }
        
        manager.save_profile("test-profile", profile_data)
        
        assert manager.profile_exists("test-profile")
        loaded_profile = manager.get_profile("test-profile")
        assert loaded_profile == profile_data
    
    def test_get_nonexistent_profile(self, temp_config_dir):
        """Test getting a non-existent profile."""
        manager = ProfileManager(config_dir=temp_config_dir)
        
        with pytest.raises(ValueError, match="Profile 'nonexistent' not found"):
            manager.get_profile("nonexistent")
    
    def test_delete_profile(self, temp_config_dir, existing_profile):
        """Test deleting an existing profile."""
        manager = ProfileManager(config_dir=temp_config_dir)
        
        assert manager.profile_exists(existing_profile)
        manager.delete_profile(existing_profile)
        assert not manager.profile_exists(existing_profile)
    
    def test_delete_nonexistent_profile(self, temp_config_dir):
        """Test deleting a non-existent profile."""
        manager = ProfileManager(config_dir=temp_config_dir)
        
        with pytest.raises(ValueError, match="Profile 'nonexistent' not found"):
            manager.delete_profile("nonexistent")
    
    def test_list_profiles(self, temp_config_dir):
        """Test listing all profiles."""
        manager = ProfileManager(config_dir=temp_config_dir)
        
        # Create multiple profiles
        profiles = [
            {"name": "profile1", "include_patterns": ["*.py"], "exclude_patterns": [], "max_file_size": 102400},
            {"name": "profile2", "include_patterns": ["*.js"], "exclude_patterns": [], "max_file_size": 51200},
            {"name": "profile3", "include_patterns": ["*.md"], "exclude_patterns": [], "max_file_size": 204800}
        ]
        
        for profile in profiles:
            manager.save_profile(profile["name"], profile)
        
        listed_profiles = manager.list_profiles()
        assert len(listed_profiles) == 3
        assert "profile1" in listed_profiles
        assert "profile2" in listed_profiles
        assert "profile3" in listed_profiles
    
    def test_profile_overwrite(self, temp_config_dir):
        """Test overwriting an existing profile."""
        manager = ProfileManager(config_dir=temp_config_dir)
        
        initial_data = {
            "name": "overwrite-test",
            "include_patterns": ["*.py"],
            "exclude_patterns": [],
            "max_file_size": 102400
        }
        
        updated_data = {
            "name": "overwrite-test",
            "include_patterns": ["*.py", "*.js"],
            "exclude_patterns": ["*.tmp"],
            "max_file_size": 204800,
            "description": "Updated profile"
        }
        
        manager.save_profile("overwrite-test", initial_data)
        manager.save_profile("overwrite-test", updated_data, force=True)
        
        loaded_profile = manager.get_profile("overwrite-test")
        assert loaded_profile == updated_data
    
    def test_profile_overwrite_without_force(self, temp_config_dir, existing_profile):
        """Test overwriting without force flag."""
        manager = ProfileManager(config_dir=temp_config_dir)
        
        new_data = {
            "name": existing_profile,
            "include_patterns": ["*.js"],
            "exclude_patterns": [],
            "max_file_size": 102400
        }
        
        with pytest.raises(ValueError, match="already exists"):
            manager.save_profile(existing_profile, new_data, force=False)
    
    def test_profile_data_validation(self, temp_config_dir):
        """Test profile data validation."""
        manager = ProfileManager(config_dir=temp_config_dir)
        
        # Test missing required fields
        invalid_data = {"name": "invalid"}
        with pytest.raises(ValueError, match="Invalid profile data"):
            manager.save_profile("invalid", invalid_data)
        
        # Test invalid max_file_size
        invalid_data = {
            "name": "invalid",
            "include_patterns": ["*.py"],
            "exclude_patterns": [],
            "max_file_size": "invalid"
        }
        with pytest.raises(ValueError, match="Invalid profile data"):
            manager.save_profile("invalid", invalid_data)
    
    def test_profile_with_description(self, temp_config_dir):
        """Test creating profile with description."""
        manager = ProfileManager(config_dir=temp_config_dir)
        
        profile_data = {
            "name": "desc-profile",
            "include_patterns": ["*.py"],
            "exclude_patterns": [],
            "max_file_size": 102400,
            "description": "Profile with description"
        }
        
        manager.save_profile("desc-profile", profile_data)
        
        loaded_profile = manager.get_profile("desc-profile")
        assert loaded_profile["description"] == "Profile with description"
    
    def test_profile_without_description(self, temp_config_dir):
        """Test creating profile without description."""
        manager = ProfileManager(config_dir=temp_config_dir)
        
        profile_data = {
            "name": "no-desc-profile",
            "include_patterns": ["*.py"],
            "exclude_patterns": [],
            "max_file_size": 102400
        }
        
        manager.save_profile("no-desc-profile", profile_data)
        
        loaded_profile = manager.get_profile("no-desc-profile")
        assert "description" not in loaded_profile
    
    def test_profile_with_empty_patterns(self, temp_config_dir):
        """Test creating profile with empty patterns."""
        manager = ProfileManager(config_dir=temp_config_dir)
        
        profile_data = {
            "name": "empty-patterns",
            "include_patterns": [],
            "exclude_patterns": [],
            "max_file_size": 102400
        }
        
        manager.save_profile("empty-patterns", profile_data)
        
        loaded_profile = manager.get_profile("empty-patterns")
        assert loaded_profile["include_patterns"] == []
        assert loaded_profile["exclude_patterns"] == []
    
    def test_profile_with_complex_patterns(self, temp_config_dir):
        """Test creating profile with complex patterns."""
        manager = ProfileManager(config_dir=temp_config_dir)
        
        profile_data = {
            "name": "complex-patterns",
            "include_patterns": [
                "**/*.py",
                "**/*.js",
                "src/**/*.ts",
                "!**/test_*",
                "!**/*_test.py"
            ],
            "exclude_patterns": [
                "**/__pycache__/**",
                "**/*.pyc",
                "**/.git/**",
                "**/node_modules/**"
            ],
            "max_file_size": 102400
        }
        
        manager.save_profile("complex-patterns", profile_data)
        
        loaded_profile = manager.get_profile("complex-patterns")
        assert loaded_profile["include_patterns"] == profile_data["include_patterns"]
        assert loaded_profile["exclude_patterns"] == profile_data["exclude_patterns"]
    
    def test_profile_persistence(self, temp_config_dir):
        """Test that profiles persist across manager instances."""
        profile_data = {
            "name": "persistence-test",
            "include_patterns": ["*.py"],
            "exclude_patterns": [],
            "max_file_size": 102400
        }
        
        # Create profile with first manager
        manager1 = ProfileManager(config_dir=temp_config_dir)
        manager1.save_profile("persistence-test", profile_data)
        
        # Load with second manager
        manager2 = ProfileManager(config_dir=temp_config_dir)
        assert manager2.profile_exists("persistence-test")
        
        loaded_profile = manager2.get_profile("persistence-test")
        assert loaded_profile == profile_data
    
    def test_profile_file_structure(self, temp_config_dir):
        """Test that profile files are stored correctly."""
        manager = ProfileManager(config_dir=temp_config_dir)
        
        profile_data = {
            "name": "file-structure-test",
            "include_patterns": ["*.py"],
            "exclude_patterns": [],
            "max_file_size": 102400
        }
        
        manager.save_profile("file-structure-test", profile_data)
        
        # Check that file exists
        profile_file = temp_config_dir / "profiles" / "file-structure-test.json"
        assert profile_file.exists()
        assert profile_file.is_file()
        
        # Check file content
        import json
        with open(profile_file) as f:
            saved_data = json.load(f)
        assert saved_data == profile_data
    
    def test_profile_name_validation(self, temp_config_dir):
        """Test profile name validation."""
        manager = ProfileManager(config_dir=temp_config_dir)
        
        profile_data = {
            "name": "valid-name",
            "include_patterns": ["*.py"],
            "exclude_patterns": [],
            "max_file_size": 102400
        }
        
        # Valid names
        manager.save_profile("valid-name", profile_data)
        manager.save_profile("valid_name", profile_data)
        manager.save_profile("valid123", profile_data)
        
        # Invalid names
        with pytest.raises(ValueError, match="Invalid profile name"):
            manager.save_profile("", profile_data)
        
        with pytest.raises(ValueError, match="Invalid profile name"):
            manager.save_profile("invalid/name", profile_data)
        
        with pytest.raises(ValueError, match="Invalid profile name"):
            manager.save_profile("invalid\\name", profile_data)
        
        with pytest.raises(ValueError, match="Invalid profile name"):
            manager.save_profile("invalid:name", profile_data)
    
    def test_profile_case_sensitivity(self, temp_config_dir):
        """Test profile name case sensitivity."""
        manager = ProfileManager(config_dir=temp_config_dir)
        
        profile_data = {
            "name": "case-test",
            "include_patterns": ["*.py"],
            "exclude_patterns": [],
            "max_file_size": 102400
        }
        
        manager.save_profile("case-test", profile_data)
        
        # Should be case sensitive
        assert manager.profile_exists("case-test")
        assert not manager.profile_exists("Case-Test")
        assert not manager.profile_exists("CASE-TEST")
    
    def test_profile_directory_creation(self, temp_config_dir):
        """Test that profile directory is created automatically."""
        manager = ProfileManager(config_dir=temp_config_dir)
        
        profile_data = {
            "name": "dir-creation-test",
            "include_patterns": ["*.py"],
            "exclude_patterns": [],
            "max_file_size": 102400
        }
        
        # Ensure profiles directory doesn't exist yet
        profiles_dir = temp_config_dir / "profiles"
        if profiles_dir.exists():
            profiles_dir.rmdir()
        
        manager.save_profile("dir-creation-test", profile_data)
        
        # Check that directory was created
        assert profiles_dir.exists()
        assert profiles_dir.is_dir()