"""Export context to various formats command."""
import typer
import yaml
import json
from pathlib import Path
from typing import Optional, List
import os
from datetime import datetime

from ..config import get_config_dir

app = typer.Typer(help="Export context to various formats")

def load_context():
    """Load the current context from YAML file."""
    config_dir = get_config_dir()
    context_file = config_dir / "context.yaml"
    
    if not context_file.exists():
        return {"files": []}
    
    with open(context_file, 'r') as f:
        return yaml.safe_load(f) or {"files": []}

def read_file_content(file_path):
    """Read and return file content."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

def load_profile(profile_name: str) -> Optional[dict]:
    """Load export profile configuration."""
    if not profile_name:
        return None
    
    from ..commands.profile_cmd import load_profile as load_profile_config
    return load_profile_config(profile_name)

def filter_files_by_profile(files: List[str], profile: Optional[dict]) -> List[str]:
    """Filter files based on profile settings."""
    if not profile:
        return files
    
    filtered_files = []
    max_size = profile.get('max_file_size')
    extensions = profile.get('file_extensions')
    
    for file_path in files:
        # Check file extension filter
        if extensions:
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in [f".{ext.lower()}" for ext in extensions]:
                continue
        
        # Check file size filter
        if max_size and os.path.exists(file_path):
            try:
                if os.path.getsize(file_path) > max_size:
                    continue
            except OSError:
                continue
        
        filtered_files.append(file_path)
    
    return filtered_files

@app.command()
def markdown(
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Export profile to use"),
):
    """Export context as markdown."""
    context = load_context()
    files = context.get("files", [])
    
    if not files:
        typer.echo("No files in context to export")
        return
    
    # Load and apply profile
    profile_config = load_profile(profile)
    if profile_config:
        files = filter_files_by_profile(files, profile_config)
        typer.echo(f"Using profile: {profile}")
    
    if not files:
        typer.echo("No files match profile criteria")
        return
    
    # Check if metadata should be included
    include_metadata = True
    if profile_config:
        include_metadata = profile_config.get('include_metadata', True)
    
    # Generate markdown content
    markdown_content = f"# Context Export\n\n"
    
    if include_metadata:
        markdown_content += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        markdown_content += f"Total files: {len(files)}\n\n"
        markdown_content += "---\n\n"
    
    for file_path in files:
        if os.path.exists(file_path):
            content = read_file_content(file_path)
            markdown_content += f"## {file_path}\n\n"
            markdown_content += f"```{Path(file_path).suffix[1:] or 'text'}\n"
            markdown_content += f"{content}\n"
            markdown_content += "```\n\n"
        else:
            markdown_content += f"## {file_path}\n\n"
            markdown_content += "*File not found*\n\n"
    
    if output:
        with open(output, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        typer.echo(f"Exported to {output}")
    else:
        typer.echo(markdown_content)

@app.command()
def xml(
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Export profile to use"),
):
    """Export context as XML."""
    context = load_context()
    files = context.get("files", [])
    
    if not files:
        typer.echo("No files in context to export")
        return
    
    # Load and apply profile
    profile_config = load_profile(profile)
    if profile_config:
        files = filter_files_by_profile(files, profile_config)
        typer.echo(f"Using profile: {profile}")
    
    if not files:
        typer.echo("No files match profile criteria")
        return
    
    # Check if metadata should be included
    include_metadata = True
    if profile_config:
        include_metadata = profile_config.get('include_metadata', True)
    
    # Generate XML content
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<context>\n'
    
    if include_metadata:
        xml_content += f'  <metadata>\n'
        xml_content += f'    <generated>{datetime.now().isoformat()}</generated>\n'
        xml_content += f'    <total_files>{len(files)}</total_files>\n'
        xml_content += f'  </metadata>\n'
    
    for file_path in files:
        xml_content += f'  <file path="{file_path}">\n'
        if os.path.exists(file_path):
            content = read_file_content(file_path)
            xml_content += f'    <content><![CDATA[{content}]]></content>\n'
        else:
            xml_content += '    <content>File not found</content>\n'
        xml_content += '  </file>\n'
    
    xml_content += '</context>\n'
    
    if output:
        with open(output, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        typer.echo(f"Exported to {output}")
    else:
        typer.echo(xml_content)

@app.command()
def json(
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Export profile to use"),
):
    """Export context as JSON."""
    context = load_context()
    files = context.get("files", [])
    
    if not files:
        typer.echo("No files in context to export")
        return
    
    # Load and apply profile
    profile_config = load_profile(profile)
    if profile_config:
        files = filter_files_by_profile(files, profile_config)
        typer.echo(f"Using profile: {profile}")
    
    if not files:
        typer.echo("No files match profile criteria")
        return
    
    # Check if metadata should be included
    include_metadata = True
    if profile_config:
        include_metadata = profile_config.get('include_metadata', True)
    
    # Generate JSON content
    export_data = {"files": []}
    
    if include_metadata:
        export_data["metadata"] = {
            "generated": datetime.now().isoformat(),
            "total_files": len(files)
        }
    
    for file_path in files:
        file_data = {
            "path": file_path,
            "exists": os.path.exists(file_path)
        }
        
        if file_data["exists"]:
            file_data["content"] = read_file_content(file_path)
            file_data["size"] = os.path.getsize(file_path)
        else:
            file_data["content"] = None
            file_data["size"] = 0
        
        export_data["files"].append(file_data)
    
    json_content = json.dumps(export_data, indent=2)
    
    if output:
        with open(output, 'w', encoding='utf-8') as f:
            f.write(json_content)
        typer.echo(f"Exported to {output}")
    else:
        typer.echo(json_content)