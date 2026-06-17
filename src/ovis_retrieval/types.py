# ---
# id: MODULE-RETRIEVAL-0002
# title: OVIS Retrieval Types
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: retrieval
# repo: ovis-runtime
# path: src/ovis_retrieval/types.py
# owner: Owen Vitae
# created: '2026-06-17'
# last_updated: '2026-06-17'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-RETRIEVAL-0002.yaml
# module_id: MOD-RETRIEVAL-LAYER-0001
# module_slug: retrieval_layer
# system_id: SYS-RETRIEVAL-MEMORY-0001
# system_slug: retrieval_memory
# ---
"""Shared dataclasses for local retrieval."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class RetrievalDocument:
    document_id: str
    source_ref: str
    text: str
    title: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievalChunk:
    chunk_id: str
    document_id: str
    source_ref: str
    text: str
    start_word: int
    end_word: int


@dataclass(frozen=True)
class RetrievalQuery:
    text: str
    limit: int = 10


@dataclass(frozen=True)
class RetrievalCitation:
    document_id: str
    source_ref: str
    chunk_id: str
    start_word: int
    end_word: int
    text: str


@dataclass(frozen=True)
class RetrievalResult:
    chunk: RetrievalChunk
    score: int
    citation: RetrievalCitation
