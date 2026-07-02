"""Local review queue rendering and file writing."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable

from ovis_refinement import (
    BOUNDARY_CODEX_VITAE,
    BOUNDARY_GENERAL_INQUIRY,
    BOUNDARY_LIFE_OPS,
    BOUNDARY_OVC,
    BOUNDARY_OVIS,
    BOUNDARY_REVIEW_AMBIGUOUS,
    ClassifiedEvidenceResult,
)

from .types import (
    REVIEW_ROUTE_ARCHIVE_NOTE,
    REVIEW_ROUTE_CJ_CANDIDATE,
    REVIEW_ROUTE_DOCTRINE_CANDIDATE,
    REVIEW_ROUTE_OVC_SPEC_CANDIDATE,
    REVIEW_ROUTE_REVIEW_LATER,
    REVIEW_ROUTE_ROUTINE_ACTION_CANDIDATE,
    REVIEW_STATE_BLOCKED_MISSING_EVIDENCE,
    REVIEW_STATE_PENDING,
    PromotionCandidate,
    ReviewQueue,
    build_candidate_id,
    build_queue_id,
    record_to_dict,
    validate_candidate_evidence,
)


REVIEW_QUEUE_WRITER_VERSION = "review-queue-writer-v0"

DEFAULT_ROUTE_BY_BOUNDARY = {
    BOUNDARY_OVIS: REVIEW_ROUTE_CJ_CANDIDATE,
    BOUNDARY_OVC: REVIEW_ROUTE_OVC_SPEC_CANDIDATE,
    BOUNDARY_CODEX_VITAE: REVIEW_ROUTE_DOCTRINE_CANDIDATE,
    BOUNDARY_LIFE_OPS: REVIEW_ROUTE_ROUTINE_ACTION_CANDIDATE,
    BOUNDARY_GENERAL_INQUIRY: REVIEW_ROUTE_ARCHIVE_NOTE,
    BOUNDARY_REVIEW_AMBIGUOUS: REVIEW_ROUTE_REVIEW_LATER,
}


@dataclass(frozen=True)
class ReviewQueueFiles:
    markdown_path: str
    json_path: str
    jsonl_path: str


def candidate_from_classified_evidence(
    result: ClassifiedEvidenceResult,
    *,
    recommended_route: str | None = None,
    candidate_title: str | None = None,
    candidate_text: str | None = None,
    ambiguity_status: str | None = None,
    source_type: str = "b3_classified_evidence",
) -> PromotionCandidate:
    classification = result.classification
    evidence_link = result.evidence_link
    route = recommended_route or DEFAULT_ROUTE_BY_BOUNDARY.get(classification.boundary, REVIEW_ROUTE_REVIEW_LATER)
    evidence_links = (evidence_link,)
    candidate_id = build_candidate_id(
        source_id=evidence_link.source_id,
        segment_id=evidence_link.segment_id,
        chunk_id=evidence_link.chunk_id,
        boundary=classification.boundary,
        recommended_route=route,
        evidence_links=evidence_links,
    )
    status = REVIEW_STATE_BLOCKED_MISSING_EVIDENCE if evidence_link.evidence_id == "" else REVIEW_STATE_PENDING
    return PromotionCandidate(
        candidate_id=candidate_id,
        source_type=source_type,
        source_id=evidence_link.source_id,
        segment_id=evidence_link.segment_id,
        chunk_id=evidence_link.chunk_id,
        boundary=classification.boundary,
        recommended_route=route,
        candidate_title=candidate_title or _candidate_title(classification.boundary, evidence_link.segment_id, evidence_link.chunk_id),
        candidate_text=candidate_text if candidate_text is not None else evidence_link.snippet or "",
        classifier_reason=classification.reason,
        ambiguity_status=BOUNDARY_REVIEW_AMBIGUOUS if classification.review_required else ambiguity_status,
        evidence_links=evidence_links,
        decision_status=status,
        created_by=REVIEW_QUEUE_WRITER_VERSION,
    )


def build_review_queue(
    candidates: Iterable[PromotionCandidate],
    *,
    generated_from: str,
    generated_at: str | None = None,
) -> ReviewQueue:
    ordered = tuple(sorted(candidates, key=lambda candidate: candidate.candidate_id))
    candidate_ids = tuple(candidate.candidate_id for candidate in ordered)
    boundary_counts = dict(sorted(Counter(candidate.boundary for candidate in ordered).items()))
    pending_count = sum(1 for candidate in ordered if candidate.decision_status == REVIEW_STATE_PENDING)
    manifest_refs = sorted(
        {
            link.manifest_ref
            for candidate in ordered
            for link in candidate.evidence_links
            if link.manifest_ref is not None
        }
    )
    return ReviewQueue(
        queue_id=build_queue_id(generated_from=generated_from, candidate_ids=candidate_ids),
        generated_from=generated_from,
        candidate_ids=candidate_ids,
        candidate_count=len(ordered),
        boundary_counts=boundary_counts,
        pending_count=pending_count,
        source_manifest_refs=tuple(manifest_refs),
        generated_at=generated_at,
    )


def render_review_queue_markdown(queue: ReviewQueue, candidates: Iterable[PromotionCandidate]) -> str:
    ordered = tuple(sorted(candidates, key=lambda candidate: candidate.candidate_id))
    lines = [
        f"# Review Queue {queue.queue_id}",
        "",
        f"Generated from: {queue.generated_from}",
        f"Candidate count: {queue.candidate_count}",
        f"Pending count: {queue.pending_count}",
        "",
    ]
    for candidate in ordered:
        evidence_refs = ", ".join(link.evidence_id for link in candidate.evidence_links) or "MISSING"
        source_ref = _source_ref(candidate)
        reason = candidate.classifier_reason or "None recorded"
        text = _blockquote(candidate.candidate_text)
        lines.extend(
            [
                f"## {candidate.candidate_id} - {candidate.candidate_title}",
                "",
                f"Boundary: {candidate.boundary}",
                f"Recommended route: {candidate.recommended_route}",
                f"Status: {candidate.decision_status}",
                f"Source: {source_ref}",
                f"Reason: {reason}",
                f"Evidence: {evidence_refs}",
                "Text:",
                text,
                "",
                "Decision:",
                "- [ ] Approve",
                "- [ ] Archive",
                "- [ ] Discard",
                "- [ ] Review later",
                "- [ ] Block missing evidence",
                "Notes:",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_review_queue_json(queue: ReviewQueue, candidates: Iterable[PromotionCandidate]) -> dict[str, object]:
    ordered = tuple(sorted(candidates, key=lambda candidate: candidate.candidate_id))
    return {
        "queue": record_to_dict(queue),
        "candidates": [record_to_dict(candidate) for candidate in ordered],
    }


def render_review_queue_jsonl(candidates: Iterable[PromotionCandidate]) -> str:
    ordered = tuple(sorted(candidates, key=lambda candidate: candidate.candidate_id))
    return "".join(json.dumps(record_to_dict(candidate), sort_keys=True) + "\n" for candidate in ordered)


def write_review_queue_files(
    queue: ReviewQueue,
    candidates: Iterable[PromotionCandidate],
    output_dir: str | Path,
    *,
    basename: str = "review_queue",
) -> ReviewQueueFiles:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    markdown_path = target / f"{basename}.md"
    json_path = target / f"{basename}.json"
    jsonl_path = target / f"{basename}.jsonl"

    markdown_path.write_text(render_review_queue_markdown(queue, candidates), encoding="utf-8")
    json_path.write_text(json.dumps(render_review_queue_json(queue, candidates), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    jsonl_path.write_text(render_review_queue_jsonl(candidates), encoding="utf-8")

    return ReviewQueueFiles(
        markdown_path=str(markdown_path),
        json_path=str(json_path),
        jsonl_path=str(jsonl_path),
    )


def _candidate_title(boundary: str, segment_id: str, chunk_id: str | None) -> str:
    ref = chunk_id or segment_id
    return f"{boundary} review candidate {ref}"


def _source_ref(candidate: PromotionCandidate) -> str:
    return f"{candidate.source_id} / {candidate.segment_id or ''} / {candidate.chunk_id or ''}"


def _blockquote(text: str) -> str:
    if not text:
        return "> "
    return "\n".join(f"> {line}" for line in text.splitlines())
