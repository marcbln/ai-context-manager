# RAG & Chat Documentation

AI Context Manager now includes a Retrieval-Augmented Generation (RAG) workflow powered by **Qdrant** and **OpenAI**.

## Prerequisites

1. **Install dependencies**
   ```bash
   uv pip install -e ".[ai]"
   ```
2. **Run Qdrant** (example docker-compose)
   ```yaml
   services:
     qdrant:
       image: qdrant/qdrant
       ports:
         - "6333:6333"
       volumes:
         - ./vol/qdrant_storage:/qdrant/storage
   ```
3. **Configure OpenAI**
   Set `OPENAI_API_KEY` in your environment or in `~/.config/ai-context-manager/config.json`.

## Usage

### 1. Index selections
Index the files referenced in your selection file.
```bash
aicontext chat index selection.yaml
```

### 2. Chat with your repo
```bash
# Interactive mode
aicontext chat ask

# Single question
aicontext chat ask "How does the Selector class work?"
```
The output will display the generated answer followed by a list of source files used as context.

### 3. Frontmatter schema
Give downstream AI agents the canonical JSON schema for documentation frontmatter:
```bash
aicontext chat schema
```
