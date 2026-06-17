# ---
# id: MODULE-RETRIEVAL-0001
# title: OVIS Retrieval Package
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: retrieval
# repo: ovis-runtime
# path: src/ovis_retrieval/__init__.py
# owner: Owen Vitae
# created: '2026-06-17'
# last_updated: '2026-06-17'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-RETRIEVAL-0001.yaml
# module_id: MOD-RETRIEVAL-LAYER-0001
# module_slug: retrieval_layer
# system_id: SYS-RETRIEVAL-MEMORY-0001
# system_slug: retrieval_memory
# ---
"""Local deterministic retrieval scaffold."""

from .chunking import chunk_document
from .index import InMemoryRetrievalIndex
from .query import lexical_score, tokenize
from .types import (
    RetrievalChunk,
    RetrievalCitation,
    RetrievalDocument,
    RetrievalQuery,
    RetrievalResult,
)

__all__ = [
    "InMemoryRetrievalIndex",
    "RetrievalChunk",
    "RetrievalCitation",
    "RetrievalDocument",
    "RetrievalQuery",
    "RetrievalResult",
    "chunk_document",
    "lexical_score",
    "tokenize",
]
