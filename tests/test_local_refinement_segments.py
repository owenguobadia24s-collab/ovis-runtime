from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_chat_ingestion import parse_transcript_file  # noqa: E402
from ovis_refinement import (  # noqa: E402
    REFINEMENT_CHUNK_VERSION,
    REFINEMENT_SEGMENT_VERSION,
    RefinementChunk,
    RefinementSegment,
    adapt_chat_segments,
    chunk_refinement_segment,
    chunk_refinement_segments,
    to_retrieval_chunks,
    to_retrieval_document,
)
from ovis_retrieval import RetrievalChunk, RetrievalDocument  # noqa: E402


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "chat_ingestion"


def test_chat_segments_adapt_deterministically_and_preserve_source_fields() -> None:
    parsed = parse_transcript_file(FIXTURE_ROOT / "sample_transcript.md")

    first = adapt_chat_segments(parsed.source, parsed.segments, manifest=parsed.manifest)
    second = adapt_chat_segments(parsed.source, parsed.segments, manifest=parsed.manifest)

    assert first == second
    assert all(isinstance(segment, RefinementSegment) for segment in first)
    assert len(first) == 3
    assert first[0].segment_id == parsed.segments[0].segment_id
    assert first[0].source_id == parsed.source.source_id
    assert first[0].message_id == parsed.segments[0].message_id
    assert first[0].speaker == "User"
    assert first[0].text == parsed.segments[0].text
    assert first[0].start_index == parsed.segments[0].start_index
    assert first[0].end_index == parsed.segments[0].end_index
    assert first[0].segment_index == 0
    assert first[0].source_path == parsed.source.path
    assert first[0].manifest_ref == parsed.manifest.raw_path
    assert REFINEMENT_SEGMENT_VERSION == "refinement-segment-v0"


def test_adapter_rejects_segments_from_a_different_source() -> None:
    parsed = parse_transcript_file(FIXTURE_ROOT / "sample_transcript.md")
    wrong_source = parsed.source.__class__(
        source_id="SRC-OTHER",
        source_type=parsed.source.source_type,
        path=parsed.source.path,
        title=parsed.source.title,
        created_at=parsed.source.created_at,
        imported_at=parsed.source.imported_at,
        import_status=parsed.source.import_status,
        parser_version=parsed.source.parser_version,
        raw_sha256=parsed.source.raw_sha256,
        message_count=parsed.source.message_count,
        segment_count=parsed.source.segment_count,
    )

    with pytest.raises(ValueError, match="source_id"):
        adapt_chat_segments(wrong_source, parsed.segments)


def test_refinement_chunks_are_deterministic_and_preserve_segment_references() -> None:
    parsed = parse_transcript_file(FIXTURE_ROOT / "sample_transcript.md")
    segment = adapt_chat_segments(parsed.source, parsed.segments, manifest=parsed.manifest)[0]

    first = chunk_refinement_segment(segment, max_words=4, overlap_words=1)
    second = chunk_refinement_segment(segment, max_words=4, overlap_words=1)

    assert first == second
    assert all(isinstance(chunk, RefinementChunk) for chunk in first)
    assert [chunk.chunk_id for chunk in first] == [
        f"{segment.segment_id}:chunk_0000",
        f"{segment.segment_id}:chunk_0001",
        f"{segment.segment_id}:chunk_0002",
    ]
    assert [chunk.chunk_index for chunk in first] == [0, 1, 2]
    assert [(chunk.start_word, chunk.end_word) for chunk in first] == [(0, 4), (3, 7), (6, 10)]
    assert first[0].segment_id == segment.segment_id
    assert first[0].source_id == segment.source_id
    assert first[0].message_id == segment.message_id
    assert first[0].speaker == segment.speaker
    assert first[0].source_path == segment.source_path
    assert first[0].manifest_ref == segment.manifest_ref
    assert first[0].normalized_terms == ("capture", "this", "local", "surface")
    assert REFINEMENT_CHUNK_VERSION == "refinement-chunk-v0"


def test_refinement_segments_convert_to_existing_retrieval_records() -> None:
    parsed = parse_transcript_file(FIXTURE_ROOT / "sample_transcript.md")
    segment = adapt_chat_segments(parsed.source, parsed.segments, manifest=parsed.manifest)[0]

    document = to_retrieval_document(segment)
    retrieval_chunks = to_retrieval_chunks(segment, max_words=4, overlap_words=1)

    assert isinstance(document, RetrievalDocument)
    assert document.document_id == segment.segment_id
    assert document.source_ref == segment.source_path
    assert document.text == segment.text
    assert document.metadata["source_id"] == segment.source_id
    assert document.metadata["refinement_segment_version"] == REFINEMENT_SEGMENT_VERSION
    assert all(isinstance(chunk, RetrievalChunk) for chunk in retrieval_chunks)
    assert [chunk.chunk_id for chunk in retrieval_chunks] == [
        f"{segment.segment_id}:chunk_0000",
        f"{segment.segment_id}:chunk_0001",
        f"{segment.segment_id}:chunk_0002",
    ]


def test_multiple_segments_chunk_in_stable_segment_order() -> None:
    parsed = parse_transcript_file(FIXTURE_ROOT / "sample_transcript.md")
    segments = adapt_chat_segments(parsed.source, parsed.segments, manifest=parsed.manifest)

    chunks = chunk_refinement_segments(segments, max_words=20)

    assert [chunk.segment_id for chunk in chunks] == [segment.segment_id for segment in segments]
    assert [chunk.chunk_index for chunk in chunks] == [0, 0, 0]
