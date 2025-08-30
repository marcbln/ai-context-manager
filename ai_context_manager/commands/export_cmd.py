"""Export command for AI Context Manager."""
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional

import typer
import yaml
from typing_extensions import Annotated

from ai_context_manager.core.profile import Profile
from ai_context_manager.utils.file_utils import collect_files, format_file_size
from ai_context_manager.utils.token_counter import count_tokens

app = typer.Typer(help="Export code context for AI analysis")


@app.command("export")
def export_context(
    path: Annotated[Path, typer.Option("--path", "-p", help="Path to analyze")],
    output: Annotated[Optional[Path], typer.Option("--output", "-o", help="Output file path")] = None,
    format: Annotated[str, typer.Option("--format", "-f", help="Output format (json, markdown, xml, yaml)")] = "json",
    include: Annotated[Optional[str], typer.Option("--include", "-i", help="Include patterns (comma-separated)")] = None,
    exclude: Annotated[Optional[str], typer.Option("--exclude", "-e", help="Exclude patterns (comma-separated)")] = None,
    max_size: Annotated[int, typer.Option("--max-size", help="Maximum file size in bytes")] = 102400,
    binary: Annotated[bool, typer.Option("--binary/--no-binary", help="Include binary files")] = False,
    token_limit: Annotated[Optional[int], typer.Option("--token-limit", help="Maximum tokens to include")] = None,
    profile: Annotated[Optional[str], typer.Option("--profile", help="Profile name to use")] = None,
    profiles_dir: Annotated[Path, typer.Option("--profiles-dir", help="Directory containing profiles")] = Path.home() / ".ai-context-manager" / "profiles"
) -> None:
    """Export code context for AI analysis."""
    if not path.exists():
        typer.echo(f"Error: Path '{path}' does not exist", err=True)
        raise typer.Exit(1)

    # Load profile if specified
    profile_config = None
    if profile:
        profile_path = profiles_dir / f"{profile}.json"
        if not profile_path.exists():
            typer.echo(f"Error: Profile '{profile}' not found at {profile_path}", err=True)
            raise typer.Exit(1)
        
        try:
            profile_config = Profile.from_file(profile_path)
        except Exception as e:
            typer.echo(f"Error loading profile: {e}", err=True)
            raise typer.Exit(1)

    # Apply profile settings if available
    if profile_config:
        include_patterns = profile_config.include_patterns or ["*"]
        exclude_patterns = profile_config.exclude_patterns or []
        max_file_size = profile_config.max_file_size or max_size
        include_binary = profile_config.include_binary or binary
        output_format = profile_config.output_format or format
        output_file = output or Path(profile_config.output_file or "ai-context.json")
    else:
        include_patterns = include.split(",") if include else ["*"]
        exclude_patterns = exclude.split(",") if exclude else []
        max_file_size = max_size
        include_binary = binary
        output_format = format
        output_file = output or Path(f"ai-context.{format}")

    # Collect files
    try:
        files = collect_files(
            path,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            max_file_size=max_file_size,
            include_binary=include_binary
        )
    except Exception as e:
        typer.echo(f"Error collecting files: {e}", err=True)
        raise typer.Exit(1)

    # Apply token limit if specified
    if token_limit:
        filtered_files = []
        total_tokens = 0
        
        for file_info in files:
            try:
                tokens = count_tokens(file_info["content"], file_info["path"])
                if total_tokens + tokens <= token_limit:
                    filtered_files.append(file_info)
                    total_tokens += tokens
                else:
                    break
            except Exception:
                # Skip files that can't be tokenized
                continue
        
        files = filtered_files

    # Prepare export data
    export_data = {
        "metadata": {
            "source_path": str(path),
            "total_files": len(files),
            "total_size": sum(f["size"] for f in files),
            "format": output_format,
            "generated_at": str(typer.echo)
        },
        "files": files
    }

    # Write output in specified format
    try:
        if output_format == "json":
            with open(output_file, "w") as f:
                json.dump(export_data, f, indent=2)
        elif output_format == "markdown":
            _write_markdown(output_file, export_data)
        elif output_format == "xml":
            _write_xml(output_file, export_data)
        elif output_format == "yaml":
            with open(output_file, "w") as f:
                yaml.dump(export_data, f, default_flow_style=False)
        else:
            typer.echo(f"Error: Unsupported format '{output_format}'", err=True)
            raise typer.Exit(1)

        typer.echo(f"Exported {len(files)} files to {output_file}")
        
    except Exception as e:
        typer.echo(f"Error writing output: {e}", err=True)
        raise typer.Exit(1)


def _write_markdown(output_file: Path, export_data: dict) -> None:
    """Write export data in markdown format."""
    with open(output_file, "w") as f:
        f.write("# AI Context Export\n\n")
        f.write(f"**Source:** {export_data['metadata']['source_path']}\n")
        f.write(f"**Files:** {export_data['metadata']['total_files']}\n")
        f.write(f"**Total Size:** {format_file_size(export_data['metadata']['total_size'])}\n\n")
        
        for file_info in export_data["files"]:
            f.write(f"## {file_info['path']}\n\n")
            f.write(f"- **Size:** {format_file_size(file_info['size'])}\n")
            f.write(f"- **Type:** {file_info['type']}\n\n")
            
            if file_info["type"] == "text":
                lang = _get_language_from_extension(file_info["path"])
                f.write(f"```{lang}\n")
                f.write(file_info["content"])
                f.write("\n```\n\n")
            else:
                f.write(f"*Binary file - {file_info['size']} bytes*\n\n")


def _write_xml(output_file: Path, export_data: dict) -> None:
    """Write export data in XML format."""
    root = ET.Element("export")
    
    metadata = ET.SubElement(root, "metadata")
    ET.SubElement(metadata, "source_path").text = export_data["metadata"]["source_path"]
    ET.SubElement(metadata, "total_files").text = str(export_data["metadata"]["total_files"])
    ET.SubElement(metadata, "total_size").text = str(export_data["metadata"]["total_size"])
    ET.SubElement(metadata, "format").text = export_data["metadata"]["format"]
    
    files = ET.SubElement(root, "files")
    for file_info in export_data["files"]:
        file_elem = ET.SubElement(files, "file")
        ET.SubElement(file_elem, "path").text = file_info["path"]
        ET.SubElement(file_elem, "size").text = str(file_info["size"])
        ET.SubElement(file_elem, "type").text = file_info["type"]
        if file_info["type"] == "text":
            content = ET.SubElement(file_elem, "content")
            content.text = file_info["content"]
    
    tree = ET.ElementTree(root)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)


def _get_language_from_extension(file_path: str) -> str:
    """Get language identifier from file extension."""
    extension_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
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
        ".xml": "xml",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".ini": "ini",
        ".cfg": "ini",
        ".conf": "ini",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "zsh",
        ".fish": "fish",
        ".ps1": "powershell",
        ".sql": "sql",
        ".md": "markdown",
        ".dockerfile": "dockerfile",
        ".jsx": "jsx",
        ".tsx": "tsx",
        ".vue": "vue",
        ".svelte": "svelte",
    }
    
    ext = Path(file_path).suffix.lower()
    return extension_map.get(ext, "")


if __name__ == "__main__":
    app()