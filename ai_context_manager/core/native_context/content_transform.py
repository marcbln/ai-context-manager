"""Content transformation for compression and optimization."""
import ast
import re
from pathlib import Path
from typing import Optional

from .models import TransformOptions


class ContentTransformer:
    """Transforms content for compression and optimization."""
    
    def transform(self, text: str, file_path: str, opts: TransformOptions) -> str:
        """Transform content based on options."""
        if not opts.compress:
            return text.strip()
        
        try:
            file_ext = Path(file_path).suffix.lower()
            
            # Python-specific compression using AST
            if file_ext == ".py":
                return self._compress_python(text)
            
            # Generic compression for other file types
            return self._compress_generic(text)
        
        except Exception:
            # Fallback: return stripped original text on any error
            return text.strip()
    
    def _compress_python(self, text: str) -> str:
        """Compress Python code using AST to extract structure."""
        try:
            tree = ast.parse(text)
            lines = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    docstring = ast.get_docstring(node)
                    lines.append(f"class {node.name}:")
                    if docstring:
                        lines.append(f'    """{docstring}"""')
                    lines.append("")
                
                elif isinstance(node, ast.FunctionDef):
                    # Get function signature
                    args = []
                    for arg in node.args.args:
                        args.append(arg.arg)
                    
                    signature = f"def {node.name}({', '.join(args)})"
                    if node.returns:
                        signature += " -> ..."
                    
                    lines.append(signature)
                    
                    docstring = ast.get_docstring(node)
                    if docstring:
                        lines.append(f'    """{docstring}"""')
                    lines.append("")
            
            return "\n".join(lines).strip()
        
        except Exception:
            return self._compress_generic(text)
    
    def _compress_generic(self, text: str) -> str:
        """Generic compression for non-Python files."""
        lines = text.split("\n")
        compressed_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Skip empty lines
            if not stripped:
                continue
            
            # Skip common comment patterns
            if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*") or stripped.startswith("*/"):
                continue
            
            # Remove excessive whitespace within lines
            compressed_line = re.sub(r"\s+", " ", stripped)
            compressed_lines.append(compressed_line)
        
        return "\n".join(compressed_lines)
