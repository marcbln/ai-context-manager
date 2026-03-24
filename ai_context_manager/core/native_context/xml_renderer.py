"""XML renderer for Repomix-compatible output."""
import xml.etree.ElementTree as ET
from xml.dom import minidom

from .models import ContextRenderInput


class XmlContextRenderer:
    """Renders context as Repomix-compatible XML."""
    
    def render(self, payload: ContextRenderInput) -> str:
        """Render the context payload to XML string."""
        root = ET.Element("repomix")
        
        if payload.include_summary:
            summary = ET.SubElement(root, "file_summary")
            summary.text = payload.generation_header
        
        if payload.include_tree:
            tree = ET.SubElement(root, "directory_structure")
            tree.text = payload.tree_string
        
        if payload.include_files:
            files_el = ET.SubElement(root, "files")
            for item in payload.files:
                node = ET.SubElement(files_el, "file", {"path": item.path})
                node.text = item.content
        
        # Convert to pretty-printed XML
        rough_string = ET.tostring(root, encoding="unicode")
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")[23:]  # Remove XML declaration
