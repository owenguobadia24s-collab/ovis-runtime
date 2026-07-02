"""Deterministic lexical theme grouping for local refinement records."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Iterable, Mapping

from ovis_retrieval import tokenize

from .evidence import EvidenceLink, build_chunk_evidence_link, build_segment_evidence_link
from .segments import RefinementChunk, RefinementSegment


THEME_PASS_VERSION = "theme-dedup-v0"
DEFAULT_MIN_MEMBERS = 2

THEME_STOPWORDS = frozenset(
    {
        "about",
        "again",
        "also",
        "from",
        "have",
        "here",
        "into",
        "only",
        "that",
        "their",
        "there",
        "this",
        "with",
        "would",
    }
)


@dataclass(frozen=True)
class ThemeMember:
    item_id: str
    source_id: str
    segment_id: str
    chunk_id: str | None
    speaker: str
    evidence_link: EvidenceLink


@dataclass(frozen=True)
class ThemeCluster:
    cluster_id: str
    key: str
    member_count: int
    member_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    segment_ids: tuple[str, ...]
    members: tuple[ThemeMember, ...]
    created_by: str = THEME_PASS_VERSION


def build_theme_clusters(
    items: Iterable[RefinementSegment | RefinementChunk],
    *,
    evidence_links: Mapping[str, EvidenceLink] | None = None,
    min_members: int = DEFAULT_MIN_MEMBERS,
    max_terms_per_item: int = 12,
) -> tuple[ThemeCluster, ...]:
    if min_members < 2:
        raise ValueError("min_members must be at least 2")
    if max_terms_per_item < 1:
        raise ValueError("max_terms_per_item must be at least 1")

    link_map = evidence_links or {}
    grouped: dict[str, dict[str, ThemeMember]] = {}

    for item in items:
        item_id = _item_id(item)
        member = _theme_member(item, link_map.get(item_id))
        for key in _candidate_terms(item, max_terms_per_item=max_terms_per_item):
            grouped.setdefault(key, {})[item_id] = member

    clusters = [
        _theme_cluster(key, tuple(members[item_id] for item_id in sorted(members)))
        for key, members in grouped.items()
        if len(members) >= min_members
    ]
    return tuple(sorted(clusters, key=lambda cluster: (cluster.key, cluster.cluster_id)))


def _candidate_terms(item: RefinementSegment | RefinementChunk, *, max_terms_per_item: int) -> tuple[str, ...]:
    terms = item.normalized_terms if isinstance(item, RefinementChunk) else tokenize(item.text)
    candidates = sorted({term for term in terms if len(term) >= 4 and term not in THEME_STOPWORDS})
    return tuple(candidates[:max_terms_per_item])


def _theme_member(item: RefinementSegment | RefinementChunk, evidence_link: EvidenceLink | None) -> ThemeMember:
    link = evidence_link if evidence_link is not None else _build_evidence_link(item)
    return ThemeMember(
        item_id=_item_id(item),
        source_id=item.source_id,
        segment_id=item.segment_id,
        chunk_id=item.chunk_id if isinstance(item, RefinementChunk) else None,
        speaker=item.speaker,
        evidence_link=link,
    )


def _theme_cluster(key: str, members: tuple[ThemeMember, ...]) -> ThemeCluster:
    member_ids = tuple(member.item_id for member in members)
    return ThemeCluster(
        cluster_id=_cluster_id(key, member_ids),
        key=key,
        member_count=len(members),
        member_ids=member_ids,
        source_ids=tuple(sorted({member.source_id for member in members})),
        segment_ids=tuple(sorted({member.segment_id for member in members})),
        members=members,
    )


def _build_evidence_link(item: RefinementSegment | RefinementChunk) -> EvidenceLink:
    if isinstance(item, RefinementChunk):
        return build_chunk_evidence_link(item, created_by=THEME_PASS_VERSION)
    return build_segment_evidence_link(item, created_by=THEME_PASS_VERSION)


def _item_id(item: RefinementSegment | RefinementChunk) -> str:
    return item.chunk_id if isinstance(item, RefinementChunk) else item.segment_id


def _cluster_id(key: str, member_ids: tuple[str, ...]) -> str:
    raw = f"{key}:{':'.join(member_ids)}:{THEME_PASS_VERSION}".encode("utf-8")
    return f"THEME-{hashlib.sha256(raw).hexdigest()[:16]}"
