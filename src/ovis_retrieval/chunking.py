# ---
# id: MODULE-RETRIEVAL-0003
# title: OVIS Retrieval Chunking
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: retrieval
# repo: ovis-runtime
# path: src/ovis_retrieval/chunking.py
# owner: Owen Vitae
# created: '2026-06-17'
# last_updated: '2026-06-17'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-RETRIEVAL-0003.yaml
# module_id: MOD-RETRIEVAL-LAYER-0001
# module_slug: retrieval_layer
# system_id: SYS-RETRIEVAL-MEMORY-0001
# system_slug: retrieval_memory
# ---
"""Deterministic plain-text chunking for local retrieval."""

from __future__ import annotations

from .types import RetrievalChunk, RetrievalDocument


def chunk_document(
    document: RetrievalDocument,
    *,
    max_words: int = 120,
    overlap_words: int = 0,
) -> tuple[RetrievalChunk, ...]:
    """Split a document into stable word-window chunks."""

    if max_words <= 0:
        raise ValueError("max_words must be greater than zero.")
    if overlap_words < 0:
        raise ValueError("overlap_words must be zero or greater.")
    if overlap_words >= max_words:
        raise ValueError("overlap_words must be less than max_words.")

    words = document.text.split()
    if not words:
        return ()

    chunks: list[RetrievalChunk] = []
    step = max_words - overlap_words
    start = 0
    while start < len(words):
        end = min(start + max_words, len(words))
        chunk_text = " ".join(words[start:end])
        chunks.append(
            RetrievalChunk(
                chunk_id=f"{document.document_id}:chunk_{len(chunks):04d}",
                document_id=document.document_id,
                source_ref=document.source_ref,
                text=chunk_text,
                start_word=start,
                end_word=end,
            )
        )
        if end == len(words):
            break
        start += step

    return tuple(chunks)
