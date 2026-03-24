"""File loading and collection for native context generation."""
import os
from pathlib import Path
from typing import List

from .models import ContextFile


class FileLoader:
    """Loads and collects files based on include patterns."""
    
    def load(self, execution_root: Path, include_patterns: List[str]) -> List[ContextFile]:
        """Load files matching the include patterns."""
        files = []
        
        for pattern in include_patterns:
            # Handle directory patterns (ending with /**)
            if pattern.endswith("/**"):
                dir_path = execution_root / pattern[:-3]
                if dir_path.exists() and dir_path.is_dir():
                    for file_path in dir_path.rglob("*"):
                        if file_path.is_file():
                            rel_path = file_path.relative_to(execution_root)
                            content = self._read_file_safely(file_path)
                            if content is not None:
                                files.append(ContextFile(
                                    path=str(rel_path),
                                    content=content
                                ))
            else:
                # Handle specific file patterns
                file_path = execution_root / pattern
                if file_path.exists() and file_path.is_file():
                    rel_path = file_path.relative_to(execution_root)
                    content = self._read_file_safely(file_path)
                    if content is not None:
                        files.append(ContextFile(
                            path=str(rel_path),
                            content=content
                        ))
        
        # Remove duplicates and sort by path
        unique_files = {f.path: f for f in files}
        return [unique_files[path] for path in sorted(unique_files.keys())]
    
    def _read_file_safely(self, file_path: Path) -> str | None:
        """Safely read file content with proper encoding handling."""
        try:
            # Try UTF-8 first
            return file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                # Fallback to latin-1 for binary files
                return file_path.read_text(encoding="latin-1")
            except Exception:
                # Skip files that can't be read
                return None
        except Exception:
            # Skip files that can't be read
            return None
