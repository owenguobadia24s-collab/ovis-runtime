import json
from pathlib import Path
import socket
import sys
import tempfile

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_refinement import (  # noqa: E402
    BOUNDARY_CODEX_VITAE,
    BOUNDARY_OVIS,
    CLASSIFIER_VERSION,
    BoundaryLabel,
    ClassifiedEvidenceResult,
    EvidenceLink,
)
from ovis_review_promotion import (  # noqa: E402
    REVIEW_ROUTE_CJ_CANDIDATE,
    REVIEW_ROUTE_DOCTRINE_CANDIDATE,
    REVIEW_STATE_PENDING,
    PromotionCandidate,
    ReviewQueue,
    build_review_queue,
    candidate_from_classified_evidence,
    render_review_queue_json,
    render_review_queue_jsonl,
    render_review_queue_markdown,
    write_review_queue_files,
)


def _classified_result(
    *,
    item_id: str = "SEG-REVIEW-0001:chunk_0000",
    boundary: str = BOUNDARY_OVIS,
    reason: str = "Matched local review evidence.",
) -> ClassifiedEvidenceResult:
    segment_id = item_id.split(":")[0]
    link = EvidenceLink(
        evidence_id=f"EVID-{item_id.replace(':', '-')}",
        source_ref=f"tests/fixtures/review_promotion/source.md#{item_id}",
        source_id="SRC-REVIEW-FIXTURE",
        segment_id=segment_id,
        chunk_id=item_id if ":chunk_" in item_id else None,
        path="tests/fixtures/review_promotion/source.md",
        quote_span_or_chunk_id=item_id,
        snippet="Review this cited candidate without external calls.",
        created_by="evidence-link-v0",
        manifest_ref="tests/fixtures/review_promotion/manifest.json",
    )
    label = BoundaryLabel(
        item_id=item_id,
        boundary=boundary,
        confidence=1.0,
        reason=reason,
        matched_rules=("fixture-rule",),
        classifier_version=CLASSIFIER_VERSION,
        is_ambiguous=False,
        review_required=False,
        scores={boundary: 1},
    )
    return ClassifiedEvidenceResult(classification=label, evidence_link=link)


def test_candidate_from_classified_evidence_preserves_b3_fields() -> None:
    result = _classified_result()

    candidate = candidate_from_classified_evidence(result)

    assert isinstance(candidate, PromotionCandidate)
    assert candidate.candidate_id.startswith("CAND-")
    assert candidate.source_type == "b3_classified_evidence"
    assert candidate.source_id == result.evidence_link.source_id
    assert candidate.segment_id == result.evidence_link.segment_id
    assert candidate.chunk_id == result.evidence_link.chunk_id
    assert candidate.boundary == BOUNDARY_OVIS
    assert candidate.recommended_route == REVIEW_ROUTE_CJ_CANDIDATE
    assert candidate.classifier_reason == result.classification.reason
    assert candidate.evidence_links == (result.evidence_link,)
    assert candidate.decision_status == REVIEW_STATE_PENDING


def test_candidate_default_routes_follow_boundary() -> None:
    candidate = candidate_from_classified_evidence(
        _classified_result(
            item_id="SEG-CODEX-0001",
            boundary=BOUNDARY_CODEX_VITAE,
            reason="Matched doctrine fixture.",
        )
    )

    assert candidate.recommended_route == REVIEW_ROUTE_DOCTRINE_CANDIDATE


def test_review_queue_is_deterministic_and_counts_boundaries() -> None:
    first = candidate_from_classified_evidence(_classified_result(item_id="SEG-REVIEW-0002:chunk_0000"))
    second = candidate_from_classified_evidence(_classified_result(item_id="SEG-CODEX-0001", boundary=BOUNDARY_CODEX_VITAE))

    queue_a = build_review_queue((first, second), generated_from="safe-fixture")
    queue_b = build_review_queue((second, first), generated_from="safe-fixture")

    assert isinstance(queue_a, ReviewQueue)
    assert queue_a == queue_b
    assert queue_a.queue_id.startswith("QUEUE-")
    assert queue_a.candidate_count == 2
    assert queue_a.boundary_counts == {BOUNDARY_CODEX_VITAE: 1, BOUNDARY_OVIS: 1}
    assert queue_a.pending_count == 2
    assert queue_a.source_manifest_refs == ("tests/fixtures/review_promotion/manifest.json",)


def test_rendered_markdown_and_json_preserve_evidence_fields() -> None:
    candidate = candidate_from_classified_evidence(_classified_result())
    queue = build_review_queue((candidate,), generated_from="safe-fixture")

    markdown = render_review_queue_markdown(queue, (candidate,))
    queue_json = render_review_queue_json(queue, (candidate,))
    jsonl = render_review_queue_jsonl((candidate,))

    assert f"## {candidate.candidate_id} -" in markdown
    assert "Boundary: OVIS" in markdown
    assert "Recommended route: cj_candidate" in markdown
    assert "Evidence: EVID-SEG-REVIEW-0001-chunk_0000" in markdown
    assert "- [ ] Approve" in markdown
    assert queue_json["queue"]["queue_id"] == queue.queue_id
    assert queue_json["candidates"][0]["evidence_links"][0]["source_id"] == "SRC-REVIEW-FIXTURE"
    assert json.loads(jsonl)["candidate_id"] == candidate.candidate_id


def test_write_review_queue_files_is_deterministic_under_local_tempdir() -> None:
    candidate = candidate_from_classified_evidence(_classified_result())
    queue = build_review_queue((candidate,), generated_from="safe-fixture")

    with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as temp_dir:
        temp_path = Path(temp_dir)
        first = write_review_queue_files(queue, (candidate,), temp_path / "first", basename="queue")
        second = write_review_queue_files(queue, (candidate,), temp_path / "second", basename="queue")

        assert Path(first.markdown_path).read_text(encoding="utf-8") == Path(second.markdown_path).read_text(encoding="utf-8")
        assert Path(first.json_path).read_text(encoding="utf-8") == Path(second.json_path).read_text(encoding="utf-8")
        assert Path(first.jsonl_path).read_text(encoding="utf-8") == Path(second.jsonl_path).read_text(encoding="utf-8")
        assert json.loads(Path(first.json_path).read_text(encoding="utf-8"))["candidates"][0]["decision_status"] == REVIEW_STATE_PENDING


def test_review_writer_does_not_require_socket_access(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_socket(*args: object, **kwargs: object) -> None:
        raise AssertionError("review writer attempted socket access")

    monkeypatch.setattr(socket, "socket", fail_socket)
    candidate = candidate_from_classified_evidence(_classified_result())
    queue = build_review_queue((candidate,), generated_from="safe-fixture")
    with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as temp_dir:
        files = write_review_queue_files(queue, (candidate,), temp_dir, basename="queue")

        assert Path(files.markdown_path).exists()
