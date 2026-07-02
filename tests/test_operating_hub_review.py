import json
from pathlib import Path
import socket
import sys
import tempfile

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_operator import cli  # noqa: E402
from ovis_refinement import BOUNDARY_OVC, BOUNDARY_OVIS, BOUNDARY_REVIEW_AMBIGUOUS, EvidenceLink  # noqa: E402
from ovis_review_promotion import (  # noqa: E402
    REVIEW_ROUTE_CJ_CANDIDATE,
    REVIEW_ROUTE_OVC_SPEC_CANDIDATE,
    REVIEW_ROUTE_REVIEW_LATER,
    REVIEW_STATE_BLOCKED_MISSING_EVIDENCE,
    REVIEW_STATE_PENDING,
    PromotionCandidate,
    build_candidate_id,
    build_review_queue,
    render_review_queue_json,
)
from ovis_operating_hub import (  # noqa: E402
    EVIDENCE_POSTURE_BLOCKED_MISSING_EVIDENCE,
    EVIDENCE_POSTURE_PRESENT,
    ReviewListItem,
    list_review_candidates,
    load_review_candidates_from_queue_json,
    record_to_dict,
    render_review_list_text,
)


def _evidence_link(index: int) -> EvidenceLink:
    segment_id = f"SEG-REVIEW-LIST-{index:04d}"
    chunk_id = f"{segment_id}:chunk_0000"
    return EvidenceLink(
        evidence_id=f"EVID-REVIEW-LIST-{index:04d}",
        source_ref=f"tests/fixtures/operating_hub/review_source.md#{chunk_id}",
        source_id="SRC-REVIEW-LIST",
        segment_id=segment_id,
        chunk_id=chunk_id,
        path="tests/fixtures/operating_hub/review_source.md",
        quote_span_or_chunk_id=chunk_id,
        snippet="Do not expose this full candidate text in list output.",
        created_by="evidence-link-v0",
        manifest_ref="tests/fixtures/operating_hub/review_manifest.json",
    )


def _candidate(
    *,
    boundary: str,
    route: str,
    index: int,
    status: str = REVIEW_STATE_PENDING,
    evidence_links: tuple[EvidenceLink, ...] | None = None,
    ambiguity_status: str | None = None,
) -> PromotionCandidate:
    links = (_evidence_link(index),) if evidence_links is None else evidence_links
    segment_id = f"SEG-REVIEW-LIST-{index:04d}"
    chunk_id = f"{segment_id}:chunk_0000"
    candidate_id = build_candidate_id(
        source_id="SRC-REVIEW-LIST",
        segment_id=segment_id,
        chunk_id=chunk_id,
        boundary=boundary,
        recommended_route=route,
        evidence_links=links,
    )
    return PromotionCandidate(
        candidate_id=candidate_id,
        source_type="b4_review_fixture",
        source_id="SRC-REVIEW-LIST",
        segment_id=segment_id,
        chunk_id=chunk_id,
        boundary=boundary,
        recommended_route=route,
        candidate_title=f"{boundary} review list candidate",
        candidate_text="Do not expose this full candidate text in list output.",
        classifier_reason=f"Matched {boundary} review list fixture.",
        ambiguity_status=ambiguity_status,
        evidence_links=links,
        decision_status=status,
    )


def _candidates() -> tuple[PromotionCandidate, ...]:
    return (
        _candidate(boundary=BOUNDARY_OVIS, route=REVIEW_ROUTE_CJ_CANDIDATE, index=1),
        _candidate(boundary=BOUNDARY_OVC, route=REVIEW_ROUTE_OVC_SPEC_CANDIDATE, index=2),
        _candidate(
            boundary=BOUNDARY_REVIEW_AMBIGUOUS,
            route=REVIEW_ROUTE_REVIEW_LATER,
            index=3,
            status=REVIEW_STATE_BLOCKED_MISSING_EVIDENCE,
            evidence_links=(),
            ambiguity_status=BOUNDARY_REVIEW_AMBIGUOUS,
        ),
    )


def _queue_json_path(candidates: tuple[PromotionCandidate, ...]) -> str:
    queue = build_review_queue(candidates, generated_from="review-list-fixture")
    with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as temp_dir:
        path = Path(temp_dir) / "review_queue.json"
        path.write_text(json.dumps(render_review_queue_json(queue, candidates), sort_keys=True), encoding="utf-8")
        return str(path)


def test_review_list_filters_by_boundary_status_route_and_evidence_posture() -> None:
    candidates = _candidates()

    ovc_items = list_review_candidates(candidates, boundary=BOUNDARY_OVC)
    pending_items = list_review_candidates(candidates, status=REVIEW_STATE_PENDING)
    route_items = list_review_candidates(candidates, route=REVIEW_ROUTE_CJ_CANDIDATE)
    blocked_items = list_review_candidates(candidates, evidence_posture=EVIDENCE_POSTURE_BLOCKED_MISSING_EVIDENCE)

    assert len(ovc_items) == 1
    assert ovc_items[0].boundary == BOUNDARY_OVC
    assert len(pending_items) == 2
    assert {item.status for item in pending_items} == {REVIEW_STATE_PENDING}
    assert len(route_items) == 1
    assert route_items[0].route == REVIEW_ROUTE_CJ_CANDIDATE
    assert len(blocked_items) == 1
    assert blocked_items[0].boundary == BOUNDARY_REVIEW_AMBIGUOUS
    assert blocked_items[0].evidence_posture == EVIDENCE_POSTURE_BLOCKED_MISSING_EVIDENCE


def test_review_list_items_are_deterministic_and_do_not_include_candidate_text() -> None:
    first = list_review_candidates(_candidates())
    second = list_review_candidates(tuple(reversed(_candidates())))
    payload = [record_to_dict(item) for item in first]

    assert first == second
    assert all(isinstance(item, ReviewListItem) for item in first)
    assert [item.candidate_id for item in first] == sorted(item.candidate_id for item in first)
    assert all(item.evidence_posture in {EVIDENCE_POSTURE_PRESENT, EVIDENCE_POSTURE_BLOCKED_MISSING_EVIDENCE} for item in first)
    assert "candidate_text" not in payload[0]
    assert "Do not expose this full candidate text" not in render_review_list_text(first)


def test_load_review_candidates_from_b4_queue_json() -> None:
    candidates = _candidates()
    queue = build_review_queue(candidates, generated_from="review-list-fixture")
    with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as temp_dir:
        path = Path(temp_dir) / "review_queue.json"
        path.write_text(json.dumps(render_review_queue_json(queue, candidates), sort_keys=True), encoding="utf-8")

        loaded = load_review_candidates_from_queue_json(path)

    assert loaded == tuple(sorted(candidates, key=lambda candidate: candidate.candidate_id))


def test_cli_review_list_outputs_filtered_json(capsys: pytest.CaptureFixture[str]) -> None:
    candidates = _candidates()
    queue = build_review_queue(candidates, generated_from="review-list-fixture")
    with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as temp_dir:
        path = Path(temp_dir) / "review_queue.json"
        path.write_text(json.dumps(render_review_queue_json(queue, candidates), sort_keys=True), encoding="utf-8")
        exit_code = cli.main(["review", "list", "--queue-json", str(path), "--boundary", BOUNDARY_OVC, "--json"])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert len(output) == 1
    assert output[0]["boundary"] == BOUNDARY_OVC
    assert output[0]["status"] == REVIEW_STATE_PENDING
    assert output[0]["evidence_refs"] == ["EVID-REVIEW-LIST-0002"]
    assert "candidate_text" not in output[0]


def test_cli_review_list_outputs_text_without_candidate_text(capsys: pytest.CaptureFixture[str]) -> None:
    candidates = _candidates()
    queue = build_review_queue(candidates, generated_from="review-list-fixture")
    with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as temp_dir:
        path = Path(temp_dir) / "review_queue.json"
        path.write_text(json.dumps(render_review_queue_json(queue, candidates), sort_keys=True), encoding="utf-8")
        exit_code = cli.main(["review", "list", "--queue-json", str(path), "--status", REVIEW_STATE_BLOCKED_MISSING_EVIDENCE])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Candidate ID | Boundary | Route | Status | Evidence | Title" in output
    assert BOUNDARY_REVIEW_AMBIGUOUS in output
    assert "Do not expose this full candidate text" not in output


def test_review_list_does_not_require_socket_access(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_socket(*args: object, **kwargs: object) -> None:
        raise AssertionError("review list attempted socket access")

    monkeypatch.setattr(socket, "socket", fail_socket)

    items = list_review_candidates(_candidates(), evidence_posture=EVIDENCE_POSTURE_PRESENT)

    assert len(items) == 2
