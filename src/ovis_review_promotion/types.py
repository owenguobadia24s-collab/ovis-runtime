"""Serializable review and promotion records for local operator review."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
import hashlib
from typing import Any, Mapping

from ovis_refinement import EvidenceLink


PROMOTION_CANDIDATE_VERSION = "promotion-candidate-v0"
REVIEW_QUEUE_VERSION = "review-queue-v0"
REVIEW_DECISION_VERSION = "review-decision-v0"
PROMOTION_OUTPUT_VERSION = "promotion-output-v0"
PROMOTION_GATE_POLICY_VERSION = "promotion-gate-v0"

REVIEW_STATE_PENDING = "pending_review"
REVIEW_STATE_APPROVED = "approved"
REVIEW_STATE_ARCHIVED = "archived"
REVIEW_STATE_DISCARDED = "discarded"
REVIEW_STATE_REVIEW_LATER = "review_later"
REVIEW_STATE_PROMOTED_LOCAL = "promoted_local"
REVIEW_STATE_BLOCKED_MISSING_EVIDENCE = "blocked_missing_evidence"
REVIEW_STATE_BLOCKED_ROUTE_POLICY = "blocked_route_policy"

REVIEW_STATES = (
    REVIEW_STATE_PENDING,
    REVIEW_STATE_APPROVED,
    REVIEW_STATE_ARCHIVED,
    REVIEW_STATE_DISCARDED,
    REVIEW_STATE_REVIEW_LATER,
    REVIEW_STATE_PROMOTED_LOCAL,
    REVIEW_STATE_BLOCKED_MISSING_EVIDENCE,
    REVIEW_STATE_BLOCKED_ROUTE_POLICY,
)

REVIEW_ROUTE_CJ_CANDIDATE = "cj_candidate"
REVIEW_ROUTE_DOCTRINE_CANDIDATE = "doctrine_candidate"
REVIEW_ROUTE_OVC_SPEC_CANDIDATE = "ovc_spec_candidate"
REVIEW_ROUTE_ROUTINE_ACTION_CANDIDATE = "routine_action_candidate"
REVIEW_ROUTE_ARCHIVE_NOTE = "archive_note"
REVIEW_ROUTE_DISCARD = "discard"
REVIEW_ROUTE_REVIEW_LATER = "review_later"

REVIEW_ROUTES = (
    REVIEW_ROUTE_CJ_CANDIDATE,
    REVIEW_ROUTE_DOCTRINE_CANDIDATE,
    REVIEW_ROUTE_OVC_SPEC_CANDIDATE,
    REVIEW_ROUTE_ROUTINE_ACTION_CANDIDATE,
    REVIEW_ROUTE_ARCHIVE_NOTE,
    REVIEW_ROUTE_DISCARD,
    REVIEW_ROUTE_REVIEW_LATER,
)


@dataclass(frozen=True)
class PromotionCandidate:
    candidate_id: str
    source_type: str
    source_id: str
    segment_id: str | None
    chunk_id: str | None
    boundary: str
    recommended_route: str
    candidate_title: str
    candidate_text: str
    classifier_reason: str | None
    ambiguity_status: str | None
    evidence_links: tuple[EvidenceLink, ...]
    decision_status: str = REVIEW_STATE_PENDING
    created_by: str = PROMOTION_CANDIDATE_VERSION
    created_at: str | None = None
    candidate_version: str = PROMOTION_CANDIDATE_VERSION


@dataclass(frozen=True)
class ReviewQueue:
    queue_id: str
    generated_from: str
    candidate_ids: tuple[str, ...]
    candidate_count: int
    boundary_counts: Mapping[str, int]
    pending_count: int
    source_manifest_refs: tuple[str, ...]
    queue_version: str = REVIEW_QUEUE_VERSION
    generated_at: str | None = None


@dataclass(frozen=True)
class ReviewDecision:
    decision_id: str
    candidate_id: str
    decision: str
    route: str
    reviewer: str
    reason_or_notes: str
    evidence_links: tuple[EvidenceLink, ...]
    previous_status: str
    new_status: str
    promotion_output_ref: str | None = None
    created_at: str | None = None
    decision_version: str = REVIEW_DECISION_VERSION


@dataclass(frozen=True)
class PromotionOutput:
    promotion_id: str
    candidate_id: str
    route: str
    boundary: str
    output_type: str
    output_path_or_ref: str
    source_evidence_links: tuple[EvidenceLink, ...]
    decision_id: str
    generated_by: str
    promotion_status: str
    created_at: str | None = None
    promotion_version: str = PROMOTION_OUTPUT_VERSION


@dataclass(frozen=True)
class PromotionGateResult:
    candidate_id: str
    allowed: bool
    blocked_reason: str | None
    required_fields_present: bool
    required_evidence_present: bool
    operator_decision_present: bool
    route_allowed: bool
    policy_version: str = PROMOTION_GATE_POLICY_VERSION


def build_candidate_id(
    *,
    source_id: str,
    segment_id: str | None,
    chunk_id: str | None,
    boundary: str,
    recommended_route: str,
    evidence_links: tuple[EvidenceLink, ...],
) -> str:
    evidence_ids = ",".join(sorted(link.evidence_id for link in evidence_links))
    return _stable_id(
        "CAND",
        source_id,
        segment_id or "",
        chunk_id or "",
        boundary,
        recommended_route,
        evidence_ids,
        PROMOTION_CANDIDATE_VERSION,
    )


def build_queue_id(*, generated_from: str, candidate_ids: tuple[str, ...]) -> str:
    return _stable_id("QUEUE", generated_from, ",".join(sorted(candidate_ids)), REVIEW_QUEUE_VERSION)


def build_decision_id(
    *,
    candidate_id: str,
    decision: str,
    route: str,
    reviewer: str,
    evidence_links: tuple[EvidenceLink, ...],
) -> str:
    evidence_ids = ",".join(sorted(link.evidence_id for link in evidence_links))
    return _stable_id("DECISION", candidate_id, decision, route, reviewer, evidence_ids, REVIEW_DECISION_VERSION)


def build_promotion_id(*, candidate_id: str, route: str, output_type: str, decision_id: str) -> str:
    return _stable_id("PROMO", candidate_id, route, output_type, decision_id, PROMOTION_OUTPUT_VERSION)


def validate_candidate_evidence(candidate: PromotionCandidate) -> tuple[str, ...]:
    missing: list[str] = []
    if not candidate.source_id:
        missing.append("source_id")
    if not candidate.segment_id and not candidate.chunk_id:
        missing.append("segment_or_chunk_id")
    if not candidate.evidence_links:
        missing.append("evidence_links")

    for index, link in enumerate(candidate.evidence_links):
        prefix = f"evidence_links[{index}]"
        if not link.evidence_id:
            missing.append(f"{prefix}.evidence_id")
        if not link.source_id:
            missing.append(f"{prefix}.source_id")
        if candidate.source_id and link.source_id != candidate.source_id:
            missing.append(f"{prefix}.source_id_mismatch")
        if not link.segment_id:
            missing.append(f"{prefix}.segment_id")
        if candidate.segment_id and link.segment_id != candidate.segment_id:
            missing.append(f"{prefix}.segment_id_mismatch")
        if candidate.chunk_id and link.chunk_id != candidate.chunk_id:
            missing.append(f"{prefix}.chunk_id_mismatch")
        if not link.source_ref:
            missing.append(f"{prefix}.source_ref")
        if not link.path:
            missing.append(f"{prefix}.path")
        if not link.quote_span_or_chunk_id:
            missing.append(f"{prefix}.quote_span_or_chunk_id")

    return tuple(missing)


def promotion_gate_result(
    candidate: PromotionCandidate,
    *,
    operator_decision_present: bool = False,
) -> PromotionGateResult:
    required_fields_present = all(
        (
            candidate.candidate_id,
            candidate.source_type,
            candidate.source_id,
            candidate.boundary,
            candidate.recommended_route,
            candidate.candidate_title,
            candidate.candidate_text,
            candidate.decision_status,
        )
    )
    required_evidence_present = not validate_candidate_evidence(candidate)
    route_allowed = candidate.recommended_route in REVIEW_ROUTES

    blocked_reason = None
    if not required_fields_present:
        blocked_reason = "missing_required_fields"
    elif not required_evidence_present:
        blocked_reason = REVIEW_STATE_BLOCKED_MISSING_EVIDENCE
    elif not route_allowed:
        blocked_reason = REVIEW_STATE_BLOCKED_ROUTE_POLICY
    elif not operator_decision_present:
        blocked_reason = "operator_decision_missing"

    return PromotionGateResult(
        candidate_id=candidate.candidate_id,
        allowed=blocked_reason is None,
        blocked_reason=blocked_reason,
        required_fields_present=required_fields_present,
        required_evidence_present=required_evidence_present,
        operator_decision_present=operator_decision_present,
        route_allowed=route_allowed,
    )


def record_to_dict(record: object) -> dict[str, Any]:
    return _to_json_value(record)


def promotion_candidate_from_dict(data: Mapping[str, Any]) -> PromotionCandidate:
    return PromotionCandidate(
        **{
            **dict(data),
            "evidence_links": _evidence_links_from_dicts(data.get("evidence_links", ())),
        }
    )


def review_queue_from_dict(data: Mapping[str, Any]) -> ReviewQueue:
    return ReviewQueue(
        **{
            **dict(data),
            "candidate_ids": tuple(data.get("candidate_ids", ())),
            "source_manifest_refs": tuple(data.get("source_manifest_refs", ())),
        }
    )


def review_decision_from_dict(data: Mapping[str, Any]) -> ReviewDecision:
    return ReviewDecision(
        **{
            **dict(data),
            "evidence_links": _evidence_links_from_dicts(data.get("evidence_links", ())),
        }
    )


def promotion_output_from_dict(data: Mapping[str, Any]) -> PromotionOutput:
    return PromotionOutput(
        **{
            **dict(data),
            "source_evidence_links": _evidence_links_from_dicts(data.get("source_evidence_links", ())),
        }
    )


def promotion_gate_result_from_dict(data: Mapping[str, Any]) -> PromotionGateResult:
    return PromotionGateResult(**dict(data))


def _to_json_value(value: Any) -> Any:
    if is_dataclass(value):
        return {key: _to_json_value(item) for key, item in asdict(value).items()}
    if isinstance(value, tuple | list):
        return [_to_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _to_json_value(item) for key, item in value.items()}
    return value


def _evidence_links_from_dicts(values: object) -> tuple[EvidenceLink, ...]:
    return tuple(EvidenceLink(**dict(value)) if not isinstance(value, EvidenceLink) else value for value in values or ())


def _stable_id(prefix: str, *parts: str) -> str:
    raw = ":".join(parts).encode("utf-8")
    return f"{prefix}-{hashlib.sha256(raw).hexdigest()[:16]}"
