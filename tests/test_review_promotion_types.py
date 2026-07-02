from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_refinement import EvidenceLink  # noqa: E402
from ovis_review_promotion import (  # noqa: E402
    PROMOTION_CANDIDATE_VERSION,
    PROMOTION_GATE_POLICY_VERSION,
    PROMOTION_OUTPUT_VERSION,
    REVIEW_DECISION_VERSION,
    REVIEW_QUEUE_VERSION,
    REVIEW_ROUTE_CJ_CANDIDATE,
    REVIEW_ROUTE_DOCTRINE_CANDIDATE,
    REVIEW_STATE_APPROVED,
    REVIEW_STATE_BLOCKED_MISSING_EVIDENCE,
    REVIEW_STATE_PENDING,
    REVIEW_STATE_PROMOTED_LOCAL,
    PromotionCandidate,
    PromotionGateResult,
    PromotionOutput,
    ReviewDecision,
    ReviewQueue,
    build_candidate_id,
    build_decision_id,
    build_promotion_id,
    build_queue_id,
    promotion_candidate_from_dict,
    promotion_gate_result,
    promotion_gate_result_from_dict,
    promotion_output_from_dict,
    record_to_dict,
    review_decision_from_dict,
    review_queue_from_dict,
    validate_candidate_evidence,
)


def _evidence_link() -> EvidenceLink:
    return EvidenceLink(
        evidence_id="EVID-VALIDATION-0001",
        source_ref="tests/fixtures/refinement/validation_pack.md#SEG-VALIDATION-0000",
        source_id="SRC-VALIDATION-PACK",
        segment_id="SEG-VALIDATION-0000",
        chunk_id="SEG-VALIDATION-0000:chunk_0000",
        path="tests/fixtures/refinement/validation_pack.md",
        quote_span_or_chunk_id="SEG-VALIDATION-0000:chunk_0000",
        snippet="Update the CJ register and retrieval evidence ledger before validation close.",
        created_by="evidence-link-v0",
        manifest_ref="tests/fixtures/refinement/validation_manifest.json",
    )


def _candidate() -> PromotionCandidate:
    evidence_links = (_evidence_link(),)
    candidate_id = build_candidate_id(
        source_id="SRC-VALIDATION-PACK",
        segment_id="SEG-VALIDATION-0000",
        chunk_id="SEG-VALIDATION-0000:chunk_0000",
        boundary="OVIS",
        recommended_route=REVIEW_ROUTE_CJ_CANDIDATE,
        evidence_links=evidence_links,
    )
    return PromotionCandidate(
        candidate_id=candidate_id,
        source_type="b3_refinement_chunk",
        source_id="SRC-VALIDATION-PACK",
        segment_id="SEG-VALIDATION-0000",
        chunk_id="SEG-VALIDATION-0000:chunk_0000",
        boundary="OVIS",
        recommended_route=REVIEW_ROUTE_CJ_CANDIDATE,
        candidate_title="Update CJ register evidence",
        candidate_text="Update the CJ register and retrieval evidence ledger before validation close.",
        classifier_reason="Matched OVIS evidence and register rules.",
        ambiguity_status=None,
        evidence_links=evidence_links,
    )


def test_candidate_preserves_b3_source_route_and_evidence_fields() -> None:
    candidate = _candidate()

    assert isinstance(candidate, PromotionCandidate)
    assert candidate.candidate_id.startswith("CAND-")
    assert candidate.source_id == "SRC-VALIDATION-PACK"
    assert candidate.segment_id == "SEG-VALIDATION-0000"
    assert candidate.chunk_id == "SEG-VALIDATION-0000:chunk_0000"
    assert candidate.boundary == "OVIS"
    assert candidate.recommended_route == REVIEW_ROUTE_CJ_CANDIDATE
    assert candidate.classifier_reason == "Matched OVIS evidence and register rules."
    assert candidate.ambiguity_status is None
    assert candidate.evidence_links == (_evidence_link(),)
    assert candidate.decision_status == REVIEW_STATE_PENDING
    assert candidate.candidate_version == PROMOTION_CANDIDATE_VERSION


def test_candidate_ids_are_deterministic() -> None:
    first = _candidate()
    second = _candidate()

    assert first.candidate_id == second.candidate_id
    assert first == second


def test_review_queue_preserves_counts_and_manifest_refs() -> None:
    candidate = _candidate()
    queue = ReviewQueue(
        queue_id=build_queue_id(generated_from="b3-validation-pack", candidate_ids=(candidate.candidate_id,)),
        generated_from="b3-validation-pack",
        candidate_ids=(candidate.candidate_id,),
        candidate_count=1,
        boundary_counts={"OVIS": 1},
        pending_count=1,
        source_manifest_refs=("tests/fixtures/refinement/validation_manifest.json",),
    )

    assert queue.queue_id.startswith("QUEUE-")
    assert queue.candidate_ids == (candidate.candidate_id,)
    assert queue.candidate_count == 1
    assert queue.boundary_counts == {"OVIS": 1}
    assert queue.pending_count == 1
    assert queue.source_manifest_refs == ("tests/fixtures/refinement/validation_manifest.json",)
    assert queue.queue_version == REVIEW_QUEUE_VERSION


def test_review_decision_preserves_status_route_reviewer_and_evidence() -> None:
    candidate = _candidate()
    decision = ReviewDecision(
        decision_id=build_decision_id(
            candidate_id=candidate.candidate_id,
            decision=REVIEW_STATE_APPROVED,
            route=REVIEW_ROUTE_CJ_CANDIDATE,
            reviewer="operator",
            evidence_links=candidate.evidence_links,
        ),
        candidate_id=candidate.candidate_id,
        decision=REVIEW_STATE_APPROVED,
        route=REVIEW_ROUTE_CJ_CANDIDATE,
        reviewer="operator",
        reason_or_notes="Approved for local CJ candidate drafting.",
        evidence_links=candidate.evidence_links,
        previous_status=REVIEW_STATE_PENDING,
        new_status=REVIEW_STATE_APPROVED,
        promotion_output_ref=None,
    )

    assert isinstance(decision, ReviewDecision)
    assert decision.decision_id.startswith("DECISION-")
    assert decision.candidate_id == candidate.candidate_id
    assert decision.route == REVIEW_ROUTE_CJ_CANDIDATE
    assert decision.reviewer == "operator"
    assert decision.evidence_links == candidate.evidence_links
    assert decision.previous_status == REVIEW_STATE_PENDING
    assert decision.new_status == REVIEW_STATE_APPROVED
    assert decision.decision_version == REVIEW_DECISION_VERSION


def test_promotion_output_and_gate_prechecks_are_local_records() -> None:
    candidate = _candidate()
    decision_id = build_decision_id(
        candidate_id=candidate.candidate_id,
        decision=REVIEW_STATE_APPROVED,
        route=REVIEW_ROUTE_CJ_CANDIDATE,
        reviewer="operator",
        evidence_links=candidate.evidence_links,
    )
    output = PromotionOutput(
        promotion_id=build_promotion_id(
            candidate_id=candidate.candidate_id,
            route=REVIEW_ROUTE_CJ_CANDIDATE,
            output_type="cj_candidate_markdown",
            decision_id=decision_id,
        ),
        candidate_id=candidate.candidate_id,
        route=REVIEW_ROUTE_CJ_CANDIDATE,
        boundary="OVIS",
        output_type="cj_candidate_markdown",
        output_path_or_ref="local/promotions/CAND.md",
        source_evidence_links=candidate.evidence_links,
        decision_id=decision_id,
        generated_by="promotion-output-v0",
        promotion_status=REVIEW_STATE_PROMOTED_LOCAL,
    )
    gate = promotion_gate_result(candidate, operator_decision_present=True)

    assert output.promotion_id.startswith("PROMO-")
    assert output.source_evidence_links == candidate.evidence_links
    assert output.promotion_version == PROMOTION_OUTPUT_VERSION
    assert isinstance(gate, PromotionGateResult)
    assert gate.allowed is True
    assert gate.blocked_reason is None
    assert gate.policy_version == PROMOTION_GATE_POLICY_VERSION


def test_gate_result_blocks_missing_evidence_and_operator_decision() -> None:
    candidate = _candidate()
    missing_evidence_candidate = PromotionCandidate(
        candidate_id="CAND-MISSING-EVIDENCE",
        source_type=candidate.source_type,
        source_id=candidate.source_id,
        segment_id=candidate.segment_id,
        chunk_id=candidate.chunk_id,
        boundary=candidate.boundary,
        recommended_route=REVIEW_ROUTE_DOCTRINE_CANDIDATE,
        candidate_title=candidate.candidate_title,
        candidate_text=candidate.candidate_text,
        classifier_reason=candidate.classifier_reason,
        ambiguity_status="Review / Ambiguous",
        evidence_links=(),
    )

    assert validate_candidate_evidence(missing_evidence_candidate) == ("evidence_links",)
    missing_evidence_gate = promotion_gate_result(missing_evidence_candidate, operator_decision_present=True)
    missing_operator_gate = promotion_gate_result(candidate)

    assert missing_evidence_gate.allowed is False
    assert missing_evidence_gate.blocked_reason == REVIEW_STATE_BLOCKED_MISSING_EVIDENCE
    assert missing_operator_gate.allowed is False
    assert missing_operator_gate.blocked_reason == "operator_decision_missing"


def test_serialization_round_trips_preserve_fields() -> None:
    candidate = _candidate()
    queue = ReviewQueue(
        queue_id=build_queue_id(generated_from="b3-validation-pack", candidate_ids=(candidate.candidate_id,)),
        generated_from="b3-validation-pack",
        candidate_ids=(candidate.candidate_id,),
        candidate_count=1,
        boundary_counts={"OVIS": 1},
        pending_count=1,
        source_manifest_refs=("tests/fixtures/refinement/validation_manifest.json",),
    )
    decision = ReviewDecision(
        decision_id=build_decision_id(
            candidate_id=candidate.candidate_id,
            decision=REVIEW_STATE_APPROVED,
            route=REVIEW_ROUTE_CJ_CANDIDATE,
            reviewer="operator",
            evidence_links=candidate.evidence_links,
        ),
        candidate_id=candidate.candidate_id,
        decision=REVIEW_STATE_APPROVED,
        route=REVIEW_ROUTE_CJ_CANDIDATE,
        reviewer="operator",
        reason_or_notes="Approved.",
        evidence_links=candidate.evidence_links,
        previous_status=REVIEW_STATE_PENDING,
        new_status=REVIEW_STATE_APPROVED,
    )
    output = PromotionOutput(
        promotion_id=build_promotion_id(
            candidate_id=candidate.candidate_id,
            route=REVIEW_ROUTE_CJ_CANDIDATE,
            output_type="cj_candidate_markdown",
            decision_id=decision.decision_id,
        ),
        candidate_id=candidate.candidate_id,
        route=REVIEW_ROUTE_CJ_CANDIDATE,
        boundary="OVIS",
        output_type="cj_candidate_markdown",
        output_path_or_ref="local/promotions/CAND.md",
        source_evidence_links=candidate.evidence_links,
        decision_id=decision.decision_id,
        generated_by="promotion-output-v0",
        promotion_status=REVIEW_STATE_PROMOTED_LOCAL,
    )
    gate = promotion_gate_result(candidate, operator_decision_present=True)

    assert promotion_candidate_from_dict(record_to_dict(candidate)) == candidate
    assert review_queue_from_dict(record_to_dict(queue)) == queue
    assert review_decision_from_dict(record_to_dict(decision)) == decision
    assert promotion_output_from_dict(record_to_dict(output)) == output
    assert promotion_gate_result_from_dict(record_to_dict(gate)) == gate
