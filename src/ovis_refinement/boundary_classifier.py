"""Deterministic local boundary classifier for refinement records."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Mapping

from ovis_retrieval import tokenize

from .segments import RefinementChunk, RefinementSegment


CLASSIFIER_VERSION = "boundary-rules-v0"

BOUNDARY_OVIS = "OVIS"
BOUNDARY_OVC = "OVC"
BOUNDARY_CODEX_VITAE = "Codex Vitae"
BOUNDARY_LIFE_OPS = "Life Ops"
BOUNDARY_GENERAL_INQUIRY = "General Inquiry"
BOUNDARY_REVIEW_AMBIGUOUS = "Review / Ambiguous"

BOUNDARY_LABELS = (
    BOUNDARY_OVIS,
    BOUNDARY_OVC,
    BOUNDARY_CODEX_VITAE,
    BOUNDARY_LIFE_OPS,
    BOUNDARY_GENERAL_INQUIRY,
    BOUNDARY_REVIEW_AMBIGUOUS,
)
SCORABLE_BOUNDARIES = BOUNDARY_LABELS[:-1]
INSUFFICIENT_EVIDENCE_PHRASES = (
    "belongs in the system somewhere",
    "probably as a task or doctrine",
    "probably",
)


@dataclass(frozen=True)
class BoundaryRule:
    rule_id: str
    boundary: str
    phrase: str
    weight: int


@dataclass(frozen=True)
class BoundaryLabel:
    item_id: str
    boundary: str
    confidence: float
    reason: str
    matched_rules: tuple[str, ...]
    classifier_version: str
    is_ambiguous: bool
    review_required: bool
    scores: Mapping[str, int]


RULES: tuple[BoundaryRule, ...] = (
    BoundaryRule("OVIS-BUNDLE-LEDGER", BOUNDARY_OVIS, "bundle ledger", 4),
    BoundaryRule("OVIS-CJ-REGISTER", BOUNDARY_OVIS, "cj register", 4),
    BoundaryRule("OVIS-REGISTRY", BOUNDARY_OVIS, "registry", 3),
    BoundaryRule("OVIS-RECONCILE", BOUNDARY_OVIS, "reconcile", 3),
    BoundaryRule("OVIS-RUNTIME", BOUNDARY_OVIS, "runtime", 2),
    BoundaryRule("OVIS-RETRIEVAL", BOUNDARY_OVIS, "retrieval", 2),
    BoundaryRule("OVIS-EVIDENCE", BOUNDARY_OVIS, "evidence", 2),
    BoundaryRule("OVIS-OPERATING-HUB", BOUNDARY_OVIS, "operating hub", 4),
    BoundaryRule("OVIS-BRIDGE", BOUNDARY_OVIS, "bridge preview", 4),
    BoundaryRule("OVIS-VALIDATION", BOUNDARY_OVIS, "validation", 2),
    BoundaryRule("OVC-MARKET", BOUNDARY_OVC, "market", 2),
    BoundaryRule("OVC-MARKET-STRUCTURE", BOUNDARY_OVC, "market structure", 4),
    BoundaryRule("OVC-TRADING", BOUNDARY_OVC, "trading", 3),
    BoundaryRule("OVC-TRADE", BOUNDARY_OVC, "trade", 2),
    BoundaryRule("OVC-CHART", BOUNDARY_OVC, "chart", 3),
    BoundaryRule("OVC-AUCTION", BOUNDARY_OVC, "auction", 3),
    BoundaryRule("OVC-PROP-FIRM", BOUNDARY_OVC, "prop firm", 4),
    BoundaryRule("OVC-RISK-LIMITS", BOUNDARY_OVC, "risk limits", 4),
    BoundaryRule("OVC-TPO", BOUNDARY_OVC, "tpo", 4),
    BoundaryRule("OVC-POST-TRADE", BOUNDARY_OVC, "post-trade", 4),
    BoundaryRule("CODEX-DOCTRINE", BOUNDARY_CODEX_VITAE, "doctrine", 3),
    BoundaryRule("CODEX-VOW", BOUNDARY_CODEX_VITAE, "vow", 4),
    BoundaryRule("CODEX-RITUAL", BOUNDARY_CODEX_VITAE, "ritual", 4),
    BoundaryRule("CODEX-ARCHETYPE", BOUNDARY_CODEX_VITAE, "archetype", 4),
    BoundaryRule("CODEX-THRESHOLD", BOUNDARY_CODEX_VITAE, "threshold", 3),
    BoundaryRule("CODEX-INVOCATION", BOUNDARY_CODEX_VITAE, "invocation", 4),
    BoundaryRule("CODEX-PHILOSOPHICAL", BOUNDARY_CODEX_VITAE, "philosophical", 3),
    BoundaryRule("CODEX-LYRICAL", BOUNDARY_CODEX_VITAE, "lyrical", 4),
    BoundaryRule("LIFE-SLEEP", BOUNDARY_LIFE_OPS, "sleep", 4),
    BoundaryRule("LIFE-ROUTINE", BOUNDARY_LIFE_OPS, "routine", 3),
    BoundaryRule("LIFE-SCREENS", BOUNDARY_LIFE_OPS, "screens", 3),
    BoundaryRule("LIFE-STUDY", BOUNDARY_LIFE_OPS, "study", 3),
    BoundaryRule("LIFE-HEALTH", BOUNDARY_LIFE_OPS, "health", 3),
    BoundaryRule("LIFE-CAREER", BOUNDARY_LIFE_OPS, "career", 3),
    BoundaryRule("LIFE-WATER", BOUNDARY_LIFE_OPS, "water intake", 4),
    BoundaryRule("LIFE-WALKING", BOUNDARY_LIFE_OPS, "walking minutes", 4),
    BoundaryRule("LIFE-PHONE", BOUNDARY_LIFE_OPS, "phone check", 4),
    BoundaryRule("LIFE-DEVICE", BOUNDARY_LIFE_OPS, "device reduction", 4),
    BoundaryRule("GEN-DIFFERENCE", BOUNDARY_GENERAL_INQUIRY, "what is the difference", 4),
    BoundaryRule("GEN-FIND", BOUNDARY_GENERAL_INQUIRY, "find common", 3),
    BoundaryRule("GEN-LIST", BOUNDARY_GENERAL_INQUIRY, "list the main", 3),
    BoundaryRule("GEN-PUBLIC-SERVICES", BOUNDARY_GENERAL_INQUIRY, "public services", 4),
    BoundaryRule("GEN-EXPLAIN", BOUNDARY_GENERAL_INQUIRY, "explain the difference", 4),
    BoundaryRule("GEN-WEATHER", BOUNDARY_GENERAL_INQUIRY, "weather", 2),
    BoundaryRule("GEN-CLIMATE", BOUNDARY_GENERAL_INQUIRY, "climate", 2),
)


def classify_refinement_item(item: RefinementSegment | RefinementChunk) -> BoundaryLabel:
    return classify_text(item.text, item_id=_item_id(item))


def classify_text(text: str, *, item_id: str = "<memory>") -> BoundaryLabel:
    scores, matched_rule_ids = _score_text(text)
    ranked = sorted(scores.items(), key=lambda entry: (-entry[1], entry[0]))
    top_boundary, top_score = ranked[0]
    runner_up_score = ranked[1][1]
    normalized = _normalize(text)

    if top_score <= 0:
        return _ambiguous_label(
            item_id,
            scores,
            (),
            "No boundary rule reached the minimum evidence threshold.",
            confidence=0.0,
        )

    if any(phrase in normalized for phrase in INSUFFICIENT_EVIDENCE_PHRASES):
        return _ambiguous_label(
            item_id,
            scores,
            _matched_ids(matched_rule_ids),
            "Text contains uncertainty or insufficient routing evidence.",
            confidence=_confidence(top_score, scores),
        )

    if runner_up_score > 0 and top_score == runner_up_score:
        return _ambiguous_label(
            item_id,
            scores,
            _matched_ids(matched_rule_ids),
            "Two or more boundaries have tied rule strength.",
            confidence=_confidence(top_score, scores),
        )

    if runner_up_score >= 3 and top_score - runner_up_score <= 3:
        return _ambiguous_label(
            item_id,
            scores,
            _matched_ids(matched_rule_ids),
            "Multiple boundaries have strong similar claim strength.",
            confidence=_confidence(top_score, scores),
        )

    if runner_up_score > 0 and top_score - runner_up_score <= 1:
        return _ambiguous_label(
            item_id,
            scores,
            _matched_ids(matched_rule_ids),
            "Boundary scores are too close for safe automatic routing.",
            confidence=_confidence(top_score, scores),
        )

    top_rules = tuple(sorted(matched_rule_ids[top_boundary]))
    return BoundaryLabel(
        item_id=item_id,
        boundary=top_boundary,
        confidence=_confidence(top_score, scores),
        reason=f"{top_boundary} selected from strongest matched B1-derived rules.",
        matched_rules=top_rules,
        classifier_version=CLASSIFIER_VERSION,
        is_ambiguous=False,
        review_required=False,
        scores=dict(scores),
    )


def _score_text(text: str) -> tuple[dict[str, int], dict[str, list[str]]]:
    normalized = _normalize(text)
    token_set = set(tokenize(text))
    scores = {boundary: 0 for boundary in SCORABLE_BOUNDARIES}
    matched_rule_ids: dict[str, list[str]] = {boundary: [] for boundary in SCORABLE_BOUNDARIES}

    for rule in RULES:
        if _rule_matches(rule.phrase, normalized, token_set):
            scores[rule.boundary] += rule.weight
            matched_rule_ids[rule.boundary].append(rule.rule_id)

    return scores, matched_rule_ids


def _rule_matches(phrase: str, normalized_text: str, token_set: set[str]) -> bool:
    normalized_phrase = _normalize(phrase)
    if " " in normalized_phrase:
        return normalized_phrase in normalized_text
    return normalized_phrase in token_set


def _normalize(text: str) -> str:
    lowered = text.lower().replace("-", " ")
    return re.sub(r"\s+", " ", lowered).strip()


def _confidence(top_score: int, scores: Mapping[str, int]) -> float:
    total = sum(scores.values())
    if total <= 0:
        return 0.0
    return round(top_score / total, 3)


def _matched_ids(matched_rule_ids: Mapping[str, list[str]]) -> tuple[str, ...]:
    all_ids: list[str] = []
    for boundary in SCORABLE_BOUNDARIES:
        all_ids.extend(matched_rule_ids[boundary])
    return tuple(sorted(all_ids))


def _ambiguous_label(
    item_id: str,
    scores: Mapping[str, int],
    matched_rules: tuple[str, ...],
    reason: str,
    *,
    confidence: float,
) -> BoundaryLabel:
    return BoundaryLabel(
        item_id=item_id,
        boundary=BOUNDARY_REVIEW_AMBIGUOUS,
        confidence=confidence,
        reason=reason,
        matched_rules=matched_rules,
        classifier_version=CLASSIFIER_VERSION,
        is_ambiguous=True,
        review_required=True,
        scores=dict(scores),
    )


def _item_id(item: RefinementSegment | RefinementChunk) -> str:
    if isinstance(item, RefinementChunk):
        return item.chunk_id
    return item.segment_id
