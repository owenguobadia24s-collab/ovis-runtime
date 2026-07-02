"""Deterministic local project status aggregation."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Iterable, Mapping

from ovis_refinement import BOUNDARY_LABELS
from ovis_review_promotion import (
    REVIEW_STATE_APPROVED,
    REVIEW_STATE_ARCHIVED,
    REVIEW_STATE_BLOCKED_MISSING_EVIDENCE,
    REVIEW_STATE_BLOCKED_ROUTE_POLICY,
    REVIEW_STATE_DISCARDED,
    REVIEW_STATE_PENDING,
    REVIEW_STATE_PROMOTED_LOCAL,
    REVIEW_STATE_REVIEW_LATER,
    PromotionCandidate,
    PromotionOutput,
    ReviewDecision,
    ReviewQueue,
)

from .models import HUB_STATUS_VERSION, HubStatus, ProjectStatus, ReviewSummary


DEFAULT_BOUNDARIES = BOUNDARY_LABELS
BLOCKED_STATES = (REVIEW_STATE_BLOCKED_MISSING_EVIDENCE, REVIEW_STATE_BLOCKED_ROUTE_POLICY)


def build_project_statuses(
    candidates: Iterable[PromotionCandidate],
    *,
    decisions: Iterable[ReviewDecision] = (),
    promotion_outputs: Iterable[PromotionOutput] = (),
    open_cj_counts: Mapping[str, int] | None = None,
    boundaries: tuple[str, ...] = DEFAULT_BOUNDARIES,
) -> tuple[ProjectStatus, ...]:
    candidate_records = tuple(sorted(candidates, key=lambda candidate: candidate.candidate_id))
    decision_records = tuple(sorted(decisions, key=lambda decision: decision.decision_id))
    output_records = tuple(sorted(promotion_outputs, key=lambda output: output.promotion_id))
    decisions_by_candidate = _decisions_by_candidate(decision_records)
    outputs_by_candidate = _outputs_by_candidate(output_records)
    open_counts = dict(open_cj_counts or {})

    statuses: list[ProjectStatus] = []
    for boundary in boundaries:
        scoped_candidates = tuple(candidate for candidate in candidate_records if candidate.boundary == boundary)
        status_counts = Counter(_effective_status(candidate, decisions_by_candidate) for candidate in scoped_candidates)
        promoted_count = sum(len(outputs_by_candidate.get(candidate.candidate_id, ())) for candidate in scoped_candidates)
        blocked_count = sum(status_counts[state] for state in BLOCKED_STATES)
        source_refs = _source_refs(scoped_candidates, decision_records, output_records)
        statuses.append(
            ProjectStatus(
                boundary=boundary,
                classified_count=len(scoped_candidates),
                pending_review_count=status_counts[REVIEW_STATE_PENDING],
                approved_count=status_counts[REVIEW_STATE_APPROVED],
                archived_count=status_counts[REVIEW_STATE_ARCHIVED],
                discarded_count=status_counts[REVIEW_STATE_DISCARDED],
                review_later_count=status_counts[REVIEW_STATE_REVIEW_LATER],
                blocked_count=blocked_count,
                promoted_local_count=promoted_count,
                open_cj_count=open_counts.get(boundary, 0),
                next_action_hint=_next_action_hint(
                    pending_count=status_counts[REVIEW_STATE_PENDING],
                    approved_count=status_counts[REVIEW_STATE_APPROVED],
                    blocked_count=blocked_count,
                    promoted_count=promoted_count,
                    open_cj_count=open_counts.get(boundary, 0),
                ),
                source_refs=source_refs,
            )
        )
    return tuple(statuses)


def build_review_summary(
    candidates: Iterable[PromotionCandidate],
    *,
    decisions: Iterable[ReviewDecision] = (),
    promotion_outputs: Iterable[PromotionOutput] = (),
    review_queues: Iterable[ReviewQueue] = (),
    boundaries: tuple[str, ...] = DEFAULT_BOUNDARIES,
) -> ReviewSummary:
    candidate_records = tuple(sorted(candidates, key=lambda candidate: candidate.candidate_id))
    decision_records = tuple(sorted(decisions, key=lambda decision: decision.decision_id))
    output_records = tuple(sorted(promotion_outputs, key=lambda output: output.promotion_id))
    decisions_by_candidate = _decisions_by_candidate(decision_records)
    status_counts = Counter(_effective_status(candidate, decisions_by_candidate) for candidate in candidate_records)
    boundary_counts = {boundary: 0 for boundary in boundaries}
    boundary_counts.update(Counter(candidate.boundary for candidate in candidate_records))

    return ReviewSummary(
        total_candidates=len(candidate_records),
        pending_count=status_counts[REVIEW_STATE_PENDING],
        approved_count=status_counts[REVIEW_STATE_APPROVED],
        archived_count=status_counts[REVIEW_STATE_ARCHIVED],
        discarded_count=status_counts[REVIEW_STATE_DISCARDED],
        review_later_count=status_counts[REVIEW_STATE_REVIEW_LATER],
        blocked_count=sum(status_counts[state] for state in BLOCKED_STATES),
        promoted_local_count=len(output_records),
        boundary_counts=dict(sorted(boundary_counts.items())),
        source_queue_refs=tuple(sorted(queue.queue_id for queue in review_queues)),
    )


def build_hub_status(
    candidates: Iterable[PromotionCandidate],
    *,
    decisions: Iterable[ReviewDecision] = (),
    promotion_outputs: Iterable[PromotionOutput] = (),
    review_queues: Iterable[ReviewQueue] = (),
    open_cj_counts: Mapping[str, int] | None = None,
    generated_from: Iterable[str] = (),
    active_bundle: str | None = None,
    active_cj: str | None = None,
    validation_posture: str = "unknown",
    external_side_effects: str = "disabled",
    created_at: str | None = None,
    boundaries: tuple[str, ...] = DEFAULT_BOUNDARIES,
) -> HubStatus:
    candidate_records = tuple(candidates)
    decision_records = tuple(decisions)
    output_records = tuple(promotion_outputs)
    queue_records = tuple(review_queues)
    project_statuses = build_project_statuses(
        candidate_records,
        decisions=decision_records,
        promotion_outputs=output_records,
        open_cj_counts=open_cj_counts,
        boundaries=boundaries,
    )
    review_summary = build_review_summary(
        candidate_records,
        decisions=decision_records,
        promotion_outputs=output_records,
        review_queues=queue_records,
        boundaries=boundaries,
    )
    source_refs = tuple(
        sorted(
            {
                *generated_from,
                *(queue.queue_id for queue in queue_records),
                *(ref for status in project_statuses for ref in status.source_refs),
            }
        )
    )
    return HubStatus(
        hub_version=HUB_STATUS_VERSION,
        generated_from=tuple(sorted(generated_from)),
        project_statuses=project_statuses,
        review_summary=review_summary,
        active_bundle=active_bundle,
        active_cj=active_cj,
        validation_posture=validation_posture,
        external_side_effects=external_side_effects,
        next_action=_hub_next_action(project_statuses),
        source_refs=source_refs,
        created_at=created_at,
    )


def _effective_status(candidate: PromotionCandidate, decisions_by_candidate: Mapping[str, tuple[ReviewDecision, ...]]) -> str:
    decisions = decisions_by_candidate.get(candidate.candidate_id, ())
    if decisions:
        return decisions[-1].new_status
    return candidate.decision_status


def _decisions_by_candidate(decisions: tuple[ReviewDecision, ...]) -> dict[str, tuple[ReviewDecision, ...]]:
    grouped: dict[str, list[ReviewDecision]] = defaultdict(list)
    for decision in decisions:
        grouped[decision.candidate_id].append(decision)
    return {candidate_id: tuple(sorted(items, key=lambda item: item.decision_id)) for candidate_id, items in grouped.items()}


def _outputs_by_candidate(outputs: tuple[PromotionOutput, ...]) -> dict[str, tuple[PromotionOutput, ...]]:
    grouped: dict[str, list[PromotionOutput]] = defaultdict(list)
    for output in outputs:
        grouped[output.candidate_id].append(output)
    return {candidate_id: tuple(sorted(items, key=lambda item: item.promotion_id)) for candidate_id, items in grouped.items()}


def _source_refs(
    candidates: tuple[PromotionCandidate, ...],
    decisions: tuple[ReviewDecision, ...],
    outputs: tuple[PromotionOutput, ...],
) -> tuple[str, ...]:
    refs = {
        ref
        for candidate in candidates
        for link in candidate.evidence_links
        for ref in (link.source_ref, link.manifest_ref)
        if ref
    }
    candidate_ids = {candidate.candidate_id for candidate in candidates}
    refs.update(decision.decision_id for decision in decisions if decision.candidate_id in candidate_ids)
    refs.update(output.promotion_id for output in outputs if output.candidate_id in candidate_ids)
    return tuple(sorted(refs))


def _next_action_hint(
    *,
    pending_count: int,
    approved_count: int,
    blocked_count: int,
    promoted_count: int,
    open_cj_count: int,
) -> str:
    if blocked_count:
        return "Repair missing or blocked evidence before promotion."
    if pending_count:
        return "Review pending local candidates."
    if approved_count > promoted_count:
        return "Review approved candidates for local promotion output."
    if open_cj_count:
        return "Continue open CJ work for this boundary."
    return "No local next action found."


def _hub_next_action(project_statuses: tuple[ProjectStatus, ...]) -> str:
    for status in project_statuses:
        if status.blocked_count:
            return f"{status.boundary}: repair blocked evidence."
    for status in project_statuses:
        if status.pending_review_count:
            return f"{status.boundary}: review pending candidates."
    for status in project_statuses:
        if status.approved_count > status.promoted_local_count:
            return f"{status.boundary}: prepare local promotion output."
    for status in project_statuses:
        if status.open_cj_count:
            return f"{status.boundary}: continue open CJ work."
    return "No local next action found."
