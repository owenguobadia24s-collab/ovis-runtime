import json
from pathlib import Path
import socket
import sys
import tempfile

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_refinement import EvidenceLink  # noqa: E402
from ovis_review_promotion import (  # noqa: E402
    REVIEW_DECISION_APPROVE,
    REVIEW_DECISION_ARCHIVE,
    REVIEW_DECISION_BLOCK_MISSING_EVIDENCE,
    REVIEW_DECISION_DISCARD,
    REVIEW_DECISION_REVIEW_LATER,
    REVIEW_ROUTE_CJ_CANDIDATE,
    REVIEW_ROUTE_DISCARD,
    REVIEW_ROUTE_REVIEW_LATER,
    REVIEW_STATE_APPROVED,
    REVIEW_STATE_ARCHIVED,
    REVIEW_STATE_BLOCKED_MISSING_EVIDENCE,
    REVIEW_STATE_DISCARDED,
    REVIEW_STATE_PENDING,
    REVIEW_STATE_PROMOTED_LOCAL,
    REVIEW_STATE_REVIEW_LATER,
    PromotionCandidate,
    build_candidate_id,
    build_review_queue,
    create_local_promotion_output,
    record_review_decision,
    record_to_dict,
    render_review_queue_json,
    validate_candidate_evidence,
    write_review_queue_files,
)


def _evidence_link() -> EvidenceLink:
    return EvidenceLink(
        evidence_id="EVID-WORKFLOW-0001",
        source_ref="tests/fixtures/review_promotion/source.md#SEG-WORKFLOW-0001:chunk_0000",
        source_id="SRC-WORKFLOW-FIXTURE",
        segment_id="SEG-WORKFLOW-0001",
        chunk_id="SEG-WORKFLOW-0001:chunk_0000",
        path="tests/fixtures/review_promotion/source.md",
        quote_span_or_chunk_id="SEG-WORKFLOW-0001:chunk_0000",
        snippet="Approve this local CJ candidate only after evidence review.",
        created_by="evidence-link-v0",
        manifest_ref="tests/fixtures/review_promotion/manifest.json",
    )


def _candidate(*, evidence_links: tuple[EvidenceLink, ...] | None = None) -> PromotionCandidate:
    links = (_evidence_link(),) if evidence_links is None else evidence_links
    candidate_id = build_candidate_id(
        source_id="SRC-WORKFLOW-FIXTURE",
        segment_id="SEG-WORKFLOW-0001",
        chunk_id="SEG-WORKFLOW-0001:chunk_0000",
        boundary="OVIS",
        recommended_route=REVIEW_ROUTE_CJ_CANDIDATE,
        evidence_links=links,
    )
    return PromotionCandidate(
        candidate_id=candidate_id,
        source_type="b3_classified_evidence",
        source_id="SRC-WORKFLOW-FIXTURE",
        segment_id="SEG-WORKFLOW-0001",
        chunk_id="SEG-WORKFLOW-0001:chunk_0000",
        boundary="OVIS",
        recommended_route=REVIEW_ROUTE_CJ_CANDIDATE,
        candidate_title="Prepare local CJ candidate",
        candidate_text="Approve this local CJ candidate only after evidence review.",
        classifier_reason="Matched OVIS CJ/task route with cited source evidence.",
        ambiguity_status=None,
        evidence_links=links,
    )


def test_queue_writing_and_json_preserve_candidate_source_and_boundary_fields() -> None:
    candidate = _candidate()
    queue = build_review_queue((candidate,), generated_from="workflow-fixture")

    queue_json = render_review_queue_json(queue, (candidate,))
    with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as temp_dir:
        files = write_review_queue_files(queue, (candidate,), temp_dir, basename="workflow_queue")
        persisted = json.loads(Path(files.json_path).read_text(encoding="utf-8"))

    assert queue_json == persisted
    assert persisted["queue"]["candidate_ids"] == [candidate.candidate_id]
    assert persisted["queue"]["boundary_counts"] == {"OVIS": 1}
    assert persisted["candidates"][0]["source_id"] == candidate.source_id
    assert persisted["candidates"][0]["evidence_links"][0]["evidence_id"] == "EVID-WORKFLOW-0001"


def test_approve_decision_records_operator_route_evidence_and_notes() -> None:
    candidate = _candidate()

    decision = record_review_decision(
        candidate,
        decision=REVIEW_DECISION_APPROVE,
        reviewer="operator",
        reason_or_notes="Approved for local CJ candidate output.",
    )

    assert decision.decision_id.startswith("DECISION-")
    assert decision.decision == REVIEW_DECISION_APPROVE
    assert decision.route == REVIEW_ROUTE_CJ_CANDIDATE
    assert decision.reviewer == "operator"
    assert decision.reason_or_notes == "Approved for local CJ candidate output."
    assert decision.evidence_links == candidate.evidence_links
    assert decision.previous_status == REVIEW_STATE_PENDING
    assert decision.new_status == REVIEW_STATE_APPROVED


def test_archive_discard_and_review_later_preserve_audit_evidence() -> None:
    candidate = _candidate()

    archived = record_review_decision(
        candidate,
        decision=REVIEW_DECISION_ARCHIVE,
        reviewer="operator",
        reason_or_notes="Useful reference, not promotable now.",
    )
    discarded = record_review_decision(
        candidate,
        decision=REVIEW_DECISION_DISCARD,
        reviewer="operator",
        reason_or_notes="Duplicate candidate; discard after review.",
    )
    later = record_review_decision(
        candidate,
        decision=REVIEW_DECISION_REVIEW_LATER,
        reviewer="operator",
        reason_or_notes="Hold pending route clarification.",
    )

    assert archived.new_status == REVIEW_STATE_ARCHIVED
    assert archived.route == "archive_note"
    assert archived.evidence_links == candidate.evidence_links
    assert discarded.new_status == REVIEW_STATE_DISCARDED
    assert discarded.route == REVIEW_ROUTE_DISCARD
    assert discarded.reason_or_notes.startswith("Duplicate")
    assert discarded.evidence_links == candidate.evidence_links
    assert later.new_status == REVIEW_STATE_REVIEW_LATER
    assert later.route == REVIEW_ROUTE_REVIEW_LATER
    assert later.evidence_links == candidate.evidence_links


def test_missing_evidence_blocks_promotion_and_preserves_audit_record() -> None:
    candidate = _candidate(evidence_links=())

    decision = record_review_decision(
        candidate,
        decision=REVIEW_DECISION_BLOCK_MISSING_EVIDENCE,
        reviewer="operator",
        reason_or_notes="Missing source evidence blocks promotion.",
    )

    assert validate_candidate_evidence(candidate) == ("evidence_links",)
    assert decision.new_status == REVIEW_STATE_BLOCKED_MISSING_EVIDENCE
    assert decision.evidence_links == ()
    assert record_to_dict(decision)["reason_or_notes"] == "Missing source evidence blocks promotion."
    with pytest.raises(ValueError, match="local promotion output requires an approved decision"):
        create_local_promotion_output(
            candidate,
            decision,
            output_type="cj_candidate_markdown",
            output_path_or_ref="local/promotions/CAND-WORKFLOW.md",
        )


def test_block_missing_evidence_decision_requires_missing_evidence() -> None:
    with pytest.raises(ValueError, match="requires missing evidence"):
        record_review_decision(
            _candidate(),
            decision=REVIEW_DECISION_BLOCK_MISSING_EVIDENCE,
            reviewer="operator",
            reason_or_notes="Should not block a fully cited candidate.",
        )


def test_promote_local_requires_approved_decision_and_preserves_evidence_ref() -> None:
    candidate = _candidate()
    archive_decision = record_review_decision(
        candidate,
        decision=REVIEW_DECISION_ARCHIVE,
        reviewer="operator",
        reason_or_notes="Not approved.",
    )
    approval_decision = record_review_decision(
        candidate,
        decision=REVIEW_DECISION_APPROVE,
        reviewer="operator",
        reason_or_notes="Approved for local candidate output.",
    )

    with pytest.raises(ValueError, match="requires an approved decision"):
        create_local_promotion_output(
            candidate,
            archive_decision,
            output_type="cj_candidate_markdown",
            output_path_or_ref="local/promotions/CAND-WORKFLOW.md",
        )

    output = create_local_promotion_output(
        candidate,
        approval_decision,
        output_type="cj_candidate_markdown",
        output_path_or_ref="local/promotions/CAND-WORKFLOW.md",
    )

    assert output.promotion_id.startswith("PROMO-")
    assert output.candidate_id == candidate.candidate_id
    assert output.route == REVIEW_ROUTE_CJ_CANDIDATE
    assert output.source_evidence_links == candidate.evidence_links
    assert output.decision_id == approval_decision.decision_id
    assert output.promotion_status == REVIEW_STATE_PROMOTED_LOCAL
    assert output.output_path_or_ref == "local/promotions/CAND-WORKFLOW.md"


def test_workflow_does_not_require_socket_access(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_socket(*args: object, **kwargs: object) -> None:
        raise AssertionError("review workflow attempted socket access")

    monkeypatch.setattr(socket, "socket", fail_socket)
    candidate = _candidate()
    decision = record_review_decision(
        candidate,
        decision=REVIEW_DECISION_APPROVE,
        reviewer="operator",
        reason_or_notes="Approved without external calls.",
    )
    output = create_local_promotion_output(
        candidate,
        decision,
        output_type="cj_candidate_markdown",
        output_path_or_ref="local/promotions/CAND-WORKFLOW.md",
    )

    assert output.source_evidence_links == candidate.evidence_links
