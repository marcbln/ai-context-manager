"""Export functionality for AI Context Manager."""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional
import datetime

from ai_context_manager.core.profile import Profile, PathEntry
from ai_context_manager.core.selector import Selector
from ai_context_manager.utils.file_utils import get_file_info
from ai_context_manager.utils.token_counter import count_tokens


class ContextExporter:
    """Handles exporting selected files to various formats for AI context."""
    
    def __init__(self, profile: Profile):
        """Initialize exporter with a profile."""
        self.profile = profile
        self.selector = Selector(profile)
    
    def export_to_file(
        self,
        output_path: Path,
        format: str = "markdown",
        max_file_size: int = 102400,
        include_binary: bool = False,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Export selected files to the specified format."""
        # Select files based on criteria
        selected_files = self.selector.select_files(
            max_file_size=max_file_size,
            include_binary=include_binary,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
        )
        
        if not selected_files:
            return {
                "success": False,
                "message": "No files selected for export",
                "files": [],
                "total_size": 0,
                "total_tokens": 0,
            }
        
        # Get summary information
        summary = self.selector.get_summary(selected_files)
        
        # Generate export content based on format
        if format.lower() == "json":
            content = self._export_json(selected_files, summary)
        elif format.lower() == "xml":
            content = self._export_xml(selected_files, summary)
        elif format.lower() == "yaml":
            content = self._export_yaml(selected_files, summary)
        else:  # markdown
            content = self._export_markdown(selected_files, summary)
        
        # Write to file
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding='utf-8')
            
            # Count tokens in the exported content
            total_tokens = count_tokens(content)
            
            return {
                "success": True,
                "message": f"Successfully exported {len(selected_files)} files to {output_path}",
                "files": [str(f) for f in selected_files],
                "total_size": summary["total_size"],
                "total_size_human": summary["total_size_human"],
                "total_tokens": total_tokens,
                "output_path": str(output_path),
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to export: {str(e)}",
                "files": [],
                "total_size": 0,
                "total_tokens": 0,
            }
    
    def _export_markdown(self, files: List[Path], summary: Dict[str, Any]) -> str:
        """Export to markdown format."""
        lines = []
        
        # Header
        lines.append("# AI Context Export")
        lines.append(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append(f"Profile: {self.profile.name}")
        lines.append("")
        
        # Summary
        lines.append("## Summary")
        lines.append(f"- **Total Files**: {summary['total_files']}")
        lines.append(f"- **Total Size**: {summary['total_size_human']}")
        lines.append(f"- **Total Lines**: {summary['total_lines']:,}")
        lines.append(f"- **Languages**: {', '.join(summary['languages'].keys())}")
        lines.append("")
        
        # Directory structure
        lines.append("## Directory Structure")
        lines.append("```")
        tree_structure = self._generate_tree_structure(files)
        lines.extend(tree_structure)
        lines.append("```")
        lines.append("")
        
        # File contents
        lines.append("## File Contents")
        lines.append("")
        
        for file_path in files:
            try:
                content = file_path.read_text(encoding='utf-8')
                info = get_file_info(file_path)
                language = self._get_language_from_extension(file_path)
                
                lines.append(f"### {file_path}")
                lines.append(f"- **Size**: {info['size_human']}")
                lines.append(f"- **Lines**: {info['lines']:,}")
                if language:
                    lines.append(f"- **Language**: {language}")
                lines.append("")
                
                lines.append(f"```{language}")
                lines.append(content)
                lines.append("```")
                lines.append("")
                
            except Exception as e:
                lines.append(f"### {file_path}")
                lines.append(f"*Error reading file: {e}*")
                lines.append("")
        
        return "\n".join(lines)
    
    def _export_json(self, files: List[Path], summary: Dict[str, Any]) -> str:
        """Export to JSON format."""
        export_data = {
            "metadata": {
                "generated_at": datetime.datetime.now().isoformat(),
                "profile": self.profile.name,
                "summary": summary
            },
            "files": []
        }
        
        for file_path in files:
            try:
                content = file_path.read_text(encoding='utf-8')
                info = get_file_info(file_path)
                
                export_data["files"].append({
                    "path": str(file_path),
                    "size": info["size"],
                    "lines": info["lines"],
                    "language": self._get_language_from_extension(file_path),
                    "content": content
                })
                
            except Exception as e:
                export_data["files"].append({
                    "path": str(file_path),
                    "error": str(e)
                })
        
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    def _export_xml(self, files: List[Path], summary: Dict[str, Any]) -> str:
        """Export to XML format."""
        root = ET.Element("ai_context_export")
        
        # Metadata
        metadata = ET.SubElement(root, "metadata")
        ET.SubElement(metadata, "generated_at").text = datetime.datetime.now().isoformat()
        ET.SubElement(metadata, "profile").text = self.profile.name
        
        summary_elem = ET.SubElement(metadata, "summary")
        ET.SubElement(summary_elem, "total_files").text = str(summary["total_files"])
        ET.SubElement(summary_elem, "total_size").text = str(summary["total_size"])
        ET.SubElement(summary_elem, "total_lines").text = str(summary["total_lines"])
        
        languages = ET.SubElement(summary_elem, "languages")
        for lang, count in summary["languages"].items():
            lang_elem = ET.SubElement(languages, "language")
            lang_elem.set("name", lang)
            lang_elem.set("count", str(count))
        
        # Files
        files_elem = ET.SubElement(root, "files")
        
        for file_path in files:
            file_elem = ET.SubElement(files_elem, "file")
            file_elem.set("path", str(file_path))
            
            try:
                content = file_path.read_text(encoding='utf-8')
                info = get_file_info(file_path)
                
                ET.SubElement(file_elem, "size").text = str(info["size"])
                ET.SubElement(file_elem, "lines").text = str(info["lines"])
                ET.SubElement(file_elem, "language").text = self._get_language_from_extension(file_path)
                ET.SubElement(file_elem, "content").text = content
                
            except Exception as e:
                ET.SubElement(file_elem, "error").text = str(e)
        
        # Convert to string
        ET.indent(root, space="  ")
        return ET.tostring(root, encoding='unicode')
    
    def _export_yaml(self, files: List[Path], summary: Dict[str, Any]) -> str:
        """Export to YAML format."""
        try:
            import yaml
        except ImportError:
            raise ImportError("PyYAML is required for YAML export. Install with: pip install PyYAML")
        
        export_data = {
            "metadata": {
                "generated_at": datetime.datetime.now().isoformat(),
                "profile": self.profile.name,
                "total_files": summary["total_files"],
                "total_size": summary["total_size"],
                "total_lines": summary["total_lines"],
                "languages": summary["languages"],
            },
            "files": []
        }
        
        for file_path in files:
            try:
                content = file_path.read_text(encoding='utf-8')
                info = get_file_info(file_path)
                
                export_data["files"].append({
                    "path": str(file_path),
                    "size": info["size"],
                    "lines": info["lines"],
                    "language": self._get_language_from_extension(file_path),
                    "content": content
                })
                
            except Exception as e:
                export_data["files"].append({
                    "path": str(file_path),
                    "error": str(e)
                })
        
        return yaml.dump(export_data, default_flow_style=False, allow_unicode=True)
    
    def _generate_tree_structure(self, files: List[Path]) -> List[str]:
        """Generate a tree-like structure representation of files."""
        if not files:
            return []
        
        # Find common prefix
        common_prefix = Path(str(files[0]))
        for file_path in files[1:]:
            while not str(file_path).startswith(str(common_prefix)):
                common_prefix = common_prefix.parent
                if common_prefix == common_prefix.parent:
                    break
        
        tree_lines = []
        
        def build_tree(current_path: Path, prefix: str = "") -> None:
            """Recursively build tree structure."""
            try:
                items = sorted(current_path.iterdir()) if current_path.is_dir() else []
            except (PermissionError, OSError):
                return
            
            dirs = [item for item in items if item.is_dir()]
            files_in_dir = [item for item in items if item.is_file()]
            
            # Add directories
            for i, dir_path in enumerate(dirs):
                is_last = i == len(dirs) - 1 and not files_in_dir
                tree_lines.append(f"{prefix}{'└── ' if is_last else '├── '}{dir_path.name}/")
                
                if dir_path in [f.parent for f in files] or any(str(f).startswith(str(dir_path)) for f in files):
                    extension = "    " if is_last else "│   "
                    build_tree(dir_path, prefix + extension)
            
            # Add files
            for i, file_path in enumerate(files_in_dir):
                if file_path in files:  # Only include selected files
                    is_last = i == len(files_in_dir) - 1
                    tree_lines.append(f"{prefix}{'└── ' if is_last else '├── '}{file_path.name}")
        
        # Build tree from common prefix
        if common_prefix.is_file():
            tree_lines.append(str(common_prefix.name))
        else:
            tree_lines.append(str(common_prefix) + "/")
            build_tree(common_prefix, "")
        
        return tree_lines
    
    def _get_language_from_extension(self, file_path: Path) -> str:
        """Get programming language from file extension."""
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "jsx",
            ".tsx": "tsx",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".h": "c",
            ".hpp": "cpp",
            ".cs": "csharp",
            ".php": "php",
            ".rb": "ruby",
            ".go": "go",
            ".rs": "rust",
            ".swift": "swift",
            ".kt": "kotlin",
            ".scala": "scala",
            ".html": "html",
            ".css": "css",
            ".scss": "scss",
            ".sass": "sass",
            ".less": "less",
            ".json": "json",
            ".xml": "xml",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "toml",
            ".ini": "ini",
            ".cfg": "ini",
            ".conf": "conf",
            ".sh": "bash",
            ".bash": "bash",
            ".zsh": "zsh",
            ".fish": "fish",
            ".ps1": "powershell",
            ".sql": "sql",
            ".md": "markdown",
            ".dockerfile": "dockerfile",
            ".vue": "vue",
            ".svelte": "svelte",
        }
        
        ext = file_path.suffix.lower()
        return extension_map.get(ext, "")