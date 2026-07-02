"""Local lexical search over refinement chunks."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from ovis_retrieval import lexical_score, tokenize

from .segments import RefinementChunk


SEARCH_VERSION = "chat-refinement-search-v0"


@dataclass(frozen=True)
class SearchIndexRecord:
    chunk_id: str
    segment_id: str
    source_id: str
    terms: tuple[str, ...]
    term_counts: tuple[tuple[str, int], ...]
    speaker: str
    source_path: str
    message_id: str | None = None
    manifest_ref: str | None = None


@dataclass(frozen=True)
class SearchResult:
    query: str
    chunk_id: str
    segment_id: str
    source_id: str
    score: int
    rank: int
    snippet: str
    matched_terms: tuple[str, ...]
    source_path: str
    speaker: str
    message_id: str | None
    manifest_ref: str | None
    search_version: str


class ChatRetrievalIndex:
    """Deterministic in-memory lexical index for B3 refinement chunks."""

    def __init__(self, chunks: Iterable[RefinementChunk] = ()) -> None:
        self._chunks: dict[str, RefinementChunk] = {}
        for chunk in chunks:
            self.add_chunk(chunk)

    def add_chunk(self, chunk: RefinementChunk) -> None:
        self._chunks[chunk.chunk_id] = chunk

    def chunks(self) -> tuple[RefinementChunk, ...]:
        return tuple(self._chunks[key] for key in sorted(self._chunks))

    def records(self) -> tuple[SearchIndexRecord, ...]:
        return tuple(build_search_index_record(chunk) for chunk in self.chunks())

    def search(self, query: str, *, limit: int = 10) -> tuple[SearchResult, ...]:
        return search_refinement_chunks(self.chunks(), query, limit=limit)


def build_search_index_record(chunk: RefinementChunk) -> SearchIndexRecord:
    counts = Counter(chunk.normalized_terms)
    return SearchIndexRecord(
        chunk_id=chunk.chunk_id,
        segment_id=chunk.segment_id,
        source_id=chunk.source_id,
        terms=tuple(sorted(counts)),
        term_counts=tuple(sorted(counts.items())),
        speaker=chunk.speaker,
        source_path=chunk.source_path,
        message_id=chunk.message_id,
        manifest_ref=chunk.manifest_ref,
    )


def build_chat_retrieval_index(chunks: Iterable[RefinementChunk]) -> ChatRetrievalIndex:
    return ChatRetrievalIndex(chunks)


def search_refinement_chunks(
    chunks: Iterable[RefinementChunk],
    query: str,
    *,
    limit: int = 10,
) -> tuple[SearchResult, ...]:
    if not query.strip() or limit <= 0:
        return ()

    scored: list[tuple[RefinementChunk, int, tuple[str, ...]]] = []
    for chunk in chunks:
        score = lexical_score(query, chunk.text)
        if score <= 0:
            continue
        scored.append((chunk, score, _matched_terms(query, chunk)))

    ranked = sorted(scored, key=lambda item: (-item[1], item[0].source_id, item[0].segment_id, item[0].chunk_id))
    return tuple(
        SearchResult(
            query=query,
            chunk_id=chunk.chunk_id,
            segment_id=chunk.segment_id,
            source_id=chunk.source_id,
            score=score,
            rank=rank,
            snippet=chunk.text,
            matched_terms=matched_terms,
            source_path=chunk.source_path,
            speaker=chunk.speaker,
            message_id=chunk.message_id,
            manifest_ref=chunk.manifest_ref,
            search_version=SEARCH_VERSION,
        )
        for rank, (chunk, score, matched_terms) in enumerate(ranked[:limit], start=1)
    )


def _matched_terms(query: str, chunk: RefinementChunk) -> tuple[str, ...]:
    chunk_terms = set(chunk.normalized_terms)
    matched: list[str] = []
    seen: set[str] = set()
    for term in tokenize(query):
        if term in chunk_terms and term not in seen:
            matched.append(term)
            seen.add(term)
    return tuple(matched)
