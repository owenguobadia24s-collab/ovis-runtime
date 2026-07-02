"""Serializable operating hub status records."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Mapping


PROJECT_STATUS_VERSION = "project-status-v0"
REVIEW_SUMMARY_VERSION = "review-summary-v0"
HUB_STATUS_VERSION = "hub-status-v0"
REVIEW_LIST_ITEM_VERSION = "review-list-item-v0"
HUB_NEXT_ACTION_VERSION = "hub-next-action-v0"


@dataclass(frozen=True)
class ProjectStatus:
    boundary: str
    classified_count: int
    pending_review_count: int
    approved_count: int
    archived_count: int
    discarded_count: int
    review_later_count: int
    blocked_count: int
    promoted_local_count: int
    open_cj_count: int
    next_action_hint: str
    source_refs: tuple[str, ...]
    status_version: str = PROJECT_STATUS_VERSION


@dataclass(frozen=True)
class ReviewSummary:
    total_candidates: int
    pending_count: int
    approved_count: int
    archived_count: int
    discarded_count: int
    review_later_count: int
    blocked_count: int
    promoted_local_count: int
    boundary_counts: Mapping[str, int]
    source_queue_refs: tuple[str, ...]
    summary_version: str = REVIEW_SUMMARY_VERSION


@dataclass(frozen=True)
class HubStatus:
    hub_version: str
    generated_from: tuple[str, ...]
    project_statuses: tuple[ProjectStatus, ...]
    review_summary: ReviewSummary
    active_bundle: str | None
    active_cj: str | None
    validation_posture: str
    external_side_effects: str
    next_action: str
    source_refs: tuple[str, ...]
    created_at: str | None = None


@dataclass(frozen=True)
class HubNextAction:
    action: str
    reason: str
    source_refs: tuple[str, ...]
    action_version: str = HUB_NEXT_ACTION_VERSION


@dataclass(frozen=True)
class ReviewListItem:
    candidate_id: str
    title: str
    boundary: str
    route: str
    status: str
    evidence_posture: str
    evidence_refs: tuple[str, ...]
    source_refs: tuple[str, ...]
    ambiguity_status: str | None
    item_version: str = REVIEW_LIST_ITEM_VERSION


def record_to_dict(record: object) -> dict[str, Any]:
    return _to_json_value(record)


def _to_json_value(value: Any) -> Any:
    if is_dataclass(value):
        return {key: _to_json_value(item) for key, item in asdict(value).items()}
    if isinstance(value, tuple | list):
        return [_to_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _to_json_value(item) for key, item in value.items()}
    return value
