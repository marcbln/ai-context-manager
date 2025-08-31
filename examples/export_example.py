#!/usr/bin/env python3
"""Example demonstrating how to use the ContextExporter."""

import tempfile
from pathlib import Path

from ai_context_manager.core.profile import Profile
from ai_context_manager.core.exporter import ContextExporter


def main():
    """Demonstrate basic usage of ContextExporter."""
    
    # Create a sample profile for a Python project
    profile = Profile(
        name="python-example",
        include_patterns=[
            "*.py",
            "*.md",
            "*.txt",
            "*.json",
            "*.yaml",
            "*.yml",
        ],
        exclude_patterns=[
            "__pycache__/*",
            "*.pyc",
            ".git/*",
            ".pytest_cache/*",
            "venv/*",
            ".venv/*",
            "node_modules/*",
        ],
        max_file_size=102400,  # 100KB
        include_binary=False,
    )
    
    # Create exporter instance
    exporter = ContextExporter(profile)
    
    # Export to different formats
    formats = ["markdown", "json", "xml", "yaml"]
    
    for format_name in formats:
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix=f'.{format_name}', 
            delete=False
        ) as f:
            output_path = Path(f.name)
        
        try:
            print(f"\nExporting to {format_name.upper()} format...")
            
            result = exporter.export_to_file(
                output_path,
                format=format_name,
                max_file_size=102400,
                include_binary=False,
            )
            
            if result["success"]:
                print(f"✅ Successfully exported {len(result['files'])} files")
                print(f"📁 Output file: {output_path}")
                print(f"📊 Total tokens: {result['total_tokens']}")
                print(f"📏 Total size: {result['total_size']} bytes")
                
                # Show first few lines of output for markdown
                if format_name == "markdown":
                    content = output_path.read_text()
                    lines = content.split('\n')[:10]
                    print("\n📄 Preview:")
                    for line in lines:
                        print(f"  {line}")
            else:
                print(f"❌ Export failed: {result['message']}")
                
        except Exception as e:
            print(f"❌ Error exporting to {format_name}: {e}")
        finally:
            # Clean up
            output_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()