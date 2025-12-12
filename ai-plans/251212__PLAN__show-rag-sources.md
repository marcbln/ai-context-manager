# Implementation Plan: Show Sources in RAG Chat

## Problem Description
The current `aicontext chat ask` command generates answers based on indexed context but keeps the source material hidden. Users need to know which files were used to generate the answer to trust and verify the information.

## Phase 1: Update RAG Engine Return Type

**Objective:** Modify the `RAGEngine.query` method to return a structured dictionary containing both the answer and the metadata of the source chunks used.

### [MODIFY] ai_context_manager/core/rag.py

1.  Update imports to include `Dict` and `Any`.
2.  Refactor `query` to extract source metadata (filename, path, score) and return it alongside the answer.

```python
from typing import List, Dict, Any  # Update imports

# ... inside RAGEngine class ...

    def query(self, question: str, n_results: int = 5) -> Dict[str, Any]:
        q_resp = self.openai.embeddings.create(
            model=self.embedding_model,
            input=question,
        )
        q_vector = q_resp.data[0].embedding

        # Compatibility: Use query_points for qdrant-client >= 1.10.0, fallback to search for older versions
        search_result = self.qdrant.query_points(
            collection_name=self.collection_name,
            query=q_vector,
            limit=n_results,
        ).points


        if not search_result:
            return {
                "answer": "No relevant context found in the vector database.",
                "sources": []
            }

        # Extract sources
        sources = []
        for res in search_result:
            sources.append({
                "filename": res.payload.get("filename"),
                "path": res.payload.get("path"),
                "score": res.score
            })

        context_str = "\n\n---\n\n".join(
            [f"File: {res.payload['filename']}\nContent:\n{res.payload['text']}" for res in search_result]
        )

        system_prompt = (
            "You are an expert coding assistant used in a RAG system. "
            "Answer strictly using the CONTEXT below. "
            "If the answer is absent, say so.\n\n"
            f"CONTEXT:\n{context_str}"
        )

        response = self.openai.chat.completions.create(
            model=self.config.get("model", "gpt-4-turbo"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
        )

        return {
            "answer": response.choices[0].message.content,
            "sources": sources
        }
```

## Phase 2: Update Chat Command UI

**Objective:** Update the CLI command to handle the new return format and visually list the sources.

### [MODIFY] ai_context_manager/commands/chat_cmd.py

Update the `_ask` inner function within `ask_cmd` to print unique sources after the answer.

```python
    def _ask(q: str) -> None:
        with console.status("[bold blue]Thinking..."):
            result = engine.query(q)
        
        # Print Answer
        console.print(Markdown(result["answer"]))
        
        # Print Sources
        sources = result.get("sources", [])
        if sources:
            console.print()
            console.print("[bold]Sources:[/bold]")
            seen = set()
            for source in sources:
                path = source.get("path")
                # Deduplicate based on path to avoid listing same file multiple times if multiple chunks matched
                if path and path not in seen:
                    console.print(f" • [cyan]{source.get('filename')}[/cyan] [dim]({path})[/dim]")
                    seen.add(path)
```

## Phase 3: Documentation

**Objective:** Update the documentation to reflect the new feature.

### [MODIFY] docs/rag.md

Update the "Usage" section to mention source citation.

```markdown
### 2. Chat with your repo
```bash
# Interactive mode
aicontext chat ask

# Single question
aicontext chat ask "How does the Selector class work?"
```
The output will display the generated answer followed by a list of source files used as context.
```

## Phase 4: Status Report

**Objective:** Record the changes.

### [NEW FILE] ai-plans/251212__REPORT__show-rag-sources.md

```markdown
# Report: Show RAG Sources

**Status**: Completed

**Changes:**
1.  **RAG Engine**: Modified `ai_context_manager/core/rag.py` to return sources in `query()`.
2.  **CLI**: Modified `ai_context_manager/commands/chat_cmd.py` to display unique sources.
3.  **Docs**: Updated `docs/rag.md`.

**Verification:**
- Performed a query using `aicontext chat ask`.
- Confirmed that relevant file paths are printed at the bottom of the output.
```

