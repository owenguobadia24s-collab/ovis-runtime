from pathlib import Path
import socket
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_chat_ingestion import parse_transcript_file  # noqa: E402
from ovis_refinement import (  # noqa: E402
    EVIDENCE_LINK_VERSION,
    BOUNDARY_OVIS,
    BoundaryLabel,
    ClassifiedEvidenceResult,
    EvidenceLink,
    SearchEvidenceResult,
    adapt_chat_segments,
    attach_classification_evidence,
    attach_search_evidence,
    attach_search_results_evidence,
    build_chat_retrieval_index,
    build_chunk_evidence_link,
    build_segment_evidence_link,
    chunk_refinement_segments,
    classify_text,
)


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "chat_ingestion"


def _fixture_segments_and_chunks():
    parsed = parse_transcript_file(FIXTURE_ROOT / "sample_transcript.md")
    segments = adapt_chat_segments(parsed.source, parsed.segments, manifest=parsed.manifest)
    chunks = chunk_refinement_segments(segments, max_words=20)
    return segments, chunks


def test_segment_evidence_link_is_stable_and_source_preserving() -> None:
    segments, _ = _fixture_segments_and_chunks()

    first = build_segment_evidence_link(segments[0])
    second = build_segment_evidence_link(segments[0])

    assert first == second
    assert isinstance(first, EvidenceLink)
    assert first.evidence_id.startswith("EVID-")
    assert first.source_id == segments[0].source_id
    assert first.segment_id == segments[0].segment_id
    assert first.chunk_id is None
    assert first.path == segments[0].source_path
    assert first.source_ref == f"{segments[0].source_path}#{segments[0].segment_id}"
    assert first.quote_span_or_chunk_id == f"chars:{segments[0].start_index}-{segments[0].end_index}"
    assert first.snippet == segments[0].text
    assert first.created_by == EVIDENCE_LINK_VERSION
    assert first.manifest_ref == segments[0].manifest_ref


def test_chunk_evidence_link_is_stable_and_source_preserving() -> None:
    _, chunks = _fixture_segments_and_chunks()

    link = build_chunk_evidence_link(chunks[0])

    assert link.source_id == chunks[0].source_id
    assert link.segment_id == chunks[0].segment_id
    assert link.chunk_id == chunks[0].chunk_id
    assert link.path == chunks[0].source_path
    assert link.source_ref == f"{chunks[0].source_path}#{chunks[0].chunk_id}"
    assert link.quote_span_or_chunk_id == f"{chunks[0].chunk_id}:words:{chunks[0].start_word}-{chunks[0].end_word}"
    assert link.snippet == chunks[0].text


def test_classification_result_keeps_evidence_link() -> None:
    segments, _ = _fixture_segments_and_chunks()
    classification = classify_text(
        "Define how local retrieval results preserve citation evidence for later review.",
        item_id=segments[0].segment_id,
    )

    result = attach_classification_evidence(classification, segments[0])

    assert isinstance(result, ClassifiedEvidenceResult)
    assert result.classification == classification
    assert result.classification.boundary == BOUNDARY_OVIS
    assert result.evidence_link.segment_id == segments[0].segment_id
    assert result.evidence_link.source_id == segments[0].source_id
    assert result.evidence_link.path == segments[0].source_path


def test_classification_evidence_rejects_mismatched_item_id() -> None:
    segments, _ = _fixture_segments_and_chunks()
    classification = BoundaryLabel(
        item_id="not-the-segment",
        boundary=BOUNDARY_OVIS,
        confidence=1.0,
        reason="fixture",
        matched_rules=("fixture-rule",),
        classifier_version="fixture",
        is_ambiguous=False,
        review_required=False,
        scores={BOUNDARY_OVIS: 1},
    )

    with pytest.raises(ValueError, match="item_id"):
        attach_classification_evidence(classification, segments[0])


def test_every_search_result_keeps_evidence_link() -> None:
    _, chunks = _fixture_segments_and_chunks()
    search_results = build_chat_retrieval_index(chunks).search("local surface")

    evidence_results = attach_search_results_evidence(search_results)

    assert len(evidence_results) == len(search_results) == 1
    assert all(isinstance(result, SearchEvidenceResult) for result in evidence_results)
    for search_result, evidence_result in zip(search_results, evidence_results):
        assert evidence_result.search_result == search_result
        assert evidence_result.evidence_link.chunk_id == search_result.chunk_id
        assert evidence_result.evidence_link.segment_id == search_result.segment_id
        assert evidence_result.evidence_link.source_id == search_result.source_id
        assert evidence_result.evidence_link.path == search_result.source_path
        assert evidence_result.evidence_link.quote_span_or_chunk_id == search_result.chunk_id
        assert evidence_result.evidence_link.snippet == search_result.snippet


def test_single_search_evidence_link_is_available() -> None:
    _, chunks = _fixture_segments_and_chunks()
    search_result = build_chat_retrieval_index(chunks).search("classification")[0]

    evidence_result = attach_search_evidence(search_result)

    assert evidence_result.evidence_link.chunk_id == search_result.chunk_id
    assert evidence_result.evidence_link.created_by == EVIDENCE_LINK_VERSION


def test_evidence_linking_does_not_require_socket_access(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_socket(*args: object, **kwargs: object) -> None:
        raise AssertionError("evidence linking attempted socket access")

    monkeypatch.setattr(socket, "socket", fail_socket)
    segments, chunks = _fixture_segments_and_chunks()

    assert build_segment_evidence_link(segments[0]).source_id == segments[0].source_id
    assert build_chunk_evidence_link(chunks[0]).chunk_id == chunks[0].chunk_id
