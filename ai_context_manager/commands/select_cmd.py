"""Interactive TUI for selecting files and folders."""

from datetime import date
import getpass
from pathlib import Path
from typing import Dict, Set

import typer
import yaml
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.events import Mount
from textual.widgets import Button, DirectoryTree, Footer, Header, Input, Label

from ..config import CLI_CONTEXT_SETTINGS
from rich.text import Text

app = typer.Typer(help="Interactive file selection TUI", context_settings=CLI_CONTEXT_SETTINGS)


class SelectableDirectoryTree(DirectoryTree):
    """DirectoryTree widget that allows toggling selections."""

    def __init__(self, path: str, **kwargs):
        super().__init__(path, **kwargs)
        self.selected_paths: Set[Path] = set()

    def on_tree_node_selected(self, event: DirectoryTree.NodeSelected) -> None:  # type: ignore[override]
        """Handle node selection (toggle inclusion)."""
        event.stop()
        node = event.node
        path = node.data.path

        # 1. Update the selection state
        if path in self.selected_paths:
            self.selected_paths.remove(path)
        else:
            self.selected_paths.add(path)

        # 2. Reconstruct the label from the source filename
        # This prevents the accumulation of "[bold green]" tags
        label = Text(path.name)

        # 3. Apply styling if selected
        if path in self.selected_paths:
            # Add prefix and apply bold green style to the whole label
            label = Text.assemble("[x] ", label)
            label.stylize("bold green")

        # 4. Set the label using the Rich Text object
        # This ensures styles are rendered correctly, not as literal text
        node.set_label(label)




    def filter_tree(self, query: str) -> None:
        """Stub for future filtering support."""
        _ = query


class SelectionApp(App):
    """Textual App for interactive selection."""

    CSS = """
    Screen { layout: vertical; }
    .header-box { height: auto; dock: top; padding: 1; background: $primary-background-darken-1; }
    Input { margin-bottom: 1; }
    DirectoryTree { border: solid $accent; height: 1fr; scrollbar-gutter: stable; }
    .is-selected { color: $success; text-style: bold; }
    .footer-box { height: auto; dock: bottom; padding: 1; background: $primary-background-darken-1; align: right middle; }
    Button { margin-left: 1; }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("s", "save_and_quit", "Save & Quit"),
    ]

    def __init__(self, base_path: Path, output_file: Path, preselected: Dict | None = None):
        super().__init__()
        self.base_path = base_path
        self.output_file = output_file
        self.preselected = preselected or {}
        self.tree_widget = SelectableDirectoryTree(str(base_path), id="file_tree")

    def compose(self) -> ComposeResult:  # type: ignore[override]
        yield Header()
        yield Container(
            Label("Search (Highlight):"),
            Input(placeholder="Highlight filenames...", id="search_box"),
            classes="header-box",
        )
        yield self.tree_widget
        yield Container(
            Button("Cancel", variant="error", id="cancel"),
            Button("Save Selection (S)", variant="primary", id="save"),
            classes="footer-box",
        )
        yield Footer()

    def on_mount(self, event: Mount) -> None:  # type: ignore[override]
        _ = event
        # Future improvement: visually mark preselected nodes when Textual supports it efficiently.

    def on_button_pressed(self, event: Button.Pressed) -> None:  # type: ignore[override]
        if event.button.id == "save":
            self.action_save_and_quit()
        elif event.button.id == "cancel":
            self.exit(result=False)

    def action_save_and_quit(self) -> None:
        """Save selection to YAML strictly adhering to the schema and exit."""
        includes = []

        for path in self.tree_widget.selected_paths:
            try:
                rel_path = path.relative_to(self.base_path)
            except ValueError:
                rel_path = path

            includes.append(str(rel_path))

        includes.sort()

        current_user = getpass.getuser()
        today_str = date.today().isoformat()

        meta_data = {
            "description": "Context selection",
            "createdAt": today_str,
            "createdBy": current_user,
            "updatedAt": today_str,
            "updatedBy": current_user,
            "documentType": "CONTEXT_DEFINITION",
            "tags": ["auto-generated"],
            "version": "v1",
        }

        if self.output_file.exists():
            try:
                with open(self.output_file, "r", encoding="utf-8") as f:
                    existing = yaml.safe_load(f) or {}
            except Exception:
                existing = {}

            existing_meta = existing.get("meta")
            if isinstance(existing_meta, dict):
                meta_data["createdAt"] = existing_meta.get("createdAt", meta_data["createdAt"])
                meta_data["createdBy"] = existing_meta.get("createdBy", meta_data["createdBy"])
                meta_data["description"] = existing_meta.get("description", meta_data["description"])
                meta_data["tags"] = existing_meta.get("tags", meta_data["tags"])
                meta_data["version"] = existing_meta.get("version", meta_data["version"])
                meta_data["updatedAt"] = today_str
                meta_data["updatedBy"] = current_user

        data = {
            "meta": meta_data,
            "content": {
                "basePath": str(self.base_path.resolve()),
                "include": includes,
            },
        }

        with open(self.output_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f, sort_keys=False)

        self.exit(result=True)


@app.command()
def start(
    path: Path = typer.Argument(".", help="Base path to scan", exists=True, file_okay=False),
    output: Path = typer.Option("selection.yaml", "--output", "-o", help="Output YAML file"),
):
    """Launch the interactive selection TUI."""

    base_path = path.resolve()
    preselected: Dict | None = None

    if output.exists():
        try:
            with open(output, "r") as f:
                preselected = yaml.safe_load(f) or {}
        except Exception:
            preselected = None

    tui = SelectionApp(base_path=base_path, output_file=output, preselected=preselected)
    result = tui.run()

    if result:
        typer.echo(f"Selection saved to: {output}")
    else:
        typer.echo("Selection cancelled.")
