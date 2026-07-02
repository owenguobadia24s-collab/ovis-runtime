from pathlib import Path
import socket
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_refinement import (  # noqa: E402
    BOUNDARY_CODEX_VITAE,
    BOUNDARY_GENERAL_INQUIRY,
    BOUNDARY_LABELS,
    BOUNDARY_LIFE_OPS,
    BOUNDARY_OVC,
    BOUNDARY_OVIS,
    BOUNDARY_REVIEW_AMBIGUOUS,
    EvidenceLink,
)
from ovis_review_promotion import (  # noqa: E402
    REVIEW_DECISION_APPROVE,
    REVIEW_DECISION_ARCHIVE,
    REVIEW_DECISION_DISCARD,
    REVIEW_DECISION_REVIEW_LATER,
    REVIEW_ROUTE_ARCHIVE_NOTE,
    REVIEW_ROUTE_CJ_CANDIDATE,
    REVIEW_ROUTE_DISCARD,
    REVIEW_ROUTE_DOCTRINE_CANDIDATE,
    REVIEW_ROUTE_OVC_SPEC_CANDIDATE,
    REVIEW_ROUTE_REVIEW_LATER,
    REVIEW_ROUTE_ROUTINE_ACTION_CANDIDATE,
    REVIEW_STATE_BLOCKED_MISSING_EVIDENCE,
    REVIEW_STATE_PENDING,
    REVIEW_STATE_PROMOTED_LOCAL,
    PromotionCandidate,
    ReviewQueue,
    build_candidate_id,
    build_queue_id,
    create_local_promotion_output,
    record_review_decision,
)
from ovis_operating_hub import (  # noqa: E402
    DEFAULT_BOUNDARIES,
    HUB_STATUS_VERSION,
    PROJECT_STATUS_VERSION,
    REVIEW_SUMMARY_VERSION,
    HubStatus,
    ProjectStatus,
    ReviewSummary,
    build_hub_status,
    build_project_statuses,
    build_review_summary,
    record_to_dict,
)


def _evidence_link(boundary: str, index: int) -> EvidenceLink:
    segment_id = f"SEG-HUB-{index:04d}"
    chunk_id = f"{segment_id}:chunk_0000"
    return EvidenceLink(
        evidence_id=f"EVID-HUB-{index:04d}",
        source_ref=f"tests/fixtures/operating_hub/source.md#{chunk_id}",
        source_id="SRC-HUB-FIXTURE",
        segment_id=segment_id,
        chunk_id=chunk_id,
        path="tests/fixtures/operating_hub/source.md",
        quote_span_or_chunk_id=chunk_id,
        snippet=f"{boundary} safe operating hub fixture candidate.",
        created_by="evidence-link-v0",
        manifest_ref="tests/fixtures/operating_hub/manifest.json",
    )


def _candidate(
    boundary: str,
    index: int,
    route: str,
    *,
    status: str = REVIEW_STATE_PENDING,
    evidence_links: tuple[EvidenceLink, ...] | None = None,
) -> PromotionCandidate:
    links = (_evidence_link(boundary, index),) if evidence_links is None else evidence_links
    segment_id = f"SEG-HUB-{index:04d}"
    chunk_id = f"{segment_id}:chunk_0000"
    candidate_id = build_candidate_id(
        source_id="SRC-HUB-FIXTURE",
        segment_id=segment_id,
        chunk_id=chunk_id,
        boundary=boundary,
        recommended_route=route,
        evidence_links=links,
    )
    return PromotionCandidate(
        candidate_id=candidate_id,
        source_type="b4_review_fixture",
        source_id="SRC-HUB-FIXTURE",
        segment_id=segment_id,
        chunk_id=chunk_id,
        boundary=boundary,
        recommended_route=route,
        candidate_title=f"{boundary} hub fixture candidate",
        candidate_text=f"{boundary} safe operating hub fixture candidate.",
        classifier_reason=f"Matched {boundary} fixture rule.",
        ambiguity_status=BOUNDARY_REVIEW_AMBIGUOUS if boundary == BOUNDARY_REVIEW_AMBIGUOUS else None,
        evidence_links=links,
        decision_status=status,
    )


def _fixture_records() -> tuple[tuple[PromotionCandidate, ...], tuple[object, ...], tuple[object, ...], tuple[ReviewQueue, ...]]:
    ovis = _candidate(BOUNDARY_OVIS, 1, REVIEW_ROUTE_CJ_CANDIDATE)
    ovc = _candidate(BOUNDARY_OVC, 2, REVIEW_ROUTE_OVC_SPEC_CANDIDATE)
    codex = _candidate(BOUNDARY_CODEX_VITAE, 3, REVIEW_ROUTE_DOCTRINE_CANDIDATE)
    life_ops = _candidate(BOUNDARY_LIFE_OPS, 4, REVIEW_ROUTE_ROUTINE_ACTION_CANDIDATE)
    general = _candidate(BOUNDARY_GENERAL_INQUIRY, 5, REVIEW_ROUTE_ARCHIVE_NOTE)
    ambiguous = _candidate(
        BOUNDARY_REVIEW_AMBIGUOUS,
        6,
        REVIEW_ROUTE_REVIEW_LATER,
        status=REVIEW_STATE_BLOCKED_MISSING_EVIDENCE,
        evidence_links=(),
    )
    decisions = (
        record_review_decision(
            ovc,
            decision=REVIEW_DECISION_APPROVE,
            reviewer="operator",
            reason_or_notes="Approved local OVC spec candidate.",
        ),
        record_review_decision(
            codex,
            decision=REVIEW_DECISION_ARCHIVE,
            reviewer="operator",
            reason_or_notes="Archive symbolic note.",
        ),
        record_review_decision(
            life_ops,
            decision=REVIEW_DECISION_DISCARD,
            route=REVIEW_ROUTE_DISCARD,
            reviewer="operator",
            reason_or_notes="Discard duplicate routine.",
        ),
        record_review_decision(
            general,
            decision=REVIEW_DECISION_REVIEW_LATER,
            reviewer="operator",
            reason_or_notes="Review later as possible evidence.",
        ),
    )
    output = create_local_promotion_output(
        ovc,
        decisions[0],
        output_type="ovc_spec_candidate_markdown",
        output_path_or_ref="local/promotions/OVC-HUB.md",
    )
    candidates = (ovis, ovc, codex, life_ops, general, ambiguous)
    queue = ReviewQueue(
        queue_id=build_queue_id(generated_from="hub-fixture", candidate_ids=tuple(candidate.candidate_id for candidate in candidates)),
        generated_from="hub-fixture",
        candidate_ids=tuple(candidate.candidate_id for candidate in candidates),
        candidate_count=len(candidates),
        boundary_counts={boundary: 1 for boundary in BOUNDARY_LABELS},
        pending_count=1,
        source_manifest_refs=("tests/fixtures/operating_hub/manifest.json",),
    )
    return candidates, decisions, (output,), (queue,)


def test_project_statuses_include_all_six_boundaries_with_counts() -> None:
    candidates, decisions, outputs, _queues = _fixture_records()

    statuses = build_project_statuses(candidates, decisions=decisions, promotion_outputs=outputs, open_cj_counts={BOUNDARY_OVIS: 1})
    by_boundary = {status.boundary: status for status in statuses}

    assert tuple(by_boundary) == DEFAULT_BOUNDARIES
    assert tuple(by_boundary) == BOUNDARY_LABELS
    assert all(isinstance(status, ProjectStatus) for status in statuses)
    assert by_boundary[BOUNDARY_OVIS].pending_review_count == 1
    assert by_boundary[BOUNDARY_OVIS].open_cj_count == 1
    assert by_boundary[BOUNDARY_OVC].approved_count == 1
    assert by_boundary[BOUNDARY_OVC].promoted_local_count == 1
    assert by_boundary[BOUNDARY_CODEX_VITAE].archived_count == 1
    assert by_boundary[BOUNDARY_LIFE_OPS].discarded_count == 1
    assert by_boundary[BOUNDARY_GENERAL_INQUIRY].review_later_count == 1
    assert by_boundary[BOUNDARY_REVIEW_AMBIGUOUS].blocked_count == 1
    assert by_boundary[BOUNDARY_OVIS].status_version == PROJECT_STATUS_VERSION


def test_review_summary_preserves_queue_refs_and_boundary_counts() -> None:
    candidates, decisions, outputs, queues = _fixture_records()

    summary = build_review_summary(candidates, decisions=decisions, promotion_outputs=outputs, review_queues=queues)

    assert isinstance(summary, ReviewSummary)
    assert summary.total_candidates == 6
    assert summary.pending_count == 1
    assert summary.approved_count == 1
    assert summary.archived_count == 1
    assert summary.discarded_count == 1
    assert summary.review_later_count == 1
    assert summary.blocked_count == 1
    assert summary.promoted_local_count == 1
    assert summary.boundary_counts == {boundary: 1 for boundary in sorted(BOUNDARY_LABELS)}
    assert summary.source_queue_refs == (queues[0].queue_id,)
    assert summary.summary_version == REVIEW_SUMMARY_VERSION


def test_hub_status_is_deterministic_and_evidence_aware() -> None:
    candidates, decisions, outputs, queues = _fixture_records()

    first = build_hub_status(
        candidates,
        decisions=decisions,
        promotion_outputs=outputs,
        review_queues=queues,
        open_cj_counts={BOUNDARY_OVIS: 1},
        generated_from=("tests/fixtures/operating_hub/review_queue_sample.json",),
        active_bundle="Bundle 5 - Operating Hub v0.1",
        active_cj="CJ-B5-002_PROJECT_STATUS_GENERATOR",
        validation_posture="known_pass",
    )
    second = build_hub_status(
        tuple(reversed(candidates)),
        decisions=tuple(reversed(decisions)),
        promotion_outputs=tuple(reversed(outputs)),
        review_queues=queues,
        open_cj_counts={BOUNDARY_OVIS: 1},
        generated_from=("tests/fixtures/operating_hub/review_queue_sample.json",),
        active_bundle="Bundle 5 - Operating Hub v0.1",
        active_cj="CJ-B5-002_PROJECT_STATUS_GENERATOR",
        validation_posture="known_pass",
    )

    assert isinstance(first, HubStatus)
    assert first == second
    assert first.hub_version == HUB_STATUS_VERSION
    assert first.external_side_effects == "disabled"
    assert first.next_action == "Review / Ambiguous: repair blocked evidence."
    assert "tests/fixtures/operating_hub/review_queue_sample.json" in first.source_refs
    assert "tests/fixtures/operating_hub/source.md#SEG-HUB-0001:chunk_0000" in first.source_refs
    assert record_to_dict(first)["review_summary"]["total_candidates"] == 6


def test_status_generation_does_not_require_socket_access(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_socket(*args: object, **kwargs: object) -> None:
        raise AssertionError("operating hub status attempted socket access")

    monkeypatch.setattr(socket, "socket", fail_socket)
    candidates, decisions, outputs, queues = _fixture_records()

    status = build_hub_status(candidates, decisions=decisions, promotion_outputs=outputs, review_queues=queues)

    assert status.review_summary.total_candidates == 6
