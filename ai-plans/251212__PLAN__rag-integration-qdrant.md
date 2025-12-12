ai-plans/251212__PLAN__rag-integration-qdrant.md

# Implementation Plan: RAG Integration with Qdrant & JSON Schema

## Problem Description
The `ai-context-manager` currently excels at selecting and exporting file contexts. However, users lack a way to interactively query this context using natural language without manually copy-pasting into an external LLM.

We need to implement a **Retrieval-Augmented Generation (RAG)** system that:
1.  **Indexes** selected files into a local **Qdrant** vector database (running in Docker).
2.  **Queries** this database using OpenAI embeddings and chat models.
3.  **Standardizes** documentation metadata using a **JSON Schema** (instead of Python/Pydantic validation), allowing the schema to be easily shared with AI agents for generating compliant documentation.

---

## Phase 1: Dependencies & Configuration

**Objective**: Update project dependencies and configuration to support AI libraries and Qdrant connection settings.

### 1. Update `pyproject.toml`
[MODIFY] `pyproject.toml`
Add the `ai` extra with `openai`, `qdrant-client`, and `jsonschema`.

```toml
# ... existing content ...

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "black>=24.0.0",
    "mypy>=1.8.0",
    "ruff>=0.3.0",
]
ai = [
    "openai>=1.0.0",
    "qdrant-client>=1.7.0",
    "tiktoken>=0.5.0",
    "jsonschema>=4.0.0",
]
# ... existing content ...
```

### 2. Update `ai_context_manager/config.py`
[MODIFY] `ai_context_manager/config.py`
Add the `ai` configuration section with Qdrant and OpenAI defaults.

```python
# ... inside class Config ...
    def create_default(self) -> None:
        """Create default configuration."""
        self.data = {
            # ... existing config ...
            "ai": {
                "openai_api_key": "",  # Reads from ENV: OPENAI_API_KEY if empty
                "model": "gpt-4-turbo",
                "embedding_model": "text-embedding-3-small",
                "qdrant_url": "http://localhost:6333",
                "collection_name": "ai_context_manager_docs"
            }
        }
        self.save()
```

---

## Phase 2: JSON Schema for Frontmatter

**Objective**: Define a strict JSON schema for documentation frontmatter. This file serves as the "source of truth" for AI agents writing docs.

### 1. Create Schema Directory
Create directory `ai_context_manager/schemas/` if it doesn't exist.

### 2. Create Schema File
[NEW FILE] `ai_context_manager/schemas/frontmatter.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "AI Documentation Frontmatter",
  "description": "Standard metadata for AI-generated documentation files.",
  "type": "object",
  "required": ["status", "last_edit_date"],
  "properties": {
    "title": {
      "type": "string",
      "description": "Overrides the H1 if needed, useful for UI display."
    },
    "status": {
      "type": "string",
      "enum": ["draft", "review", "stable", "deprecated"],
      "description": "The current lifecycle state of this document."
    },
    "last_edit_date": {
      "type": "string",
      "format": "date",
      "description": "YYYY-MM-DD format."
    },
    "reviewed_by": {
      "type": "array",
      "items": { "type": "string" },
      "description": "List of AI models or humans who have validated this document."
    },
    "tags": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Keywords for categorization."
    },
    "description": {
        "type": "string",
        "description": "Brief summary used for RAG retrieval context."
    }
  }
}
```

---

## Phase 3: Core RAG Engine

**Objective**: Implement the logic to chunk text, generate embeddings via OpenAI, and upsert vectors to Qdrant.

### 1. Create `ai_context_manager/core/rag.py`
[NEW FILE] `ai_context_manager/core/rag.py`

```python
import os
import uuid
import json
from typing import List
from pathlib import Path

# Optional imports handled gracefully in the command layer, but typed here
try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as rest
    from openai import OpenAI
except ImportError:
    pass

from ai_context_manager.core.selection import Selection
from ai_context_manager.utils.file_utils import read_file_content
from ai_context_manager.config import Config

class RAGEngine:
    def __init__(self, selection: Selection):
        self.selection = selection
        self.config = Config().get("ai")
        
        # Initialize clients
        api_key = self.config.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API Key is missing. Set OPENAI_API_KEY env var or check config.")
            
        self.openai = OpenAI(api_key=api_key)
        self.qdrant = QdrantClient(url=self.config.get("qdrant_url", "http://localhost:6333"))
        
        self.collection_name = self.config.get("collection_name", "ai_context_manager_docs")
        self.embedding_model = self.config.get("embedding_model", "text-embedding-3-small")
        # 1536 is the dimension for text-embedding-3-small
        self.vector_size = 1536 

        self._ensure_collection()

    def _ensure_collection(self):
        """Create Qdrant collection if it doesn't exist."""
        if not self.qdrant.collection_exists(self.collection_name):
            self.qdrant.create_collection(
                collection_name=self.collection_name,
                vectors_config=rest.VectorParams(
                    size=self.vector_size,
                    distance=rest.Distance.COSINE,
                ),
            )

    def index_files(self) -> int:
        """Read selection, chunk, embed, and upsert to Qdrant."""
        files = self.selection.resolve_all_files()
        points = []
        
        for file_path in files:
            content = read_file_content(file_path)
            if not content:
                continue

            chunks = self._chunk_text(content)
            
            for i, chunk_text in enumerate(chunks):
                # 1. Generate Embedding
                response = self.openai.embeddings.create(
                    input=chunk_text,
                    model=self.embedding_model
                )
                vector = response.data[0].embedding
                
                # 2. Create Deterministic ID (deduplication)
                # Content-based ID ensures we update existing chunks rather than duplicating
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{file_path.name}:{i}:{chunk_text[:30]}"))
                
                # 3. Build Payload
                points.append(rest.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "filename": file_path.name,
                        "path": str(file_path),
                        "text": chunk_text
                    }
                ))

        if not points:
            return 0

        # 4. Upsert Batch
        self.qdrant.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        return len(points)

    def query(self, question: str, n_results: int = 5) -> str:
        """RAG Workflow: Embed Question -> Search Qdrant -> LLM Answer."""
        
        # 1. Embed Query
        q_resp = self.openai.embeddings.create(
            input=question,
            model=self.embedding_model
        )
        q_vector = q_resp.data[0].embedding

        # 2. Search Vector DB
        search_result = self.qdrant.search(
            collection_name=self.collection_name,
            query_vector=q_vector,
            limit=n_results
        )

        if not search_result:
            return "No relevant context found in the vector database."

        # 3. Construct Prompt with Context
        context_str = "\n\n---\n\n".join(
            [f"File: {res.payload['filename']}\nContent:\n{res.payload['text']}" for res in search_result]
        )

        system_prompt = (
            "You are an expert coding assistant used in a RAG system. "
            "Answer the user's question strictly based on the provided CONTEXT below. "
            "If the answer is not in the context, state that explicitly.\n\n"
            f"CONTEXT:\n{context_str}"
        )

        # 4. Generate Answer
        response = self.openai.chat.completions.create(
            model=self.config.get("model", "gpt-4-turbo"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ]
        )

        return response.choices[0].message.content

    def _chunk_text(self, text: str, chunk_size: int = 1500) -> List[str]:
        """Simple chunking strategy splitting by double newlines."""
        raw_chunks = text.split("\n\n")
        merged_chunks = []
        current_chunk = ""

        for part in raw_chunks:
            if len(current_chunk) + len(part) < chunk_size:
                current_chunk += part + "\n\n"
            else:
                merged_chunks.append(current_chunk.strip())
                current_chunk = part + "\n\n"
        
        if current_chunk:
            merged_chunks.append(current_chunk.strip())
            
        return merged_chunks
```

---

## Phase 4: Chat Command & CLI Integration

**Objective**: Create the `chat` subcommand to handle indexing, querying, and displaying the JSON schema.

### 1. Create `ai_context_manager/commands/chat_cmd.py`
[NEW FILE] `ai_context_manager/commands/chat_cmd.py`

```python
import json
import typer
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax

from ai_context_manager.config import CLI_CONTEXT_SETTINGS
from ai_context_manager.core.selection import Selection

# Conditional import for optional dependencies
try:
    from ai_context_manager.core.rag import RAGEngine
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

app = typer.Typer(help="Chat with your context using Qdrant & OpenAI", context_settings=CLI_CONTEXT_SETTINGS)
console = Console()

def check_deps():
    if not RAG_AVAILABLE:
        console.print("[red]Error: AI dependencies not installed.[/red]")
        console.print("Run: [bold]uv pip install -e '.[ai]'[/bold]")
        raise typer.Exit(1)

@app.command("index")
def index_cmd(
    selection_file: Path = typer.Argument(..., help="Path to selection.yaml", exists=True),
):
    """Index the files in selection.yaml into Qdrant."""
    check_deps()
    
    try:
        selection = Selection.load(selection_file)
        engine = RAGEngine(selection)
        
        with console.status(f"[bold green]Indexing files from {selection.base_path}..."):
            count = engine.index_files()
            
        console.print(f"[green]Successfully indexed {count} chunks into Qdrant![/green]")
        
    except Exception as e:
        console.print(f"[red]Indexing failed: {e}[/red]")
        raise typer.Exit(1)

@app.command("ask")
def ask_cmd(
    question: str = typer.Argument(None, help="The question to ask. If empty, starts interactive mode."),
):
    """Query the indexed context."""
    check_deps()

    # Create dummy selection for engine init (Engine needs it for config/clients, though query doesn't use it)
    # This design could be refactored later to separate Indexer from Querier, but acceptable for MVP.
    empty_selection = Selection(base_path=Path("."), include_paths=[])
    try:
        engine = RAGEngine(empty_selection)
    except Exception as e:
        console.print(f"[red]Failed to initialize RAG engine: {e}[/red]")
        raise typer.Exit(1)

    if question:
        # Single shot
        with console.status("[bold blue]Thinking..."):
            answer = engine.query(question)
        console.print(Markdown(answer))
    else:
        # Interactive
        console.print("[bold blue]Starting Chat Session (type 'exit' or 'quit' to stop)[/bold blue]")
        while True:
            q = typer.prompt("\nUser")
            if q.lower() in ['exit', 'quit', 'q']:
                break
            
            with console.status("[bold blue]Thinking..."):
                answer = engine.query(q)
            
            console.print("\n[bold purple]AI:[/bold purple]")
            console.print(Markdown(answer))

@app.command("schema")
def schema_cmd():
    """Print the Frontmatter JSON Schema (useful for giving to AI agents)."""
    schema_path = Path(__file__).parent.parent / "schemas" / "frontmatter.json"
    if schema_path.exists():
        schema_content = schema_path.read_text()
        console.print(Syntax(schema_content, "json", theme="monokai", word_wrap=True))
    else:
        console.print("[red]Schema file not found.[/red]")

```

### 2. Update `ai_context_manager/cli.py`
[MODIFY] `ai_context_manager/cli.py`
Register the new command group.

```python
# ... imports ...
from ai_context_manager.commands import select_cmd, export_cmd, generate_cmd, chat_cmd # <--- Import

# ... inside app setup ...
app.add_typer(select_cmd.app, name="select", help="Open visual file selector")
app.add_typer(export_cmd.app, name="export", help="Native: Generate context from selection.yaml")
app.add_typer(generate_cmd.app, name="generate", help="Repomix: Generate context using external tool")
app.add_typer(chat_cmd.app, name="chat", help="RAG: Index and Chat with your code") # <--- Register

# ...
```

---

## Phase 5: Documentation

**Objective**: Update documentation to explain the new RAG capabilities, prerequisite setup (Qdrant), and how to use the schema.

### 1. Create `docs/rag.md`
[NEW FILE] `docs/rag.md`

```markdown
# RAG & Chat Documentation

AI Context Manager now includes a Retrieval-Augmented Generation (RAG) system powered by **Qdrant** and **OpenAI**.

## Prerequisites

1.  **Install Dependencies**:
    ```bash
    uv pip install -e ".[ai]"
    ```
2.  **Run Qdrant**:
    You must have a Qdrant instance running. The default configuration expects it at `http://localhost:6333`.
    ```yaml
    services:
      qdrant:
        image: qdrant/qdrant
        ports:
          - "6333:6333"
        volumes:
          - ./vol/qdrant_storage:/qdrant/storage
    ```
3.  **OpenAI API Key**:
    Set `OPENAI_API_KEY` in your environment or in `~/.config/ai-context-manager/config.json`.

## Usage

### 1. Indexing
Index the files referenced in your selection file.
```bash
aicontext chat index selection.yaml
```

### 2. Chatting
Ask questions about your indexed codebase.
```bash
# Interactive mode
aicontext chat ask

# Single question
aicontext chat ask "How does the Selector class work?"
```

### 3. Frontmatter Schema
If you use AI agents to write documentation for this project, you can retrieve the strict JSON schema for frontmatter to include in your prompt context:

```bash
aicontext chat schema
```
```

### 2. Update `README.md`
[MODIFY] `README.md`
Add a brief section about "Chat & RAG" linking to `docs/rag.md` and mentioning the schema command.

---

## Phase 6: Reporting

**Objective**: Confirm changes.

### 1. Create Report File
[NEW FILE] `ai-plans/251212__REPORT__rag-integration-qdrant.md`

```markdown
# Report: RAG Integration

## Changes Implemented
1.  **Dependencies**: Added `openai`, `qdrant-client`, `jsonschema` to `pyproject.toml`.
2.  **Configuration**: Updated `config.py` to support AI settings.
3.  **Schema**: Created `schemas/frontmatter.json` for standardized docs.
4.  **Core**: Implemented `RAGEngine` in `core/rag.py`.
5.  **CLI**: Added `chat` command group with `index`, `ask`, and `schema`.
6.  **Docs**: Created `docs/rag.md`.

## Verification
- [ ] Run `aicontext chat schema` to verify schema output.
- [ ] Ensure Docker Qdrant is running.
- [ ] Run `aicontext chat index selection.yaml`.
- [ ] Run `aicontext chat ask "Summarize this project"`.
```

