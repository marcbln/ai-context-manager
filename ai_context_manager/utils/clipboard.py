"""Clipboard utilities for AI Context Manager."""
import shutil
import subprocess
from pathlib import Path
from rich.console import Console

console = Console()

def is_xclip_installed() -> bool:
    """Check if xclip is available on the system."""
    return shutil.which("xclip") is not None

def copy_file_uri_to_clipboard(file_path: Path) -> bool:
    """
    Copy the file URI to the clipboard using xclip (Linux).
    Target format is text/uri-list for file uploads.
    """
    if not is_xclip_installed():
        console.print("[red]Error: 'xclip' is not installed. Please install it to use the --copy feature.[/red]")
        return False

    abs_path = file_path.resolve()
    if not abs_path.exists():
        console.print(f"[red]Error: File not found at {abs_path}[/red]")
        return False

    # Construct URI (file:///absolute/path)
    file_uri = abs_path.as_uri()

    try:
        # echo -n "file://..." | xclip -selection clipboard -t text/uri-list
        subprocess.run(
            ["xclip", "-selection", "clipboard", "-t", "text/uri-list"],
            input=file_uri.encode("utf-8"),
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to copy to clipboard: {e}[/red]")
        return False
