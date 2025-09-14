"""Profile management for AI Context Manager."""
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict
import yaml


@dataclass
class PathEntry:
    """Represents a path entry in a profile."""
    path: Path
    is_directory: bool
    recursive: bool = True


@dataclass
class Profile:
    """Represents an export profile."""
    name: str
    description: str  # <-- ADDED THIS FIELD
    created: datetime
    modified: datetime
    base_path: Optional[Path]
    paths: List[PathEntry]
    exclude_patterns: List[str]
    include_metadata: bool = True

    def to_dict(self) -> dict:
        """Convert profile to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,  # <-- ADDED THIS LINE
            "created": self.created.isoformat(),
            "modified": self.modified.isoformat(),
            "base_path": str(self.base_path) if self.base_path else None,
            "paths": [
                {
                    "path": str(entry.path),
                    "is_directory": entry.is_directory,
                    "recursive": entry.recursive
                }
                for entry in self.paths
            ],
            "exclude_patterns": self.exclude_patterns,
            "include_metadata": self.include_metadata
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Profile':
        """Create profile from dictionary representation."""
        return cls(
            name=data["name"],
            description=data.get("description", ""),  # <-- ADDED THIS LINE, with default for backward compatibility
            created=datetime.fromisoformat(data["created"]),
            modified=datetime.fromisoformat(data["modified"]),
            base_path=Path(data["base_path"]) if data.get("base_path") else None,
            paths=[
                PathEntry(
                    path=Path(entry["path"]),
                    is_directory=entry["is_directory"],
                    recursive=entry.get("recursive", True)
                )
                for entry in data.get("paths", [])
            ],
            exclude_patterns=data.get("exclude_patterns", []),
            include_metadata=data.get("include_metadata", True)
        )
    
    def save(self, filepath: Path) -> None:
        """Save profile to file."""
        with open(filepath, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)
    
    @classmethod
    def load(cls, filepath: Path) -> 'Profile':
        """Load profile from file."""
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)


class ProfileManager:
    """Manages multiple profiles."""
    
    def __init__(self, profiles_dir: Path):
        """Initialize profile manager with profiles directory."""
        self.profiles_dir = profiles_dir
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
    
    def list_profiles(self) -> List[str]:
        """List all available profile names."""
        if not self.profiles_dir.exists():
            return []
        
        profiles = []
        for file in self.profiles_dir.glob("*.yaml"):
            profiles.append(file.stem)
        return sorted(profiles)
    
    def get_profile(self, name: str) -> Optional[Profile]:
        """Get a profile by name."""
        profile_file = self.profiles_dir / f"{name}.yaml"
        if not profile_file.exists():
            return None
        
        try:
            return Profile.load(profile_file)
        except Exception:
            return None
    
    def save_profile(self, profile: Profile) -> None:
        """Save a profile."""
        profile_file = self.profiles_dir / f"{profile.name}.yaml"
        profile.save(profile_file)
    
    def delete_profile(self, name: str) -> bool:
        """Delete a profile."""
        profile_file = self.profiles_dir / f"{name}.yaml"
        if profile_file.exists():
            profile_file.unlink()
            return True
        return False
    
    def profile_exists(self, name: str) -> bool:
        """Check if a profile exists."""
        profile_file = self.profiles_dir / f"{name}.yaml"
        return profile_file.exists()