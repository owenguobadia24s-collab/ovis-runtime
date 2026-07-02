"""Pure local review workflow helpers for operator decisions."""

from __future__ import annotations

from .types import (
    REVIEW_ROUTE_ARCHIVE_NOTE,
    REVIEW_ROUTE_DISCARD,
    REVIEW_ROUTE_REVIEW_LATER,
    REVIEW_STATE_APPROVED,
    REVIEW_STATE_ARCHIVED,
    REVIEW_STATE_BLOCKED_MISSING_EVIDENCE,
    REVIEW_STATE_DISCARDED,
    REVIEW_STATE_PROMOTED_LOCAL,
    REVIEW_STATE_REVIEW_LATER,
    PromotionCandidate,
    PromotionOutput,
    ReviewDecision,
    build_decision_id,
    build_promotion_id,
    promotion_gate_result,
    validate_candidate_evidence,
)


REVIEW_DECISION_APPROVE = "approve"
REVIEW_DECISION_ARCHIVE = "archive"
REVIEW_DECISION_DISCARD = "discard"
REVIEW_DECISION_REVIEW_LATER = "review_later"
REVIEW_DECISION_BLOCK_MISSING_EVIDENCE = "block_missing_evidence"
REVIEW_DECISION_PROMOTE_LOCAL = "promote_local"

REVIEW_DECISIONS = (
    REVIEW_DECISION_APPROVE,
    REVIEW_DECISION_ARCHIVE,
    REVIEW_DECISION_DISCARD,
    REVIEW_DECISION_REVIEW_LATER,
    REVIEW_DECISION_BLOCK_MISSING_EVIDENCE,
    REVIEW_DECISION_PROMOTE_LOCAL,
)

_STATUS_BY_DECISION = {
    REVIEW_DECISION_APPROVE: REVIEW_STATE_APPROVED,
    REVIEW_DECISION_ARCHIVE: REVIEW_STATE_ARCHIVED,
    REVIEW_DECISION_DISCARD: REVIEW_STATE_DISCARDED,
    REVIEW_DECISION_REVIEW_LATER: REVIEW_STATE_REVIEW_LATER,
    REVIEW_DECISION_BLOCK_MISSING_EVIDENCE: REVIEW_STATE_BLOCKED_MISSING_EVIDENCE,
    REVIEW_DECISION_PROMOTE_LOCAL: REVIEW_STATE_PROMOTED_LOCAL,
}

_ROUTE_BY_DECISION = {
    REVIEW_DECISION_ARCHIVE: REVIEW_ROUTE_ARCHIVE_NOTE,
    REVIEW_DECISION_DISCARD: REVIEW_ROUTE_DISCARD,
    REVIEW_DECISION_REVIEW_LATER: REVIEW_ROUTE_REVIEW_LATER,
}


def record_review_decision(
    candidate: PromotionCandidate,
    *,
    decision: str,
    reviewer: str,
    reason_or_notes: str,
    route: str | None = None,
    promotion_output_ref: str | None = None,
    created_at: str | None = None,
) -> ReviewDecision:
    if decision not in REVIEW_DECISIONS:
        raise ValueError(f"unsupported review decision: {decision}")

    selected_route = route or _ROUTE_BY_DECISION.get(decision, candidate.recommended_route)
    new_status = _STATUS_BY_DECISION[decision]
    if decision == REVIEW_DECISION_BLOCK_MISSING_EVIDENCE and not validate_candidate_evidence(candidate):
        raise ValueError("block_missing_evidence decision requires missing evidence")

    return ReviewDecision(
        decision_id=build_decision_id(
            candidate_id=candidate.candidate_id,
            decision=decision,
            route=selected_route,
            reviewer=reviewer,
            evidence_links=candidate.evidence_links,
        ),
        candidate_id=candidate.candidate_id,
        decision=decision,
        route=selected_route,
        reviewer=reviewer,
        reason_or_notes=reason_or_notes,
        evidence_links=candidate.evidence_links,
        previous_status=candidate.decision_status,
        new_status=new_status,
        promotion_output_ref=promotion_output_ref,
        created_at=created_at,
    )


def create_local_promotion_output(
    candidate: PromotionCandidate,
    approval_decision: ReviewDecision,
    *,
    output_type: str,
    output_path_or_ref: str,
    generated_by: str = "local-review-workflow-v0",
    created_at: str | None = None,
) -> PromotionOutput:
    if approval_decision.candidate_id != candidate.candidate_id:
        raise ValueError("approval decision does not match candidate")
    if approval_decision.new_status != REVIEW_STATE_APPROVED:
        raise ValueError("local promotion output requires an approved decision")

    gate = promotion_gate_result(candidate, operator_decision_present=True)
    if not gate.allowed:
        raise ValueError(f"local promotion output blocked: {gate.blocked_reason}")

    return PromotionOutput(
        promotion_id=build_promotion_id(
            candidate_id=candidate.candidate_id,
            route=approval_decision.route,
            output_type=output_type,
            decision_id=approval_decision.decision_id,
        ),
        candidate_id=candidate.candidate_id,
        route=approval_decision.route,
        boundary=candidate.boundary,
        output_type=output_type,
        output_path_or_ref=output_path_or_ref,
        source_evidence_links=candidate.evidence_links,
        decision_id=approval_decision.decision_id,
        generated_by=generated_by,
        promotion_status=REVIEW_STATE_PROMOTED_LOCAL,
        created_at=created_at,
    )
