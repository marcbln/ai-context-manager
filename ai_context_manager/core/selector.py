"""File selection logic for AI Context Manager."""

import pathspec
from pathlib import Path
from typing import List, Set, Optional, Dict, Any
import logging

from ai_context_manager.core.profile import Profile, PathEntry
from ai_context_manager.utils.file_utils import (
    is_binary_file,
    is_text_file,
    get_file_info,
    should_include_file,
    get_language_from_extension,
    matches_pattern,
)

logger = logging.getLogger(__name__)


class Selector:
    """Handles file selection based on profiles and patterns."""
    
    def __init__(self, profile: Profile):
        """Initialize selector with a profile."""
        self.profile = profile
        self._spec = None
        self._build_pathspec()
    
    def _build_pathspec(self) -> None:
        """Build pathspec from exclude patterns."""
        if self.profile.exclude_patterns:
            self._spec = pathspec.PathSpec.from_lines(
                'gitwildmatch', 
                self.profile.exclude_patterns
            )
        else:
            self._spec = None
    
    def _is_excluded(self, file_path: Path) -> bool:
        """Check if a file should be excluded based on patterns."""
        if not self._spec:
            return False
        
        # Convert to relative path from base_path if available
        if self.profile.base_path:
            try:
                rel_path = file_path.relative_to(self.profile.base_path)
                return self._spec.match_file(str(rel_path))
            except ValueError:
                # File is not within base_path, exclude it
                return True
        
        # Use absolute path
        return self._spec.match_file(str(file_path))
    
    def _collect_files_from_entry(self, entry: PathEntry) -> List[Path]:
        """Collect files from a single PathEntry."""
        files = []
        
        if not entry.path.exists():
            logger.warning(f"Path does not exist: {entry.path}")
            return files
        
        if entry.is_directory:
            if entry.recursive:
                # Collect all files recursively
                for file_path in entry.path.rglob("*"):
                    if file_path.is_file():
                        files.append(file_path)
            else:
                # Collect only files in the directory (non-recursive)
                for file_path in entry.path.iterdir():
                    if file_path.is_file():
                        files.append(file_path)
        else:
            # Single file
            if entry.path.is_file():
                files.append(entry.path)
        
        return files
    
    def get_all_files(self) -> List[Path]:
        """Get all files from all path entries in the profile."""
        all_files = []
        
        for entry in self.profile.paths:
            files = self._collect_files_from_entry(entry)
            all_files.extend(files)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_files = []
        for file_path in all_files:
            if file_path not in seen:
                seen.add(file_path)
                unique_files.append(file_path)
        
        return unique_files
    
    def filter_files(
        self,
        files: List[Path],
        max_file_size: int = 102400,
        include_binary: bool = False,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> List[Path]:
        """Filter files based on various criteria."""
        filtered = []
        
        # Use profile patterns if not provided
        if exclude_patterns is None:
            exclude_patterns = self.profile.exclude_patterns
        
        # Build combined exclude spec
        combined_exclude = []
        if exclude_patterns:
            combined_exclude.extend(exclude_patterns)
        
        exclude_spec = None
        if combined_exclude:
            exclude_spec = pathspec.PathSpec.from_lines('gitwildmatch', combined_exclude)
        
        for file_path in files:
            # Check if file exists
            if not file_path.exists() or not file_path.is_file():
                continue
            
            # Check exclude patterns
            if exclude_spec:
                rel_path = None
                if self.profile.base_path:
                    try:
                        rel_path = file_path.relative_to(self.profile.base_path)
                    except ValueError:
                        continue
                
                check_path = str(rel_path) if rel_path else str(file_path)
                if exclude_spec.match_file(check_path):
                    continue
            
            # Check include patterns
            if include_patterns:
                matched = False
                for pattern in include_patterns:
                    if matches_pattern(file_path, [pattern]):
                        matched = True
                        break
                if not matched:
                    continue
            
            # Check file size
            try:
                if file_path.stat().st_size > max_file_size:
                    continue
            except (OSError, IOError):
                continue
            
            # Check binary files
            if not include_binary and is_binary_file(file_path):
                continue
            
            filtered.append(file_path)
        
        return sorted(filtered)
    
    def select_files(
        self,
        max_file_size: int = 102400,
        include_binary: bool = False,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> List[Path]:
        """Select files based on profile configuration and additional filters."""
        # Get all files from profile paths
        all_files = self.get_all_files()
        
        # Apply filtering
        selected_files = self.filter_files(
            files=all_files,
            max_file_size=max_file_size,
            include_binary=include_binary,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
        )
        
        return selected_files
    
    def get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Get comprehensive information about a file."""
        return get_file_info(file_path)
    
    def get_files_by_language(self, files: List[Path], languages: List[str]) -> List[Path]:
        """Filter files by programming language."""
        if not languages:
            return files
        
        filtered = []
        for file_path in files:
            language = get_language_from_extension(file_path)
            if language in languages:
                filtered.append(file_path)
        
        return sorted(filtered)
    
    def get_summary(self, files: List[Path]) -> Dict[str, Any]:
        """Get summary statistics for selected files."""
        if not files:
            return {
                "total_files": 0,
                "total_size": 0,
                "total_lines": 0,
                "languages": {},
                "largest_file": None,
                "smallest_file": None,
            }
        
        total_size = 0
        total_lines = 0
        languages = {}
        largest_file = None
        smallest_file = None
        max_size = 0
        min_size = float('inf')
        
        for file_path in files:
            info = self.get_file_info(file_path)
            
            total_size += info["size"]
            total_lines += info["lines"]
            
            language = get_language_from_extension(file_path)
            if language not in languages:
                languages[language] = 0
            languages[language] += 1
            
            if info["size"] > max_size:
                max_size = info["size"]
                largest_file = {
                    "path": str(file_path),
                    "size": info["size"],
                    "size_human": info["size_human"]
                }
            
            if info["size"] < min_size:
                min_size = info["size"]
                smallest_file = {
                    "path": str(file_path),
                    "size": info["size"],
                    "size_human": info["size_human"]
                }
        
        return {
            "total_files": len(files),
            "total_size": total_size,
            "total_size_human": self._format_size(total_size),
            "total_lines": total_lines,
            "languages": languages,
            "largest_file": largest_file,
            "smallest_file": smallest_file,
        }
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes == 0:
            return "0 B"
        
        units = ["B", "KB", "MB", "GB", "TB"]
        size = float(size_bytes)
        unit_index = 0
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        else:
            return f"{size:.1f} {units[unit_index]}"
    
    def validate_profile(self) -> List[str]:
        """Validate the profile and return any issues found."""
        issues = []
        
        # Check if base path exists
        if self.profile.base_path and not self.profile.base_path.exists():
            issues.append(f"Base path does not exist: {self.profile.base_path}")
        
        # Check individual paths
        for entry in self.profile.paths:
            if not entry.path.exists():
                issues.append(f"Path does not exist: {entry.path}")
        
        # Check for duplicate paths
        seen = set()
        for entry in self.profile.paths:
            path_str = str(entry.path.resolve())
            if path_str in seen:
                issues.append(f"Duplicate path: {entry.path}")
            seen.add(path_str)
        
        return issues