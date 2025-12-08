"""
Simple data model for handling file selections.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import List
import yaml

@dataclass
class Selection:
    base_path: Path
    include_paths: List[Path]

    @classmethod
    def load(cls, yaml_path: Path) -> 'Selection':
        """Load selection from a YAML file."""
        if not yaml_path.exists():
            raise FileNotFoundError(f"Selection file not found: {yaml_path}")

        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        
        # Resolve base path
        raw_base = data.get('basePath')
        if raw_base:
            base = Path(raw_base).resolve()
        else:
            base = yaml_path.parent.resolve()
        
        # Load the unified list. 
        # Support legacy 'files'/'folders' for backward compat if needed, but prefer 'include'.
        raw_includes = data.get('include', [])
        
        # Merge legacy keys if they exist
        raw_includes.extend(data.get('files', []))
        raw_includes.extend(data.get('folders', []))

        # Convert to Path objects relative to base
        include_paths = [base / p for p in raw_includes]
        
        return cls(base_path=base, include_paths=include_paths)

    def resolve_all_files(self) -> List[Path]:
        """
        Flatten the selection into a distinct list of files.
        Checks filesystem to determine if a path is a file or directory.
        """
        final_list = []
        
        for path in self.include_paths:
            if not path.exists():
                continue

            if path.is_file():
                final_list.append(path)
            elif path.is_dir():
                # Recursively add all files in the directory
                for f in path.rglob("*"):
                    if f.is_file():
                        final_list.append(f)
                        
        # Deduplicate and sort
        return sorted(list(set(final_list)))
