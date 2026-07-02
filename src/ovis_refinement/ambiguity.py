"""Local ambiguity routing for refinement classifier outputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .boundary_classifier import BOUNDARY_REVIEW_AMBIGUOUS, BoundaryLabel
from .evidence import EvidenceLink


AMBIGUITY_ROUTER_VERSION = "ambiguity-route-v0"
DEFAULT_MINIMUM_CONFIDENCE = 0.6
DEFAULT_MIXED_MARGIN = 1
REVIEW_ROUTE = BOUNDARY_REVIEW_AMBIGUOUS


@dataclass(frozen=True)
class AmbiguityRoute:
    item_id: str
    source_id: str | None
    segment_id_or_chunk_id: str
    candidate_boundaries: tuple[str, ...]
    scores: Mapping[str, int]
    reason: str
    route: str
    review_required: bool
    classifier_version: str
    router_version: str
    evidence_id: str | None = None


def route_boundary_label(
    classification: BoundaryLabel,
    *,
    evidence_link: EvidenceLink | None = None,
    minimum_confidence: float = DEFAULT_MINIMUM_CONFIDENCE,
    mixed_margin: int = DEFAULT_MIXED_MARGIN,
) -> AmbiguityRoute:
    candidate_boundaries = _candidate_boundaries(classification.scores)
    strongest = _strongest_score(classification.scores)
    second = _second_score(classification.scores)

    route = classification.boundary
    review_required = classification.review_required
    reasons: list[str] = []

    if classification.is_ambiguous or classification.boundary == BOUNDARY_REVIEW_AMBIGUOUS:
        route = REVIEW_ROUTE
        review_required = True
        reasons.append(classification.reason)

    if classification.confidence < minimum_confidence:
        route = REVIEW_ROUTE
        review_required = True
        reasons.append(f"confidence {classification.confidence:.3f} below minimum {minimum_confidence:.3f}")

    if strongest > 0 and second > 0 and strongest - second <= mixed_margin:
        route = REVIEW_ROUTE
        review_required = True
        reasons.append("candidate boundary scores are tied or within mixed-boundary margin")

    if evidence_link is None:
        route = REVIEW_ROUTE
        review_required = True
        reasons.append("missing evidence link")

    if not reasons:
        reasons.append(classification.reason)

    return AmbiguityRoute(
        item_id=classification.item_id,
        source_id=evidence_link.source_id if evidence_link is not None else None,
        segment_id_or_chunk_id=_segment_or_item_id(classification, evidence_link),
        candidate_boundaries=candidate_boundaries,
        scores=dict(classification.scores),
        reason="; ".join(reasons),
        route=route,
        review_required=review_required,
        classifier_version=classification.classifier_version,
        router_version=AMBIGUITY_ROUTER_VERSION,
        evidence_id=evidence_link.evidence_id if evidence_link is not None else None,
    )


def route_boundary_labels(
    classifications: tuple[BoundaryLabel, ...],
    *,
    evidence_links: Mapping[str, EvidenceLink] | None = None,
    minimum_confidence: float = DEFAULT_MINIMUM_CONFIDENCE,
    mixed_margin: int = DEFAULT_MIXED_MARGIN,
) -> tuple[AmbiguityRoute, ...]:
    links = evidence_links or {}
    return tuple(
        route_boundary_label(
            classification,
            evidence_link=links.get(classification.item_id),
            minimum_confidence=minimum_confidence,
            mixed_margin=mixed_margin,
        )
        for classification in classifications
    )


def _candidate_boundaries(scores: Mapping[str, int]) -> tuple[str, ...]:
    return tuple(boundary for boundary, score in sorted(scores.items(), key=lambda item: (-item[1], item[0])) if score > 0)


def _strongest_score(scores: Mapping[str, int]) -> int:
    return max(scores.values(), default=0)


def _second_score(scores: Mapping[str, int]) -> int:
    ranked = sorted(scores.values(), reverse=True)
    return ranked[1] if len(ranked) > 1 else 0


def _segment_or_item_id(classification: BoundaryLabel, evidence_link: EvidenceLink | None) -> str:
    if evidence_link is None:
        return classification.item_id
    return evidence_link.chunk_id or evidence_link.segment_id
