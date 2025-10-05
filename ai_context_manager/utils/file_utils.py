"""File utilities for AI Context Manager."""
import fnmatch
import mimetypes
from pathlib import Path
from typing import List, Set, Tuple


def is_binary_file(file_path: Path) -> bool:
    """Check if a file is binary based on its content."""
    try:
        with file_path.open('rb') as f:
            chunk = f.read(1024)
            return b'\0' in chunk
    except (IOError, OSError):
        return True


def is_text_file(file_path: Path) -> bool:
    """Check if a file is a text file."""
    return not is_binary_file(file_path)


def get_file_mime_type(file_path: Path) -> str:
    """Get the MIME type of a file."""
    mime_type, _ = mimetypes.guess_type(str(file_path))
    return mime_type or "application/octet-stream"


def matches_pattern(file_path: Path, patterns: List[str]) -> bool:
    """Check if a file path matches any of the given patterns."""
    path_str = str(file_path)
    for pattern in patterns:
        if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(file_path.name, pattern):
            return True
    return False


def collect_files(
    root_path: Path,
    include_patterns: List[str] = None,
    exclude_patterns: List[str] = None,
    max_file_size: int = 102400,
    include_binary: bool = False
) -> List[Path]:
    """Collect files based on include/exclude patterns and size limits."""
    if include_patterns is None:
        include_patterns = ["*"]
    if exclude_patterns is None:
        exclude_patterns = []
    
    files = []
    
    try:
        for file_path in root_path.rglob("*"):
            if not file_path.is_file():
                continue
            
            # Check file size
            try:
                if file_path.stat().st_size > max_file_size:
                    continue
            except (OSError, IOError):
                continue
            
            # Check exclude patterns
            if exclude_patterns and matches_pattern(file_path, exclude_patterns):
                continue
            
            # Check include patterns
            if not matches_pattern(file_path, include_patterns):
                continue
            
            # Check binary files
            if not include_binary and is_binary_file(file_path):
                continue
            
            files.append(file_path)
    
    except (OSError, IOError) as e:
        # Handle permission errors or other filesystem issues
        pass
    
    return sorted(files)


def read_file_content(file_path: Path, max_chars: int = None) -> str:
    """Read the content of a text file."""
    try:
        # Return empty for binary files to avoid decoding issues
        if is_binary_file(file_path):
            return ""
        with file_path.open('r', encoding='utf-8', errors='ignore') as f:
            if max_chars:
                return f.read(max_chars)
            return f.read()
    except (IOError, OSError, UnicodeDecodeError):
        return ""


def get_file_size(file_path: Path) -> int:
    """Get file size in bytes; return 0 if file doesn't exist or is inaccessible."""
    try:
        return file_path.stat().st_size
    except (OSError, IOError):
        return 0


def format_file_size(size_bytes: int) -> str:
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


def get_file_info(file_path: Path) -> dict:
    """Get comprehensive file information."""
    try:
        stat = file_path.stat()
        content = read_file_content(file_path)
        lines = len(content.splitlines()) if content is not None else 0
        
        return {
            "path": str(file_path),
            "name": file_path.name,
            "extension": file_path.suffix,
            "size": stat.st_size,
            "size_human": format_file_size(stat.st_size),
            "modified": stat.st_mtime,
            "created": stat.st_ctime,
            "is_binary": is_binary_file(file_path),
            "is_text": is_text_file(file_path),
            "mime_type": get_file_mime_type(file_path),
            "lines": lines,
            "exists": True,
        }
    except (OSError, IOError):
        return {
            "path": str(file_path),
            "name": file_path.name,
            "extension": file_path.suffix,
            "size": 0,
            "size_human": "0 B",
            "modified": 0,
            "created": 0,
            "is_binary": True,
            "is_text": False,
            "mime_type": "application/octet-stream",
            "lines": 0,
            "exists": False,
        }


def get_language_from_extension(file_path: Path) -> str:
    """Determine programming language from file extension."""
    extension = file_path.suffix.lower()
    
    from ai_context_manager.config import LANGUAGE_EXTENSIONS
    
    for language, extensions in LANGUAGE_EXTENSIONS.items():
        if extension in extensions:
            return language
    
    return "unknown"


def should_include_file(
    file_path: Path,
    include_patterns: List[str],
    exclude_patterns: List[str],
    max_file_size: int,
    include_binary: bool
) -> bool:
    """Determine if a file should be included based on all criteria."""
    try:
        # Check if file exists and is readable
        if not file_path.exists() or not file_path.is_file():
            return False
        
        # Check file size
        if file_path.stat().st_size > max_file_size:
            return False
        
        # Check exclude patterns
        if exclude_patterns and matches_pattern(file_path, exclude_patterns):
            return False
        
        # Check include patterns
        if include_patterns is None:
            include_patterns = ["*"]
        if not matches_pattern(file_path, include_patterns):
            return False
        
        # Check binary files
        if not include_binary and is_binary_file(file_path):
            return False
        
        return True
    
    except (OSError, IOError):
        return False


def get_project_structure(root_path: Path, max_depth: int = 3) -> List[Tuple[str, int]]:
    """Get project directory structure up to a certain depth."""
    structure = []
    
    try:
        for path in root_path.rglob("*"):
            if not path.is_file():
                continue
            
            try:
                relative_path = path.relative_to(root_path)
                depth = len(relative_path.parts) - 1
                
                if depth <= max_depth:
                    structure.append((str(relative_path), depth))
            except ValueError:
                continue
    
    except (OSError, IOError):
        pass
    
    return sorted(structure)


def filter_files_by_language(
    files: List[Path],
    languages: List[str]
) -> List[Path]:
    """Filter files by programming language."""
    if not languages:
        return files
    
    from ai_context_manager.config import LANGUAGE_EXTENSIONS
    
    filtered_files = []
    for file_path in files:
        extension = file_path.suffix.lower()
        for language in languages:
            if extension in LANGUAGE_EXTENSIONS.get(language, []):
                filtered_files.append(file_path)
                break
    
    return filtered_files


def filter_files_by_patterns(
    files: List[Path],
    include_patterns: List[str] = None,
    exclude_patterns: List[str] = None
) -> List[Path]:
    """Filter files by include/exclude patterns."""
    if include_patterns is None:
        include_patterns = ["*"]
    if exclude_patterns is None:
        exclude_patterns = []
    
    filtered_files = []
    
    for file_path in files:
        # Check exclude patterns
        if exclude_patterns and matches_pattern(file_path, exclude_patterns):
            continue
        
        # Check include patterns
        if not matches_pattern(file_path, include_patterns):
            continue
        
        filtered_files.append(file_path)
    
    return filtered_files