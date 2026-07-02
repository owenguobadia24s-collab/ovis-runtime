"""Local-only promotion command helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from ovis_review_promotion import (
    REVIEW_ROUTES,
    REVIEW_STATE_APPROVED,
    PromotionCandidate,
    PromotionOutput,
    ReviewDecision,
    create_local_promotion_output,
    review_decision_from_dict,
)


DEFAULT_PROMOTION_OUTPUT_TYPE = "local_promotion_reference"
DEFAULT_PROMOTION_GENERATOR = "ovis-operating-hub-promotion-command-v0"


def load_review_decisions_json(path: str | Path) -> tuple[ReviewDecision, ...]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, list):
        decision_payloads = payload
    elif isinstance(payload, dict) and "decisions" in payload:
        decision_payloads = payload["decisions"]
    elif isinstance(payload, dict):
        decision_payloads = (payload,)
    else:
        raise ValueError("decision JSON must be an object, an array, or an object with a decisions array")
    return tuple(review_decision_from_dict(decision) for decision in decision_payloads)


def prepare_local_promotion(
    candidates: Iterable[PromotionCandidate],
    decisions: Iterable[ReviewDecision],
    *,
    candidate_id: str,
    output_path_or_ref: str,
    output_type: str = DEFAULT_PROMOTION_OUTPUT_TYPE,
    route: str | None = None,
    decision_id: str | None = None,
) -> PromotionOutput:
    candidate = _select_candidate(candidates, candidate_id)
    decision = _select_approval_decision(decisions, candidate_id=candidate_id, decision_id=decision_id)

    if route is not None and route != decision.route:
        raise ValueError("requested route does not match the approved decision route")
    if decision.route not in REVIEW_ROUTES:
        raise ValueError("approved decision route is not allowed")
    if decision.new_status != REVIEW_STATE_APPROVED:
        raise ValueError("local promotion requires an approved decision")

    return create_local_promotion_output(
        candidate,
        decision,
        output_type=output_type,
        output_path_or_ref=output_path_or_ref,
        generated_by=DEFAULT_PROMOTION_GENERATOR,
    )


def render_promotion_output_text(output: PromotionOutput) -> str:
    evidence_ids = ", ".join(link.evidence_id for link in output.source_evidence_links if link.evidence_id)
    return "\n".join(
        (
            f"promotion_id: {output.promotion_id}",
            f"candidate_id: {output.candidate_id}",
            f"route: {output.route}",
            f"boundary: {output.boundary}",
            f"output_type: {output.output_type}",
            f"output_ref: {output.output_path_or_ref}",
            f"decision_id: {output.decision_id}",
            f"status: {output.promotion_status}",
            f"evidence: {evidence_ids}",
            "",
        )
    )


def _select_candidate(candidates: Iterable[PromotionCandidate], candidate_id: str) -> PromotionCandidate:
    matches = tuple(candidate for candidate in candidates if candidate.candidate_id == candidate_id)
    if not matches:
        raise ValueError("candidate_id was not found in the review queue")
    if len(matches) > 1:
        raise ValueError("candidate_id matched multiple review candidates")
    return matches[0]


def _select_approval_decision(
    decisions: Iterable[ReviewDecision],
    *,
    candidate_id: str,
    decision_id: str | None,
) -> ReviewDecision:
    candidate_decisions = tuple(decision for decision in decisions if decision.candidate_id == candidate_id)
    if decision_id is not None:
        matches = tuple(decision for decision in candidate_decisions if decision.decision_id == decision_id)
        if not matches:
            raise ValueError("decision_id was not found for the requested candidate")
        return matches[0]

    approvals = tuple(
        decision
        for decision in candidate_decisions
        if decision.new_status == REVIEW_STATE_APPROVED
    )
    if not approvals:
        raise ValueError("no approved decision found for the requested candidate")
    if len(approvals) > 1:
        raise ValueError("multiple approved decisions found; pass --decision-id")
    return approvals[0]
