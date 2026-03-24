"""Data models for native context generation."""
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class ContextFile:
    """Represents a single file in the context."""
    path: str
    content: str


@dataclass(frozen=True)
class ContextRenderInput:
    """Input payload for context rendering."""
    generation_header: str
    tree_string: str
    files: List[ContextFile]
    include_summary: bool = True
    include_tree: bool = True
    include_files: bool = True


@dataclass(frozen=True)
class TransformOptions:
    """Options for content transformation."""
    compress: bool = False
