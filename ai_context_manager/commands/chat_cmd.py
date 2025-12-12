"""Chat/RAG CLI commands."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax

from ai_context_manager.config import CLI_CONTEXT_SETTINGS
from ai_context_manager.core.selection import Selection

try:  # Optional dependencies
    from ai_context_manager.core.rag import RAGEngine

    RAG_AVAILABLE = True
except ImportError:  # pragma: no cover - runtime warning
    RAG_AVAILABLE = False


app = typer.Typer(
    name="chat",
    help="Index selections into Qdrant and chat over them",
    context_settings=CLI_CONTEXT_SETTINGS,
)
console = Console()


def _ensure_deps() -> None:
    if not RAG_AVAILABLE:
        console.print("[red]AI dependencies missing.[/red]")
        console.print("Run: [bold]uv pip install -e '.[ai]'[/bold]")
        raise typer.Exit(1)


@app.command("index")
def index_cmd(
    selection_file: Path = typer.Argument(..., exists=True, help="Path to selection.yaml"),
) -> None:
    """Index files from a selection into Qdrant."""

    _ensure_deps()

    try:
        selection = Selection.load(selection_file)
        engine = RAGEngine(selection)
    except Exception as exc:  # pragma: no cover - CLI guardrail
        console.print(f"[red]Error initializing selection/engine: {exc}[/red]")
        raise typer.Exit(1)

    with console.status(f"[bold green]Indexing files from {selection.base_path}..."):
        count = engine.index_files()

    console.print(f"[green]✓ Indexed {count} chunks into Qdrant.[/green]")


@app.command("ask")
def ask_cmd(
    question: str = typer.Argument(None, help="Provide a single question or blank for interactive mode."),
) -> None:
    """Ask questions against indexed vectors."""

    _ensure_deps()

    empty_selection = Selection(base_path=Path("."), include_paths=[])

    try:
        engine = RAGEngine(empty_selection)
    except Exception as exc:
        console.print(f"[red]Failed to initialize RAG engine: {exc}[/red]")
        raise typer.Exit(1)

    def _ask(q: str) -> None:
        with console.status("[bold blue]Thinking..."):
            answer = engine.query(q)
        console.print(Markdown(answer))

    if question:
        _ask(question)
        return

    console.print("[bold blue]Interactive mode. Type 'exit' to quit.[/bold blue]")
    while True:
        q = typer.prompt("\nUser")
        if q.strip().lower() in {"exit", "quit", "q"}:
            break
        _ask(q)


@app.command("schema")
def schema_cmd() -> None:
    """Print the documentation frontmatter JSON schema."""

    schema_path = Path(__file__).parent.parent / "schemas" / "frontmatter.json"

    if not schema_path.exists():
        console.print("[red]Schema file not found.[/red]")
        raise typer.Exit(1)

    schema_content = schema_path.read_text()
    console.print(Syntax(schema_content, "json", theme="monokai", word_wrap=True))
