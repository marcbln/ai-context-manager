"""Top-level package for AI Context Manager."""
from .cli import cli
from .commands.profile_cmd import create_profile
from .utils.file_utils import get_file_size

__all__ = ['cli', 'create_profile', 'get_file_size']