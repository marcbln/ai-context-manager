"""Tests for content transformation."""
from ai_context_manager.core.native_context.content_transform import ContentTransformer
from ai_context_manager.core.native_context.models import TransformOptions


def test_transform_no_compression():
    """Test that without compression, content is just stripped."""
    transformer = ContentTransformer()
    
    text = "  hello world  \n\n  "
    opts = TransformOptions(compress=False)
    
    result = transformer.transform(text, "test.txt", opts)
    
    assert result == "hello world"


def test_transform_python_compression():
    """Test Python-specific compression."""
    transformer = ContentTransformer()
    
    python_code = '''
"""Module docstring."""
import os

class MyClass:
    """Class docstring."""
    
    def method1(self, arg1, arg2):
        """Method docstring."""
        return arg1 + arg2
    
    def method2(self):
        # This is a comment
        print("hello")
        return 42

# Another comment
def standalone_function():
    pass
'''
    
    opts = TransformOptions(compress=True)
    result = transformer.transform(python_code, "test.py", opts)
    
    # Should contain class and function signatures
    assert "class MyClass:" in result
    assert "def method1(self, arg1, arg2):" in result
    assert "def method2(self):" in result
    assert "def standalone_function():" in result
    
    # Should contain docstrings
    assert '"""Module docstring."""' in result
    assert '"""Class docstring."""' in result
    assert '"""Method docstring."""' in result
    
    # Should not contain comments or implementation details
    assert "# This is a comment" not in result
    assert "print("hello")" not in result
    assert "return 42" not in result


def test_transform_generic_compression():
    """Test generic compression for non-Python files."""
    transformer = ContentTransformer()
    
    text = '''
This is a line
# This is a comment
Another line
// Another comment
    Whitespace-heavy line    


'''
    
    opts = TransformOptions(compress=True)
    result = transformer.transform(text, "test.txt", opts)
    
    # Should contain non-comment lines
    assert "This is a line" in result
    assert "Another line" in result
    assert "Whitespace-heavy line" in result
    
    # Should not contain comments
    assert "# This is a comment" not in result
    assert "// Another comment" not in result
    
    # Should not contain empty lines
    assert result.count("\n\n") == 0


def test_transform_error_fallback():
    """Test that transform errors fall back to stripped text."""
    transformer = ContentTransformer()
    
    # Create a malformed Python file that will fail AST parsing
    malformed_python = "def broken_syntax(\n    # Missing closing parenthesis"
    
    opts = TransformOptions(compress=True)
    result = transformer.transform(malformed_python, "test.py", opts)
    
    # Should fall back to generic compression
    assert "def broken_syntax(" in result
