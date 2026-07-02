from pathlib import Path
import socket
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_chat_ingestion import parse_transcript_file  # noqa: E402
from ovis_refinement import (  # noqa: E402
    SEARCH_VERSION,
    ChatRetrievalIndex,
    RefinementChunk,
    SearchIndexRecord,
    SearchResult,
    adapt_chat_segments,
    build_chat_retrieval_index,
    build_search_index_record,
    chunk_refinement_segments,
    search_refinement_chunks,
)


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "chat_ingestion"


def _fixture_chunks() -> tuple[RefinementChunk, ...]:
    parsed = parse_transcript_file(FIXTURE_ROOT / "sample_transcript.md")
    segments = adapt_chat_segments(parsed.source, parsed.segments, manifest=parsed.manifest)
    return chunk_refinement_segments(segments, max_words=20)


def test_search_index_records_preserve_chunk_and_source_references() -> None:
    chunk = _fixture_chunks()[0]

    record = build_search_index_record(chunk)

    assert isinstance(record, SearchIndexRecord)
    assert record.chunk_id == chunk.chunk_id
    assert record.segment_id == chunk.segment_id
    assert record.source_id == chunk.source_id
    assert record.speaker == chunk.speaker
    assert record.source_path == chunk.source_path
    assert record.message_id == chunk.message_id
    assert record.manifest_ref == chunk.manifest_ref
    assert "local" in record.terms
    assert ("local", 1) in record.term_counts


def test_chat_retrieval_index_search_is_deterministic_and_source_preserving() -> None:
    chunks = _fixture_chunks()
    index = build_chat_retrieval_index(chunks)

    first = index.search("local surface", limit=5)
    second = index.search("local surface", limit=5)

    assert first == second
    assert all(isinstance(result, SearchResult) for result in first)
    assert len(first) == 1
    assert first[0].query == "local surface"
    assert first[0].score == 2
    assert first[0].rank == 1
    assert first[0].chunk_id == chunks[0].chunk_id
    assert first[0].segment_id == chunks[0].segment_id
    assert first[0].source_id == chunks[0].source_id
    assert first[0].source_path == chunks[0].source_path
    assert first[0].matched_terms == ("local", "surface")
    assert first[0].search_version == SEARCH_VERSION


def test_search_ranking_uses_score_then_stable_secondary_keys() -> None:
    chunks = (
        RefinementChunk(
            chunk_id="chunk-b",
            segment_id="segment-b",
            source_id="source-b",
            message_id="message-b",
            speaker="User",
            text="alpha alpha beta",
            chunk_index=0,
            start_word=0,
            end_word=3,
            normalized_terms=("alpha", "alpha", "beta"),
            source_path="fixture-b.md",
        ),
        RefinementChunk(
            chunk_id="chunk-a",
            segment_id="segment-a",
            source_id="source-a",
            message_id="message-a",
            speaker="Assistant",
            text="alpha beta",
            chunk_index=0,
            start_word=0,
            end_word=2,
            normalized_terms=("alpha", "beta"),
            source_path="fixture-a.md",
        ),
        RefinementChunk(
            chunk_id="chunk-c",
            segment_id="segment-c",
            source_id="source-c",
            message_id="message-c",
            speaker="User",
            text="alpha beta",
            chunk_index=0,
            start_word=0,
            end_word=2,
            normalized_terms=("alpha", "beta"),
            source_path="fixture-c.md",
        ),
    )

    results = search_refinement_chunks(chunks, "alpha")

    assert [(result.chunk_id, result.score, result.rank) for result in results] == [
        ("chunk-b", 2, 1),
        ("chunk-a", 1, 2),
        ("chunk-c", 1, 3),
    ]


def test_search_empty_query_limit_and_non_matches_are_stable() -> None:
    index = ChatRetrievalIndex(_fixture_chunks())

    assert index.search("   ") == ()
    assert index.search("local", limit=0) == ()
    assert index.search("missing") == ()


def test_index_add_chunk_and_records_are_sorted_by_chunk_id() -> None:
    chunks = tuple(reversed(_fixture_chunks()))
    index = ChatRetrievalIndex()
    for chunk in chunks:
        index.add_chunk(chunk)

    assert [chunk.chunk_id for chunk in index.chunks()] == sorted(chunk.chunk_id for chunk in chunks)
    assert [record.chunk_id for record in index.records()] == sorted(chunk.chunk_id for chunk in chunks)


def test_search_does_not_require_socket_access(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_socket(*args: object, **kwargs: object) -> None:
        raise AssertionError("search attempted socket access")

    monkeypatch.setattr(socket, "socket", fail_socket)

    results = search_refinement_chunks(_fixture_chunks(), "classification")

    assert len(results) == 1
