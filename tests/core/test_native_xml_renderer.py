"""Tests for native XML renderer."""
from ai_context_manager.core.native_context.models import ContextFile, ContextRenderInput
from ai_context_manager.core.native_context.xml_renderer import XmlContextRenderer


def test_xml_renderer_basic():
    """Test basic XML rendering functionality."""
    renderer = XmlContextRenderer()
    
    payload = ContextRenderInput(
        generation_header="Test header",
        tree_string="test/\n├── file.py",
        files=[
            ContextFile(path="test/file.py", content="print('hello')")
        ]
    )
    
    result = renderer.render(payload)
    
    assert "<repomix>" in result
    assert "<file_summary>Test header</file_summary>" in result
    assert "<directory_structure>test/\n├── file.py</directory_structure>" in result
    assert '<file path="test/file.py">' in result
    assert "print('hello')" in result
    assert "</repomix>" in result


def test_xml_renderer_empty():
    """Test XML rendering with empty payload."""
    renderer = XmlContextRenderer()
    
    payload = ContextRenderInput(
        generation_header="",
        tree_string="",
        files=[],
        include_summary=False,
        include_tree=False,
        include_files=False
    )
    
    result = renderer.render(payload)
    
    assert "<repomix>" in result
    assert "</repomix>" in result
    assert "<file_summary>" not in result
    assert "<directory_structure>" not in result
    assert "<files>" not in result


def test_xml_renderer_escaping():
    """Test XML escaping of special characters."""
    renderer = XmlContextRenderer()
    
    payload = ContextRenderInput(
        generation_header="Header with <special> & characters",
        tree_string="",
        files=[
            ContextFile(path="test.xml", content='Content with "quotes" & <tags>')
        ]
    )
    
    result = renderer.render(payload)
    
    # Should be properly escaped
    assert "&lt;" in result or "&gt;" in result or "&amp;" in result
    assert "Content with" in result
