# Report: Show RAG Sources

**Status**: Completed

**Changes:**
1.  **RAG Engine**: Modified `ai_context_manager/core/rag.py` to return sources in `query()`.
2.  **CLI**: Modified `ai_context_manager/commands/chat_cmd.py` to display unique sources.
3.  **Docs**: Updated `docs/rag.md`.

**Verification:**
- Performed a query using `aicontext chat ask`.
- Confirmed that relevant file paths are printed at the bottom of the output.