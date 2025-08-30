"""Tests for profile core functionality."""
import json
from pathlib import Path
from typing import Any, Dict

import pytest

from ai_context_manager.core.profile import Profile, ProfileManager


class TestProfile:
    """Test suite for Profile class."""

    def test_profile_creation(self) -> None:
        """Test basic profile creation."""
        profile = Profile(
            name="test-profile",
            description="Test profile",
            include_patterns=["*.py"],
            exclude_patterns=["*.pyc"],
            max_file_size=1024,
            include_binary=False,
            output_format="json",
            output_file="output.json",
            token_limit=1000,
        )
        
        assert profile.name == "test-profile"
        assert profile.description == "Test profile"
        assert profile.include_patterns == ["*.py"]
        assert profile.exclude_patterns == ["*.pyc"]
        assert profile.max_file_size == 1024
        assert profile.include_binary is False
        assert profile.output_format == "json"
        assert profile.output_file == "output.json"
        assert profile.token_limit == 1000

    def test_profile_creation_defaults(self) -> None:
        """Test profile creation with defaults."""
        profile = Profile(name="default-profile")
        
        assert profile.name == "default-profile"
        assert profile.description == ""
        assert profile.include_patterns == ["*"]
        assert profile.exclude_patterns == []
        assert profile.max_file_size == 1024 * 1024  # 1MB
        assert profile.include_binary is False
        assert profile.output_format == "json"
        assert profile.output_file is None
        assert profile.token_limit is None

    def test_profile_to_dict(self) -> None:
        """Test profile serialization to dict."""
        profile = Profile(
            name="test-profile",
            description="Test profile",
            include_patterns=["*.py"],
            exclude_patterns=["*.pyc"],
            max_file_size=1024,
            include_binary=False,
            output_format="json",
            output_file="output.json",
            token_limit=1000,
        )
        
        profile_dict = profile.to_dict()
        
        expected = {
            "name": "test-profile",
            "description": "Test profile",
            "include_patterns": ["*.py"],
            "exclude_patterns": ["*.pyc"],
            "max_file_size": 1024,
            "include_binary": False,
            "output_format": "json",
            "output_file": "output.json",
            "token_limit": 1000,
        }
        
        assert profile_dict == expected

    def test_profile_from_dict(self) -> None:
        """Test profile deserialization from dict."""
        profile_dict = {
            "name": "test-profile",
            "description": "Test profile",
            "include_patterns": ["*.py"],
            "exclude_patterns": ["*.pyc"],
            "max_file_size": 1024,
            "include_binary": False,
            "output_format": "json",
            "output_file": "output.json",
            "token_limit": 1000,
        }
        
        profile = Profile.from_dict(profile_dict)
        
        assert profile.name == "test-profile"
        assert profile.description == "Test profile"
        assert profile.include_patterns == ["*.py"]
        assert profile.exclude_patterns == ["*.pyc"]
        assert profile.max_file_size == 1024
        assert profile.include_binary is False
        assert profile.output_format == "json"
        assert profile.output_file == "output.json"
        assert profile.token_limit == 1000

    def test_profile_from_dict_partial(self) -> None:
        """Test profile deserialization with partial data."""
        profile_dict = {
            "name": "partial-profile",
            "description": "Partial profile",
            "include_patterns": ["*.py"],
        }
        
        profile = Profile.from_dict(profile_dict)
        
        assert profile.name == "partial-profile"
        assert profile.description == "Partial profile"
        assert profile.include_patterns == ["*.py"]
        assert profile.exclude_patterns == []  # Default
        assert profile.max_file_size == 1024 * 1024  # Default
        assert profile.include_binary is False  # Default

    def test_profile_from_dict_invalid(self) -> None:
        """Test profile deserialization with invalid data."""
        with pytest.raises(KeyError):
            Profile.from_dict({})  # Missing required 'name' field

    def test_profile_equality(self) -> None:
        """Test profile equality."""
        profile1 = Profile(name="test", description="Test")
        profile2 = Profile(name="test", description="Test")
        profile3 = Profile(name="different", description="Test")
        
        assert profile1 == profile2
        assert profile1 != profile3
        assert profile1 != "not a profile"

    def test_profile_str_representation(self) -> None:
        """Test profile string representation."""
        profile = Profile(name="test-profile", description="Test profile")
        str_repr = str(profile)
        assert "test-profile" in str_repr
        assert "Test profile" in str_repr


class TestProfileManager:
    """Test suite for ProfileManager class."""

    def test_profile_manager_creation(self, temp_dir: Path) -> None:
        """Test profile manager creation."""
        profiles_dir = temp_dir / "profiles"
        manager = ProfileManager(profiles_dir)
        
        assert manager.profiles_dir == profiles_dir
        assert manager.profiles_dir.exists()

    def test_save_profile(self, temp_dir: Path, sample_profile: Profile) -> None:
        """Test saving a profile."""
        profiles_dir = temp_dir / "profiles"
        manager = ProfileManager(profiles_dir)
        
        manager.save_profile(sample_profile)
        
        profile_file = profiles_dir / f"{sample_profile.name}.json"
        assert profile_file.exists()
        
        # Verify content
        with open(profile_file) as f:
            data = json.load(f)
            assert data["name"] == sample_profile.name
            assert data["description"] == sample_profile.description

    def test_load_profile(self, temp_dir: Path, sample_profile: Profile) -> None:
        """Test loading a profile."""
        profiles_dir = temp_dir / "profiles"
        manager = ProfileManager(profiles_dir)
        
        # Save first
        manager.save_profile(sample_profile)
        
        # Then load
        loaded_profile = manager.load_profile(sample_profile.name)
        
        assert loaded_profile == sample_profile

    def test_load_nonexistent_profile(self, temp_dir: Path) -> None:
        """Test loading a non-existent profile."""
        profiles_dir = temp_dir / "profiles"
        manager = ProfileManager(profiles_dir)
        
        with pytest.raises(FileNotFoundError):
            manager.load_profile("nonexistent")

    def test_list_profiles(self, temp_dir: Path) -> None:
        """Test listing profiles."""
        profiles_dir = temp_dir / "profiles"
        manager = ProfileManager(profiles_dir)
        
        # Create some profiles
        profile1 = Profile(name="profile1", description="First profile")
        profile2 = Profile(name="profile2", description="Second profile")
        
        manager.save_profile(profile1)
        manager.save_profile(profile2)
        
        profiles = manager.list_profiles()
        
        assert len(profiles) == 2
        assert "profile1" in profiles
        assert "profile2" in profiles

    def test_list_profiles_empty(self, temp_dir: Path) -> None:
        """Test listing profiles when none exist."""
        profiles_dir = temp_dir / "profiles"
        manager = ProfileManager(profiles_dir)
        
        profiles = manager.list_profiles()
        assert profiles == []

    def test_delete_profile(self, temp_dir: Path, sample_profile: Profile) -> None:
        """Test deleting a profile."""
        profiles_dir = temp_dir / "profiles"
        manager = ProfileManager(profiles_dir)
        
        # Save first
        manager.save_profile(sample_profile)
        assert manager.profile_exists(sample_profile.name)
        
        # Delete
        manager.delete_profile(sample_profile.name)
        assert not manager.profile_exists(sample_profile.name)

    def test_delete_nonexistent_profile(self, temp_dir: Path) -> None:
        """Test deleting a non-existent profile."""
        profiles_dir = temp_dir / "profiles"
        manager = ProfileManager(profiles_dir)
        
        with pytest.raises(FileNotFoundError):
            manager.delete_profile("nonexistent")

    def test_profile_exists(self, temp_dir: Path, sample_profile: Profile) -> None:
        """Test checking if profile exists."""
        profiles_dir = temp_dir / "profiles"
        manager = ProfileManager(profiles_dir)
        
        assert not manager.profile_exists(sample_profile.name)
        
        manager.save_profile(sample_profile)
        assert manager.profile_exists(sample_profile.name)

    def test_save_profile_overwrite(self, temp_dir: Path, sample_profile: Profile) -> None:
        """Test overwriting an existing profile."""
        profiles_dir = temp_dir / "profiles"
        manager = ProfileManager(profiles_dir)
        
        # Save initial
        manager.save_profile(sample_profile)
        
        # Modify and save again
        sample_profile.description = "Updated description"
        manager.save_profile(sample_profile)
        
        # Verify update
        loaded = manager.load_profile(sample_profile.name)
        assert loaded.description == "Updated description"

    def test_load_profile_invalid_json(self, temp_dir: Path) -> None:
        """Test loading a profile with invalid JSON."""
        profiles_dir = temp_dir / "profiles"
        manager = ProfileManager(profiles_dir)
        
        # Create invalid JSON file
        profile_file = profiles_dir / "invalid.json"
        profile_file.write_text("{ invalid json }")
        
        with pytest.raises(json.JSONDecodeError):
            manager.load_profile("invalid")

    def test_load_profile_missing_name(self, temp_dir: Path) -> None:
        """Test loading a profile with missing required fields."""
        profiles_dir = temp_dir / "profiles"
        manager = ProfileManager(profiles_dir)
        
        # Create JSON file missing required 'name' field
        profile_file = profiles_dir / "missing_name.json"
        profile_file.write_text('{"description": "No name"}')
        
        with pytest.raises(KeyError):
            manager.load_profile("missing_name")

    def test_get_profile_path(self, temp_dir: Path) -> None:
        """Test getting profile file path."""
        profiles_dir = temp_dir / "profiles"
        manager = ProfileManager(profiles_dir)
        
        path = manager.get_profile_path("test-profile")
        expected = profiles_dir / "test-profile.json"
        assert path == expected

    def test_save_profile_with_special_chars(self, temp_dir: Path) -> None:
        """Test saving profile with special characters in name."""
        profiles_dir = temp_dir / "profiles"
        manager = ProfileManager(profiles_dir)
        
        profile = Profile(name="test-profile_123", description="Profile with special chars")
        manager.save_profile(profile)
        
        assert manager.profile_exists("test-profile_123")

    def test_load_all_profiles(self, temp_dir: Path) -> None:
        """Test loading all profiles at once."""
        profiles_dir = temp_dir / "profiles"
        manager = ProfileManager(profiles_dir)
        
        # Create multiple profiles
        profiles = [
            Profile(name="profile1", description="First"),
            Profile(name="profile2", description="Second"),
            Profile(name="profile3", description="Third"),
        ]
        
        for profile in profiles:
            manager.save_profile(profile)
        
        loaded_profiles = manager.load_all_profiles()
        
        assert len(loaded_profiles) == 3
        loaded_names = {p.name for p in loaded_profiles}
        expected_names = {"profile1", "profile2", "profile3"}
        assert loaded_names == expected_names

    def test_load_all_profiles_with_invalid(self, temp_dir: Path) -> None:
        """Test loading all profiles when some are invalid."""
        profiles_dir = temp_dir / "profiles"
        manager = ProfileManager(profiles_dir)
        
        # Create one valid profile
        valid_profile = Profile(name="valid", description="Valid profile")
        manager.save_profile(valid_profile)
        
        # Create one invalid profile file
        invalid_file = profiles_dir / "invalid.json"
        invalid_file.write_text("{ invalid json }")
        
        loaded_profiles = manager.load_all_profiles()
        
        # Should only load valid profiles
        assert len(loaded_profiles) == 1
        assert loaded_profiles[0].name == "valid"