from pathlib import Path
import socket
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_chat_ingestion import parse_transcript_file  # noqa: E402
from ovis_refinement import (  # noqa: E402
    AMBIGUITY_ROUTER_VERSION,
    BOUNDARY_CODEX_VITAE,
    BOUNDARY_LIFE_OPS,
    BOUNDARY_OVC,
    BOUNDARY_OVIS,
    BOUNDARY_REVIEW_AMBIGUOUS,
    CLASSIFIER_VERSION,
    AmbiguityRoute,
    BoundaryLabel,
    adapt_chat_segments,
    attach_classification_evidence,
    build_segment_evidence_link,
    classify_text,
    route_boundary_label,
    route_boundary_labels,
)


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "chat_ingestion"


def _fixture_segment():
    parsed = parse_transcript_file(FIXTURE_ROOT / "sample_transcript.md")
    return adapt_chat_segments(parsed.source, parsed.segments, manifest=parsed.manifest)[0]


def test_ambiguous_classifier_output_routes_to_review_with_evidence() -> None:
    segment = _fixture_segment()
    classification = classify_text(
        "Make the operating hub feel like a ritual threshold for every work session.",
        item_id=segment.segment_id,
    )
    evidence = attach_classification_evidence(classification, segment).evidence_link

    route = route_boundary_label(classification, evidence_link=evidence)

    assert isinstance(route, AmbiguityRoute)
    assert route.item_id == segment.segment_id
    assert route.source_id == segment.source_id
    assert route.segment_id_or_chunk_id == segment.segment_id
    assert route.route == BOUNDARY_REVIEW_AMBIGUOUS
    assert route.review_required is True
    assert route.evidence_id == evidence.evidence_id
    assert route.router_version == AMBIGUITY_ROUTER_VERSION
    assert BOUNDARY_OVIS in route.candidate_boundaries
    assert BOUNDARY_CODEX_VITAE in route.candidate_boundaries


def test_low_confidence_material_routes_to_review() -> None:
    segment = _fixture_segment()
    classification = BoundaryLabel(
        item_id=segment.segment_id,
        boundary=BOUNDARY_OVIS,
        confidence=0.5,
        reason="fixture low confidence",
        matched_rules=("OVIS-EVIDENCE",),
        classifier_version=CLASSIFIER_VERSION,
        is_ambiguous=False,
        review_required=False,
        scores={BOUNDARY_OVIS: 2, BOUNDARY_OVC: 0, BOUNDARY_CODEX_VITAE: 0, BOUNDARY_LIFE_OPS: 0},
    )
    evidence = build_segment_evidence_link(segment)

    route = route_boundary_label(classification, evidence_link=evidence)

    assert route.route == BOUNDARY_REVIEW_AMBIGUOUS
    assert route.review_required is True
    assert "confidence" in route.reason


def test_tied_boundary_scores_route_to_review() -> None:
    segment = _fixture_segment()
    classification = BoundaryLabel(
        item_id=segment.segment_id,
        boundary=BOUNDARY_OVIS,
        confidence=0.5,
        reason="fixture tie",
        matched_rules=("OVIS-RUNTIME", "CODEX-DOCTRINE"),
        classifier_version=CLASSIFIER_VERSION,
        is_ambiguous=False,
        review_required=False,
        scores={BOUNDARY_OVIS: 3, BOUNDARY_CODEX_VITAE: 3, BOUNDARY_OVC: 0, BOUNDARY_LIFE_OPS: 0},
    )

    route = route_boundary_label(classification, evidence_link=build_segment_evidence_link(segment))

    assert route.route == BOUNDARY_REVIEW_AMBIGUOUS
    assert route.review_required is True
    assert "mixed-boundary margin" in route.reason
    assert route.candidate_boundaries[:2] == (BOUNDARY_CODEX_VITAE, BOUNDARY_OVIS)


def test_mixed_ovc_life_ops_scores_route_to_review() -> None:
    segment = _fixture_segment()
    classification = classify_text(
        "My poor trade entries are probably a discipline problem, so build a morning routine around entry patience.",
        item_id=segment.segment_id,
    )

    route = route_boundary_label(classification, evidence_link=build_segment_evidence_link(segment))

    assert route.route == BOUNDARY_REVIEW_AMBIGUOUS
    assert route.review_required is True
    assert BOUNDARY_OVC in route.candidate_boundaries
    assert BOUNDARY_LIFE_OPS in route.candidate_boundaries


def test_missing_evidence_routes_to_review() -> None:
    classification = classify_text(
        "Define how local retrieval results preserve citation evidence for later review.",
        item_id="SEG-MISSING-EVIDENCE",
    )

    route = route_boundary_label(classification)

    assert route.route == BOUNDARY_REVIEW_AMBIGUOUS
    assert route.review_required is True
    assert route.source_id is None
    assert route.evidence_id is None
    assert "missing evidence link" in route.reason


def test_route_boundary_labels_is_deterministic() -> None:
    segment = _fixture_segment()
    classification = classify_text(
        "Define how local retrieval results preserve citation evidence for later review.",
        item_id=segment.segment_id,
    )
    evidence = build_segment_evidence_link(segment)

    first = route_boundary_labels((classification,), evidence_links={classification.item_id: evidence})
    second = route_boundary_labels((classification,), evidence_links={classification.item_id: evidence})

    assert first == second
    assert first[0].route == classification.boundary
    assert first[0].review_required is False


def test_ambiguity_routing_does_not_require_socket_access(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_socket(*args: object, **kwargs: object) -> None:
        raise AssertionError("ambiguity routing attempted socket access")

    monkeypatch.setattr(socket, "socket", fail_socket)
    segment = _fixture_segment()
    classification = classify_text("This belongs in the system somewhere, probably as a task or doctrine.", item_id=segment.segment_id)

    route = route_boundary_label(classification, evidence_link=build_segment_evidence_link(segment))

    assert route.route == BOUNDARY_REVIEW_AMBIGUOUS
