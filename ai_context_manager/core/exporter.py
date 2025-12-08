"""Export functionality for AI Context Manager."""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any
import datetime

from ai_context_manager.core.selection import Selection
from ai_context_manager.utils.file_utils import get_file_info
from ai_context_manager.utils.token_counter import count_tokens


class ContextExporter:
    """Handles exporting selected files to various formats for AI context."""
    
    def __init__(self, selection: Selection):
        """Initialize exporter with a selection object."""
        self.selection = selection
    
    def export_to_file(
        self,
        output_path: Path,
        format: str = "markdown",
    ) -> Dict[str, Any]:
        """Export selected files to the specified format."""
        
        # 1. Resolve files using the simplified logic
        files = self.selection.resolve_all_files()
        
        if not files:
            return {
                "success": False,
                "message": "No files found in selection",
                "files": [],
                "total_tokens": 0,
            }
        
        # 2. Get summary information
        summary = self._get_summary(files)
        
        # 3. Generate export content based on format
        if format.lower() == "json":
            content = self._export_json(files, summary)
        elif format.lower() == "xml":
            content = self._export_xml(files, summary)
        elif format.lower() == "yaml":
            content = self._export_yaml(files, summary)
        else:  # markdown
            content = self._export_markdown(files, summary)
        
        # 4. Write to file
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding='utf-8')
            
            # Count tokens in the exported content
            total_tokens = count_tokens(content)
            
            return {
                "success": True,
                "message": f"Successfully exported {len(files)} files to {output_path}",
                "files": [str(f) for f in files],
                "total_size_human": summary["total_size_human"],
                "total_tokens": total_tokens,
                "output_path": str(output_path),
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to export: {str(e)}",
                "files": [],
                "total_tokens": 0,
            }
    
    def _get_summary(self, files: List[Path]) -> Dict[str, Any]:
        """Get summary statistics for selected files."""
        total_size = 0
        total_lines = 0
        languages = {}
        
        for file_path in files:
            info = get_file_info(file_path)
            total_size += info["size"]
            total_lines += info["lines"]
            
            ext = file_path.suffix.lower()
            if ext not in languages:
                languages[ext] = 0
            languages[ext] += 1
            
        return {
            "total_files": len(files),
            "total_size": total_size,
            "total_size_human": self._format_size(total_size),
            "total_lines": total_lines,
            "languages": languages,
        }

    def _format_size(self, size_bytes: int) -> str:
        if size_bytes == 0: return "0 B"
        units = ["B", "KB", "MB", "GB"]
        size = float(size_bytes)
        idx = 0
        while size >= 1024 and idx < len(units) - 1:
            size /= 1024
            idx += 1
        return f"{size:.1f} {units[idx]}"

    def _export_markdown(self, files: List[Path], summary: Dict[str, Any]) -> str:
        lines = []
        lines.append("# AI Context Export")
        lines.append(f"Generated on: {datetime.datetime.now().isoformat()}")
        lines.append("")
        lines.append("## Summary")
        lines.append(f"- **Total Files**: {summary['total_files']}")
        lines.append(f"- **Total Size**: {summary['total_size_human']}")
        lines.append("")
        lines.append("## File Contents")
        lines.append("")
        
        for file_path in files:
            try:
                try:
                    display_path = file_path.relative_to(self.selection.base_path)
                except ValueError:
                    display_path = file_path

                content = file_path.read_text(encoding='utf-8', errors='replace')
                ext = file_path.suffix.lstrip('.') or 'txt'
                
                lines.append(f"### {display_path}")
                lines.append(f"```{ext}")
                lines.append(content)
                lines.append("```")
                lines.append("")
            except Exception as e:
                lines.append(f"### {file_path} (Error: {e})")
                lines.append("")
        return "\n".join(lines)

    def _export_json(self, files: List[Path], summary: Dict[str, Any]) -> str:
        export_data = {
            "metadata": {"generated_at": datetime.datetime.now().isoformat(), "summary": summary},
            "files": []
        }
        for file_path in files:
            try:
                try:
                    rel_path = str(file_path.relative_to(self.selection.base_path))
                except ValueError:
                    rel_path = str(file_path)
                content = file_path.read_text(encoding='utf-8', errors='replace')
                export_data["files"].append({"path": rel_path, "content": content})
            except Exception as e:
                export_data["files"].append({"path": str(file_path), "error": str(e)})
        return json.dumps(export_data, indent=2, ensure_ascii=False)

    def _export_xml(self, files: List[Path], summary: Dict[str, Any]) -> str:
        root = ET.Element("ai_context_export")
        ET.SubElement(root, "metadata").text = datetime.datetime.now().isoformat()
        files_elem = ET.SubElement(root, "files")
        for file_path in files:
            f_elem = ET.SubElement(files_elem, "file")
            try:
                try:
                    rel_path = str(file_path.relative_to(self.selection.base_path))
                except ValueError:
                    rel_path = str(file_path)
                f_elem.set("path", rel_path)
                f_elem.text = file_path.read_text(encoding='utf-8', errors='replace')
            except Exception as e:
                f_elem.set("error", str(e))
        return ET.tostring(root, encoding='unicode')

    def _export_yaml(self, files: List[Path], summary: Dict[str, Any]) -> str:
        import yaml
        data = {"metadata": {"generated": datetime.datetime.now().isoformat()}, "files": []}
        for file_path in files:
            try:
                try:
                    rel_path = str(file_path.relative_to(self.selection.base_path))
                except ValueError:
                    rel_path = str(file_path)
                content = file_path.read_text(encoding='utf-8', errors='replace')
                data["files"].append({"path": rel_path, "content": content})
            except Exception:
                pass
        return yaml.dump(data, sort_keys=False)