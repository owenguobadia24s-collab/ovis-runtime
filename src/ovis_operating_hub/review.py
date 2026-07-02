"""Read-only local review candidate listing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from ovis_review_promotion import (
    REVIEW_STATE_BLOCKED_MISSING_EVIDENCE,
    PromotionCandidate,
    promotion_candidate_from_dict,
    validate_candidate_evidence,
)

from .models import ReviewListItem


EVIDENCE_POSTURE_PRESENT = "present"
EVIDENCE_POSTURE_MISSING = "missing"
EVIDENCE_POSTURE_BLOCKED_MISSING_EVIDENCE = "blocked_missing_evidence"

EVIDENCE_POSTURES = (
    EVIDENCE_POSTURE_PRESENT,
    EVIDENCE_POSTURE_MISSING,
    EVIDENCE_POSTURE_BLOCKED_MISSING_EVIDENCE,
)


def load_review_candidates_from_queue_json(path: str | Path) -> tuple[PromotionCandidate, ...]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    candidate_payloads = payload if isinstance(payload, list) else payload.get("candidates", ())
    return tuple(promotion_candidate_from_dict(candidate) for candidate in candidate_payloads)


def list_review_candidates(
    candidates: Iterable[PromotionCandidate],
    *,
    boundary: str | None = None,
    status: str | None = None,
    route: str | None = None,
    evidence_posture: str | None = None,
    ambiguity_status: str | None = None,
) -> tuple[ReviewListItem, ...]:
    items = tuple(_to_review_list_item(candidate) for candidate in candidates)
    return tuple(
        sorted(
            (
                item
                for item in items
                if _matches(
                    item,
                    boundary=boundary,
                    status=status,
                    route=route,
                    evidence_posture=evidence_posture,
                    ambiguity_status=ambiguity_status,
                )
            ),
            key=lambda item: item.candidate_id,
        )
    )


def render_review_list_text(items: Iterable[ReviewListItem]) -> str:
    ordered = tuple(sorted(items, key=lambda item: item.candidate_id))
    if not ordered:
        return "No review candidates matched.\n"
    lines = [
        "Candidate ID | Boundary | Route | Status | Evidence | Title",
        "---|---|---|---|---|---",
    ]
    for item in ordered:
        lines.append(
            " | ".join(
                (
                    item.candidate_id,
                    item.boundary,
                    item.route,
                    item.status,
                    item.evidence_posture,
                    item.title,
                )
            )
        )
    return "\n".join(lines) + "\n"


def _to_review_list_item(candidate: PromotionCandidate) -> ReviewListItem:
    evidence_refs = tuple(sorted(link.evidence_id for link in candidate.evidence_links if link.evidence_id))
    source_refs = tuple(
        sorted(
            ref
            for link in candidate.evidence_links
            for ref in (link.source_ref, link.manifest_ref)
            if ref
        )
    )
    return ReviewListItem(
        candidate_id=candidate.candidate_id,
        title=candidate.candidate_title,
        boundary=candidate.boundary,
        route=candidate.recommended_route,
        status=candidate.decision_status,
        evidence_posture=_evidence_posture(candidate),
        evidence_refs=evidence_refs,
        source_refs=source_refs,
        ambiguity_status=candidate.ambiguity_status,
    )


def _evidence_posture(candidate: PromotionCandidate) -> str:
    if candidate.decision_status == REVIEW_STATE_BLOCKED_MISSING_EVIDENCE:
        return EVIDENCE_POSTURE_BLOCKED_MISSING_EVIDENCE
    if validate_candidate_evidence(candidate):
        return EVIDENCE_POSTURE_MISSING
    return EVIDENCE_POSTURE_PRESENT


def _matches(
    item: ReviewListItem,
    *,
    boundary: str | None,
    status: str | None,
    route: str | None,
    evidence_posture: str | None,
    ambiguity_status: str | None,
) -> bool:
    if boundary is not None and item.boundary != boundary:
        return False
    if status is not None and item.status != status:
        return False
    if route is not None and item.route != route:
        return False
    if evidence_posture is not None and item.evidence_posture != evidence_posture:
        return False
    if ambiguity_status is not None and item.ambiguity_status != ambiguity_status:
        return False
    return True
