"""Source-preserving evidence links for refinement outputs."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .boundary_classifier import BoundaryLabel
from .search_index import SearchResult
from .segments import RefinementChunk, RefinementSegment


EVIDENCE_LINK_VERSION = "evidence-link-v0"


@dataclass(frozen=True)
class EvidenceLink:
    evidence_id: str
    source_ref: str
    source_id: str
    segment_id: str
    chunk_id: str | None
    path: str
    quote_span_or_chunk_id: str
    snippet: str | None
    created_by: str
    manifest_ref: str | None = None


@dataclass(frozen=True)
class ClassifiedEvidenceResult:
    classification: BoundaryLabel
    evidence_link: EvidenceLink


@dataclass(frozen=True)
class SearchEvidenceResult:
    search_result: SearchResult
    evidence_link: EvidenceLink


def build_segment_evidence_link(
    segment: RefinementSegment,
    *,
    created_by: str = EVIDENCE_LINK_VERSION,
) -> EvidenceLink:
    quote_span = f"chars:{segment.start_index}-{segment.end_index}"
    return EvidenceLink(
        evidence_id=_evidence_id(segment.source_id, segment.segment_id, None, quote_span, created_by),
        source_ref=f"{segment.source_path}#{segment.segment_id}",
        source_id=segment.source_id,
        segment_id=segment.segment_id,
        chunk_id=None,
        path=segment.source_path,
        quote_span_or_chunk_id=quote_span,
        snippet=segment.text,
        created_by=created_by,
        manifest_ref=segment.manifest_ref,
    )


def build_chunk_evidence_link(
    chunk: RefinementChunk,
    *,
    created_by: str = EVIDENCE_LINK_VERSION,
) -> EvidenceLink:
    quote_span = f"{chunk.chunk_id}:words:{chunk.start_word}-{chunk.end_word}"
    return EvidenceLink(
        evidence_id=_evidence_id(chunk.source_id, chunk.segment_id, chunk.chunk_id, quote_span, created_by),
        source_ref=f"{chunk.source_path}#{chunk.chunk_id}",
        source_id=chunk.source_id,
        segment_id=chunk.segment_id,
        chunk_id=chunk.chunk_id,
        path=chunk.source_path,
        quote_span_or_chunk_id=quote_span,
        snippet=chunk.text,
        created_by=created_by,
        manifest_ref=chunk.manifest_ref,
    )


def attach_classification_evidence(
    classification: BoundaryLabel,
    item: RefinementSegment | RefinementChunk,
    *,
    created_by: str = EVIDENCE_LINK_VERSION,
) -> ClassifiedEvidenceResult:
    expected_id = item.chunk_id if isinstance(item, RefinementChunk) else item.segment_id
    if classification.item_id != expected_id:
        raise ValueError("classification item_id does not match evidence item")

    evidence_link = (
        build_chunk_evidence_link(item, created_by=created_by)
        if isinstance(item, RefinementChunk)
        else build_segment_evidence_link(item, created_by=created_by)
    )
    return ClassifiedEvidenceResult(classification=classification, evidence_link=evidence_link)


def build_search_result_evidence_link(
    result: SearchResult,
    *,
    created_by: str = EVIDENCE_LINK_VERSION,
) -> EvidenceLink:
    quote_ref = result.chunk_id
    return EvidenceLink(
        evidence_id=_evidence_id(result.source_id, result.segment_id, result.chunk_id, quote_ref, created_by),
        source_ref=f"{result.source_path}#{result.chunk_id}",
        source_id=result.source_id,
        segment_id=result.segment_id,
        chunk_id=result.chunk_id,
        path=result.source_path,
        quote_span_or_chunk_id=quote_ref,
        snippet=result.snippet,
        created_by=created_by,
        manifest_ref=result.manifest_ref,
    )


def attach_search_evidence(
    result: SearchResult,
    *,
    created_by: str = EVIDENCE_LINK_VERSION,
) -> SearchEvidenceResult:
    return SearchEvidenceResult(
        search_result=result,
        evidence_link=build_search_result_evidence_link(result, created_by=created_by),
    )


def attach_search_results_evidence(
    results: tuple[SearchResult, ...],
    *,
    created_by: str = EVIDENCE_LINK_VERSION,
) -> tuple[SearchEvidenceResult, ...]:
    return tuple(attach_search_evidence(result, created_by=created_by) for result in results)


def _evidence_id(
    source_id: str,
    segment_id: str,
    chunk_id: str | None,
    quote_ref: str,
    created_by: str,
) -> str:
    raw = f"{source_id}:{segment_id}:{chunk_id or ''}:{quote_ref}:{created_by}".encode("utf-8")
    return f"EVID-{hashlib.sha256(raw).hexdigest()[:16]}"
