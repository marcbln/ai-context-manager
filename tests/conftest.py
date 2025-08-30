"""Test configuration and fixtures for AI Context Manager."""
import json
import tempfile
from pathlib import Path
from typing import Dict, Any

import pytest

from ai_context_manager.core.profile import Profile


@pytest.fixture
def temp_dir() -> Path:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_profile_data() -> Dict[str, Any]:
    """Provide sample profile data for testing."""
    return {
        "name": "test-profile",
        "description": "Test profile for unit tests",
        "include_patterns": ["*.py", "*.md"],
        "exclude_patterns": ["*.pyc", "__pycache__/*", ".git/*"],
        "max_file_size": 1024 * 1024,  # 1MB
        "max_total_size": 10 * 1024 * 1024,  # 10MB
        "include_binary": False,
        "output_format": "markdown",
        "custom_metadata": {"test": True, "version": "1.0.0"},
    }


@pytest.fixture
def sample_profile(sample_profile_data: Dict[str, Any]) -> Profile:
    """Create a sample Profile instance."""
    return Profile(**sample_profile_data)


@pytest.fixture
def profile_file(temp_dir: Path, sample_profile_data: Dict[str, Any]) -> Path:
    """Create a temporary profile file."""
    profile_path = temp_dir / "test-profile.json"
    with open(profile_path, "w") as f:
        json.dump(sample_profile_data, f, indent=2)
    return profile_path


@pytest.fixture
def sample_files(temp_dir: Path) -> Dict[str, Path]:
    """Create sample files for testing."""
    files = {}
    
    # Create Python files
    files["main_py"] = temp_dir / "main.py"
    files["main_py"].write_text('print("Hello, World!")\n')
    
    files["utils_py"] = temp_dir / "utils.py"
    files["utils_py"].write_text('def helper():\n    return "helper"\n')
    
    # Create markdown files
    files["readme_md"] = temp_dir / "README.md"
    files["readme_md"].write_text("# Test Project\n\nThis is a test.")
    
    # Create binary file
    files["binary_file"] = temp_dir / "data.bin"
    files["binary_file"].write_bytes(b"\x00\x01\x02\x03")
    
    # Create gitignore-style patterns
    files["gitignore"] = temp_dir / ".gitignore"
    files["gitignore"].write_text("*.pyc\n__pycache__/\n")
    
    # Create nested directory structure
    nested_dir = temp_dir / "src" / "package"
    nested_dir.mkdir(parents=True)
    files["nested_py"] = nested_dir / "module.py"
    files["nested_py"].write_text('def nested_func():\n    pass\n')
    
    # Create large file
    files["large_file"] = temp_dir / "large.txt"
    files["large_file"].write_text("x" * 2000)  # 2KB file
    
    return files


@pytest.fixture
def gitignore_content() -> str:
    """Provide sample .gitignore content."""
    return """# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# pyenv
.python-version

# celery beat schedule file
celerybeat-schedule

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/
"""