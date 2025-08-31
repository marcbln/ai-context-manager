"""Pytest configuration and fixtures."""

import tempfile
import json
from pathlib import Path
import pytest

from ai_context_manager.config import Config


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def temp_config_dir(temp_dir):
    """Create a temporary configuration directory."""
    config_dir = temp_dir / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


@pytest.fixture
def temp_project_dir(temp_dir):
    """Create a temporary project directory with sample files."""
    project_dir = temp_dir / "project"
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Create sample Python files
    (project_dir / "main.py").write_text("""
def hello():
    print("Hello, World!")

if __name__ == "__main__":
    hello()
""")
    
    (project_dir / "utils.py").write_text("""
import os

def get_file_size(filepath):
    return os.path.getsize(filepath)

def list_files(directory):
    return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
""")
    
    # Create a subdirectory
    subdir = project_dir / "subdir"
    subdir.mkdir()
    (subdir / "module.py").write_text("""
class Calculator:
    def add(self, a, b):
        return a + b
    
    def multiply(self, a, b):
        return a * b
""")
    
    # Create some files to be excluded
    (project_dir / "temp.pyc").write_text("compiled python bytecode")
    (project_dir / "__pycache__").mkdir()
    (project_dir / "__pycache__" / "main.cpython-39.pyc").write_text("compiled python bytecode")
    
    # Create a README
    (project_dir / "README.md").write_text("""
# Test Project

This is a test project for testing the AI Context Manager.

## Features
- Python files
- Subdirectories
- Various file types
""")
    
    return project_dir


@pytest.fixture
def sample_config():
    """Create a sample configuration dictionary."""
    return {
        "name": "test-profile",
        "include_patterns": ["*.py", "*.js", "*.md"],
        "exclude_patterns": ["*.pyc", "__pycache__", "*.log"],
        "max_file_size": 1024,
        "include_binary": False,
        "encoding": "utf-8"
    }


@pytest.fixture
def config_with_profiles(temp_config_dir):
    """Create a Config instance with some pre-defined profiles."""
    config = Config(temp_config_dir)
    
    # Create default profile
    config.create_profile("default")
    
    # Create python profile
    config.create_profile("python", {
        "name": "python",
        "include_patterns": ["*.py"],
        "exclude_patterns": ["*.pyc", "__pycache__", "*.egg-info"],
        "max_file_size": 2048
    })
    
    # Create web profile
    config.create_profile("web", {
        "name": "web",
        "include_patterns": ["*.html", "*.css", "*.js", "*.py"],
        "exclude_patterns": ["*.pyc", "__pycache__", "node_modules", "*.min.js"],
        "max_file_size": 1024
    })
    
    return config


@pytest.fixture
def large_project_dir(temp_dir):
    """Create a larger project directory with nested structure."""
    project_dir = temp_dir / "large_project"
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Create nested directory structure
    dirs = [
        "src",
        "src/core",
        "src/utils",
        "tests",
        "docs",
        "examples",
        "data"
    ]
    
    for dir_path in dirs:
        (project_dir / dir_path).mkdir(parents=True, exist_ok=True)
    
    # Create multiple Python files
    files = [
        ("src/__init__.py", ""),
        ("src/core/__init__.py", ""),
        ("src/core/main.py", """
class MainApp:
    def __init__(self):
        self.name = "Large Project"
    
    def run(self):
        print(f"Running {self.name}")
"""),
        ("src/core/config.py", """
import json

class Config:
    def __init__(self, config_file):
        with open(config_file) as f:
            self.config = json.load(f)
    
    def get(self, key, default=None):
        return self.config.get(key, default)
"""),
        ("src/utils/__init__.py", ""),
        ("src/utils/helpers.py", """
import os
import hashlib

def hash_file(filepath):
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def get_all_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            yield os.path.join(root, file)
"""),
        ("tests/__init__.py", ""),
        ("tests/test_main.py", """
import unittest
from src.core.main import MainApp

class TestMainApp(unittest.TestCase):
    def test_init(self):
        app = MainApp()
        self.assertEqual(app.name, "Large Project")
"""),
        ("tests/test_config.py", """
import unittest
import tempfile
import json
from src.core.config import Config

class TestConfig(unittest.TestCase):
    def test_config_loading(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as f:
            json.dump({"test": "value"}, f)
            f.flush()
            config = Config(f.name)
            self.assertEqual(config.get("test"), "value")
"""),
        ("docs/README.md", """
# Large Project Documentation

This is a comprehensive test project with multiple files and directories.
"""),
        ("examples/example1.py", """
from src.core.main import MainApp

if __name__ == "__main__":
    app = MainApp()
    app.run()
"""),
        ("data/sample.json", """
{
    "name": "sample data",
    "items": [1, 2, 3, 4, 5]
}
""")
    ]
    
    for file_path, content in files:
        full_path = project_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
    
    # Create some binary files
    (project_dir / "data" / "sample.bin").write_bytes(b'\x00\x01\x02\x03\x04\x05')
    
    return project_dir


@pytest.fixture
def config_file_json(temp_dir):
    """Create a temporary config file in JSON format."""
    config_file = temp_dir / "config.json"
    
    config_data = {
        "profile": "test",
        "format": "json",
        "max_tokens": 5000,
        "include_patterns": ["*.py", "*.md"],
        "exclude_patterns": ["*.pyc", "__pycache__"],
        "output_file": "output.json"
    }
    
    with open(config_file, 'w') as f:
        json.dump(config_data, f, indent=2)
    
    return config_file


@pytest.fixture
def config_file_yaml(temp_dir):
    """Create a temporary config file in YAML format."""
    try:
        import yaml
    except ImportError:
        pytest.skip("PyYAML not installed")
    
    config_file = temp_dir / "config.yaml"
    
    config_data = {
        "profile": "test",
        "format": "yaml",
        "max_tokens": 5000,
        "include_patterns": ["*.py", "*.md"],
        "exclude_patterns": ["*.pyc", "__pycache__"],
        "output_file": "output.yaml"
    }
    
    with open(config_file, 'w') as f:
        yaml.dump(config_data, f)
    
    return config_file


@pytest.fixture
def mock_token_counter():
    """Create a mock token counter for testing."""
    class MockTokenCounter:
        def count_tokens(self, text):
            # Simple mock: count words as tokens
            return len(text.split())
        
        def count_tokens_in_file(self, filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    return self.count_tokens(content)
            except (IOError, UnicodeDecodeError):
                return 0
    
    return MockTokenCounter()


@pytest.fixture
def mock_file_selector():
    """Create a mock file selector for testing."""
    class MockFileSelector:
        def __init__(self, root_path, profile=None):
            self.root_path = Path(root_path)
            self.profile = profile or {}
            self.selected_files = []
        
        def select_files(self):
            # Simple mock: select all Python files
            self.selected_files = list(self.root_path.rglob("*.py"))
            return self.selected_files
        
        def get_file_info(self, filepath):
            path = Path(filepath)
            return {
                "path": str(path.relative_to(self.root_path)),
                "size": path.stat().st_size,
                "type": path.suffix,
                "encoding": "utf-8"
            }
    
    return MockFileSelector


@pytest.fixture
def mock_exporter():
    """Create a mock exporter for testing."""
    class MockExporter:
        def __init__(self, format_type="text"):
            self.format_type = format_type
        
        def export(self, files_data, output_file=None):
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(f"Mock export in {self.format_type} format\n")
                    f.write(f"Files: {len(files_data)}\n")
            return f"Mock export in {self.format_type} format with {len(files_data)} files"
    
    return MockExporter


@pytest.fixture(autouse=True)
def clean_environment():
    """Clean up environment variables that might affect tests."""
    import os
    
    # Store original values
    original_env = {}
    env_vars = ['AI_CONTEXT_CONFIG_DIR', 'AI_CONTEXT_PROFILE', 'AI_CONTEXT_FORMAT']
    
    for var in env_vars:
        original_env[var] = os.environ.get(var)
        if var in os.environ:
            del os.environ[var]
    
    yield
    
    # Restore original values
    for var, value in original_env.items():
        if value is not None:
            os.environ[var] = value
        elif var in os.environ:
            del os.environ[var]