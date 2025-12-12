"""Core RAG engine for AI Context Manager."""

from __future__ import annotations

import os
import uuid
from typing import List
from pathlib import Path

try:  # Optional heavy deps
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as rest
    from openai import OpenAI
except ImportError:  # pragma: no cover - handled at runtime by CLI
    QdrantClient = None  # type: ignore
    rest = None  # type: ignore
    OpenAI = None  # type: ignore

from ai_context_manager.core.selection import Selection
from ai_context_manager.utils.file_utils import read_file_content
from ai_context_manager.config import Config


class RAGEngine:
    """Chunk, embed, and query repository context via Qdrant + OpenAI."""

    def __init__(self, selection: Selection):
        if QdrantClient is None or OpenAI is None:
            raise ImportError("AI dependencies missing. Install with `uv pip install -e '.[ai]'`")

        self.selection = selection
        self.config = Config().get("ai") or {}

        api_key = self.config.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key missing. Set OPENAI_API_KEY or config.ai.openai_api_key")

        self.openai = OpenAI(api_key=api_key)
        self.qdrant = QdrantClient(url=self.config.get("qdrant_url", "http://localhost:6333"))

        self.collection_name = self.config.get("collection_name", "ai_context_manager_docs")
        self.embedding_model = self.config.get("embedding_model", "text-embedding-3-small")
        self.vector_size = 1536  # text-embedding-3-small dimension

        self._ensure_collection()

    def _ensure_collection(self) -> None:
        if not self.qdrant.collection_exists(self.collection_name):
            self.qdrant.create_collection(
                collection_name=self.collection_name,
                vectors_config=rest.VectorParams(
                    size=self.vector_size,
                    distance=rest.Distance.COSINE,
                ),
            )

    def index_files(self) -> int:
        files = self.selection.resolve_all_files()
        points = []

        for file_path in files:
            content = read_file_content(file_path)
            if not content:
                continue

            chunks = self._chunk_text(content)

            for idx, chunk_text in enumerate(chunks):
                response = self.openai.embeddings.create(
                    model=self.embedding_model,
                    input=chunk_text,
                )
                vector = response.data[0].embedding

                point_id = str(
                    uuid.uuid5(
                        uuid.NAMESPACE_DNS,
                        f"{file_path}:{idx}:{chunk_text[:30]}",
                    )
                )

                points.append(
                    rest.PointStruct(
                        id=point_id,
                        vector=vector,
                        payload={
                            "filename": file_path.name,
                            "path": str(file_path),
                            "text": chunk_text,
                        },
                    )
                )

        if not points:
            return 0

        self.qdrant.upsert(collection_name=self.collection_name, points=points)
        return len(points)

    def query(self, question: str, n_results: int = 5) -> str:
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
            return "No relevant context found in the vector database."

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

        return response.choices[0].message.content

    def _chunk_text(self, text: str, chunk_size: int = 1500) -> List[str]:
        raw_chunks = text.split("\n\n")
        merged: List[str] = []
        current = ""

        for part in raw_chunks:
            if len(current) + len(part) + 2 <= chunk_size:
                current += part + "\n\n"
            else:
                if current.strip():
                    merged.append(current.strip())
                current = part + "\n\n"

        if current.strip():
            merged.append(current.strip())

        return merged or [text[:chunk_size]]
