"""Tests for profile command functionality."""
import json
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from ai_context_manager.commands.profile_cmd import (
    create_profile,
    delete_profile,
    list_profiles,
    load_profile,
    show_profile,
    update_profile,
)
from ai_context_manager.core.profile import Profile


class TestProfileCommands:
    """Test suite for profile commands."""

    def test_create_profile_success(self, temp_dir: Path) -> None:
        """Test successful profile creation."""
        runner = CliRunner()
        profiles_dir = temp_dir / "profiles"
        
        result = runner.invoke(create_profile, [
            "--name", "test-profile",
            "--description", "Test profile",
            "--include-patterns", "*.py,*.js",
            "--exclude-patterns", "*.pyc,*.log",
            "--max-file-size", "2048",
            "--include-binary",
            "--output-format", "markdown",
            "--output-file", "output.md",
            "--token-limit", "5000",
            "--profiles-dir", str(profiles_dir)
        ])
        
        assert result.exit_code == 0
        assert "Profile 'test-profile' created successfully" in result.output
        
        # Verify profile was created
        profile_file = profiles_dir / "test-profile.json"
        assert profile_file.exists()
        
        with open(profile_file) as f:
            data = json.load(f)
            assert data["name"] == "test-profile"
            assert data["description"] == "Test profile"
            assert data["include_patterns"] == ["*.py", "*.js"]
            assert data["exclude_patterns"] == ["*.pyc", "*.log"]
            assert data["max_file_size"] == 2048
            assert data["include_binary"] is True
            assert data["output_format"] == "markdown"
            assert data["output_file"] == "output.md"
            assert data["token_limit"] == 5000

    def test_create_profile_minimal(self, temp_dir: Path) -> None:
        """Test creating profile with minimal options."""
        runner = CliRunner()
        profiles_dir = temp_dir / "profiles"
        
        result = runner.invoke(create_profile, [
            "--name", "minimal-profile",
            "--profiles-dir", str(profiles_dir)
        ])
        
        assert result.exit_code == 0
        assert "Profile 'minimal-profile' created successfully" in result.output

    def test_create_profile_duplicate(self, temp_dir: Path) -> None:
        """Test creating duplicate profile."""
        runner = CliRunner()
        profiles_dir = temp_dir / "profiles"
        
        # Create first
        runner.invoke(create_profile, [
            "--name", "duplicate-profile",
            "--profiles-dir", str(profiles_dir)
        ])
        
        # Try to create duplicate
        result = runner.invoke(create_profile, [
            "--name", "duplicate-profile",
            "--profiles-dir", str(profiles_dir)
        ])
        
        assert result.exit_code == 1
        assert "already exists" in result.output

    def test_list_profiles_empty(self, temp_dir: Path) -> None:
        """Test listing profiles when none exist."""
        runner = CliRunner()
        profiles_dir = temp_dir / "profiles"
        
        result = runner.invoke(list_profiles, [
            "--profiles-dir", str(profiles_dir)
        ])
        
        assert result.exit_code == 0
        assert "No profiles found" in result.output

    def test_list_profiles_with_data(self, temp_dir: Path) -> None:
        """Test listing profiles with existing profiles."""
        runner = CliRunner()
        profiles_dir = temp_dir / "profiles"
        
        # Create some profiles
        for name in ["profile1", "profile2", "profile3"]:
            runner.invoke(create_profile, [
                "--name", name,
                "--description", f"Description for {name}",
                "--profiles-dir", str(profiles_dir)
            ])
        
        result = runner.invoke(list_profiles, [
            "--profiles-dir", str(profiles_dir)
        ])
        
        assert result.exit_code == 0
        assert "profile1" in result.output
        assert "profile2" in result.output
        assert "profile3" in result.output
        assert "Description for profile1" in result.output

    def test_show_profile(self, temp_dir: Path) -> None:
        """Test showing profile details."""
        runner = CliRunner()
        profiles_dir = temp_dir / "profiles"
        
        # Create profile
        runner.invoke(create_profile, [
            "--name", "show-test",
            "--description", "Profile to show",
            "--include-patterns", "*.py",
            "--output-format", "json",
            "--profiles-dir", str(profiles_dir)
        ])
        
        result = runner.invoke(show_profile, [
            "show-test",
            "--profiles-dir", str(profiles_dir)
        ])
        
        assert result.exit_code == 0
        assert "show-test" in result.output
        assert "Profile to show" in result.output
        assert "*.py" in result.output
        assert "json" in result.output

    def test_show_nonexistent_profile(self, temp_dir: Path) -> None:
        """Test showing non-existent profile."""
        runner = CliRunner()
        profiles_dir = temp_dir / "profiles"
        
        result = runner.invoke(show_profile, [
            "nonexistent",
            "--profiles-dir", str(profiles_dir)
        ])
        
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_delete_profile(self, temp_dir: Path) -> None:
        """Test deleting a profile."""
        runner = CliRunner()
        profiles_dir = temp_dir / "profiles"
        
        # Create profile
        runner.invoke(create_profile, [
            "--name", "delete-test",
            "--profiles-dir", str(profiles_dir)
        ])
        
        # Delete it
        result = runner.invoke(delete_profile, [
            "delete-test",
            "--profiles-dir", str(profiles_dir)
        ])
        
        assert result.exit_code == 0
        assert "Profile 'delete-test' deleted successfully" in result.output
        
        # Verify it's gone
        result = runner.invoke(show_profile, [
            "delete-test",
            "--profiles-dir", str(profiles_dir)
        ])
        assert result.exit_code == 1

    def test_delete_nonexistent_profile(self, temp_dir: Path) -> None:
        """Test deleting non-existent profile."""
        runner = CliRunner()
        profiles_dir = temp_dir / "profiles"
        
        result = runner.invoke(delete_profile, [
            "nonexistent",
            "--profiles-dir", str(profiles_dir)
        ])
        
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_update_profile(self, temp_dir: Path) -> None:
        """Test updating a profile."""
        runner = CliRunner()
        profiles_dir = temp_dir / "profiles"
        
        # Create initial profile
        runner.invoke(create_profile, [
            "--name", "update-test",
            "--description", "Original description",
            "--include-patterns", "*.py",
            "--profiles-dir", str(profiles_dir)
        ])
        
        # Update it
        result = runner.invoke(update_profile, [
            "update-test",
            "--description", "Updated description",
            "--exclude-patterns", "*.pyc",
            "--max-file-size", "2048",
            "--output-format", "markdown",
            "--profiles-dir", str(profiles_dir)
        ])
        
        assert result.exit_code == 0
        assert "Profile 'update-test' updated successfully" in result.output
        
        # Verify changes
        result = runner.invoke(show_profile, [
            "update-test",
            "--profiles-dir", str(profiles_dir)
        ])
        assert "Updated description" in result.output
        assert "*.pyc" in result.output
        assert "markdown" in result.output

    def test_update_nonexistent_profile(self, temp_dir: Path) -> None:
        """Test updating non-existent profile."""
        runner = CliRunner()
        profiles_dir = temp_dir / "profiles"
        
        result = runner.invoke(update_profile, [
            "nonexistent",
            "--description", "New description",
            "--profiles-dir", str(profiles_dir)
        ])
        
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_load_profile_command(self, temp_dir: Path) -> None:
        """Test load profile command."""
        runner = CliRunner()
        profiles_dir = temp_dir / "profiles"
        
        # Create profile
        runner.invoke(create_profile, [
            "--name", "load-test",
            "--description", "Profile to load",
            "--include-patterns", "*.py",
            "--output-format", "json",
            "--profiles-dir", str(profiles_dir)
        ])
        
        with patch('ai_context_manager.commands.profile_cmd.export_context') as mock_export:
            result = runner.invoke(load_profile, [
                "load-test",
                "--path", str(temp_dir),
                "--profiles-dir", str(profiles_dir)
            ])
            
            assert result.exit_code == 0
            mock_export.assert_called_once()

    def test_load_nonexistent_profile_command(self, temp_dir: Path) -> None:
        """Test loading non-existent profile."""
        runner = CliRunner()
        profiles_dir = temp_dir / "profiles"
        
        result = runner.invoke(load_profile, [
            "nonexistent",
            "--path", str(temp_dir),
            "--profiles-dir", str(profiles_dir)
        ])
        
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_create_profile_with_comma_separated_patterns(self, temp_dir: Path) -> None:
        """Test creating profile with comma-separated patterns."""
        runner = CliRunner()
        profiles_dir = temp_dir / "profiles"
        
        result = runner.invoke(create_profile, [
            "--name", "comma-test",
            "--include-patterns", "*.py,*.js,*.ts",
            "--exclude-patterns", "*.pyc,*.log,*.tmp",
            "--profiles-dir", str(profiles_dir)
        ])
        
        assert result.exit_code == 0
        
        # Verify patterns were parsed correctly
        result = runner.invoke(show_profile, [
            "comma-test",
            "--profiles-dir", str(profiles_dir)
        ])
        assert "*.py" in result.output
        assert "*.js" in result.output
        assert "*.ts" in result.output
        assert "*.pyc" in result.output
        assert "*.log" in result.output
        assert "*.tmp" in result.output

    def test_create_profile_help(self) -> None:
        """Test create profile help output."""
        runner = CliRunner()
        
        result = runner.invoke(create_profile, ["--help"])
        
        assert result.exit_code == 0
        assert "Create a new profile" in result.output
        assert "--name" in result.output
        assert "--description" in result.output
        assert "--include-patterns" in result.output