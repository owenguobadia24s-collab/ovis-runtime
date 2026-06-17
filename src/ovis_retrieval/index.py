# ---
# id: MODULE-RETRIEVAL-0005
# title: OVIS In-Memory Retrieval Index
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: retrieval
# repo: ovis-runtime
# path: src/ovis_retrieval/index.py
# owner: Owen Vitae
# created: '2026-06-17'
# last_updated: '2026-06-17'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-RETRIEVAL-0005.yaml
# module_id: MOD-RETRIEVAL-LAYER-0001
# module_slug: retrieval_layer
# system_id: SYS-RETRIEVAL-MEMORY-0001
# system_slug: retrieval_memory
# ---
"""Local in-process retrieval index."""

from __future__ import annotations

from .chunking import chunk_document
from .query import lexical_score
from .types import RetrievalChunk, RetrievalCitation, RetrievalDocument, RetrievalQuery, RetrievalResult


class InMemoryRetrievalIndex:
    """Deterministic lexical index with no persistence or external services."""

    def __init__(self, *, max_words: int = 120, overlap_words: int = 0) -> None:
        self._max_words = max_words
        self._overlap_words = overlap_words
        self._chunks: dict[str, RetrievalChunk] = {}

    def add_document(self, document: RetrievalDocument) -> tuple[RetrievalChunk, ...]:
        chunks = chunk_document(
            document,
            max_words=self._max_words,
            overlap_words=self._overlap_words,
        )
        for chunk in chunks:
            self._chunks[chunk.chunk_id] = chunk
        return chunks

    def chunks(self) -> tuple[RetrievalChunk, ...]:
        return tuple(self._chunks[key] for key in sorted(self._chunks))

    def query(self, query: RetrievalQuery | str) -> tuple[RetrievalResult, ...]:
        retrieval_query = query if isinstance(query, RetrievalQuery) else RetrievalQuery(text=query)
        if not retrieval_query.text.strip() or retrieval_query.limit <= 0:
            return ()

        results: list[RetrievalResult] = []
        for chunk in self.chunks():
            score = lexical_score(retrieval_query.text, chunk.text)
            if score <= 0:
                continue
            results.append(
                RetrievalResult(
                    chunk=chunk,
                    score=score,
                    citation=RetrievalCitation(
                        document_id=chunk.document_id,
                        source_ref=chunk.source_ref,
                        chunk_id=chunk.chunk_id,
                        start_word=chunk.start_word,
                        end_word=chunk.end_word,
                        text=chunk.text,
                    ),
                )
            )

        ranked = sorted(
            results,
            key=lambda result: (-result.score, result.chunk.document_id, result.chunk.chunk_id),
        )
        return tuple(ranked[: retrieval_query.limit])
