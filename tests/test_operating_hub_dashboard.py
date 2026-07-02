import json
from pathlib import Path
import socket
import sys
import tempfile

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_operator import cli  # noqa: E402
from ovis_refinement import (  # noqa: E402
    BOUNDARY_OVC,
    BOUNDARY_OVIS,
    BOUNDARY_REVIEW_AMBIGUOUS,
    EvidenceLink,
)
from ovis_review_promotion import (  # noqa: E402
    REVIEW_DECISION_APPROVE,
    REVIEW_ROUTE_CJ_CANDIDATE,
    REVIEW_ROUTE_OVC_SPEC_CANDIDATE,
    REVIEW_ROUTE_REVIEW_LATER,
    REVIEW_STATE_BLOCKED_MISSING_EVIDENCE,
    PromotionCandidate,
    ReviewQueue,
    build_candidate_id,
    build_queue_id,
    create_local_promotion_output,
    record_review_decision,
)
from ovis_operating_hub import (  # noqa: E402
    DAILY_DASHBOARD_RENDERER_VERSION,
    HubNextAction,
    build_hub_status,
    build_next_action,
    hub_status_from_dict,
    load_hub_status_json,
    record_to_dict,
    render_dashboard_markdown,
    render_next_action_text,
    write_dashboard_markdown,
)


def _evidence_link(boundary: str, index: int) -> EvidenceLink:
    segment_id = f"SEG-DASH-{index:04d}"
    chunk_id = f"{segment_id}:chunk_0000"
    return EvidenceLink(
        evidence_id=f"EVID-DASH-{index:04d}",
        source_ref=f"tests/fixtures/operating_hub/dashboard_source.md#{chunk_id}",
        source_id="SRC-DASHBOARD",
        segment_id=segment_id,
        chunk_id=chunk_id,
        path="tests/fixtures/operating_hub/dashboard_source.md",
        quote_span_or_chunk_id=chunk_id,
        snippet=f"{boundary} safe dashboard fixture candidate.",
        created_by="evidence-link-v0",
        manifest_ref="tests/fixtures/operating_hub/dashboard_manifest.json",
    )


def _candidate(
    *,
    boundary: str,
    route: str,
    index: int,
    evidence_links: tuple[EvidenceLink, ...] | None = None,
    status: str = "pending_review",
) -> PromotionCandidate:
    links = (_evidence_link(boundary, index),) if evidence_links is None else evidence_links
    segment_id = f"SEG-DASH-{index:04d}"
    chunk_id = f"{segment_id}:chunk_0000"
    candidate_id = build_candidate_id(
        source_id="SRC-DASHBOARD",
        segment_id=segment_id,
        chunk_id=chunk_id,
        boundary=boundary,
        recommended_route=route,
        evidence_links=links,
    )
    return PromotionCandidate(
        candidate_id=candidate_id,
        source_type="b5_dashboard_fixture",
        source_id="SRC-DASHBOARD",
        segment_id=segment_id,
        chunk_id=chunk_id,
        boundary=boundary,
        recommended_route=route,
        candidate_title=f"{boundary} dashboard fixture",
        candidate_text=f"{boundary} safe dashboard fixture candidate.",
        classifier_reason=f"Matched {boundary} dashboard fixture.",
        ambiguity_status=BOUNDARY_REVIEW_AMBIGUOUS if boundary == BOUNDARY_REVIEW_AMBIGUOUS else None,
        evidence_links=links,
        decision_status=status,
    )


def _status_payload() -> dict[str, object]:
    ovis = _candidate(boundary=BOUNDARY_OVIS, route=REVIEW_ROUTE_CJ_CANDIDATE, index=1)
    ovc = _candidate(boundary=BOUNDARY_OVC, route=REVIEW_ROUTE_OVC_SPEC_CANDIDATE, index=2)
    ambiguous = _candidate(
        boundary=BOUNDARY_REVIEW_AMBIGUOUS,
        route=REVIEW_ROUTE_REVIEW_LATER,
        index=3,
        evidence_links=(),
        status=REVIEW_STATE_BLOCKED_MISSING_EVIDENCE,
    )
    approval = record_review_decision(
        ovc,
        decision=REVIEW_DECISION_APPROVE,
        reviewer="operator",
        reason_or_notes="Approved local dashboard fixture.",
    )
    output = create_local_promotion_output(
        ovc,
        approval,
        output_type="ovc_spec_candidate_markdown",
        output_path_or_ref="local/promotions/OVC-DASH.md",
    )
    candidates = (ovis, ovc, ambiguous)
    queue = ReviewQueue(
        queue_id=build_queue_id(generated_from="dashboard-fixture", candidate_ids=tuple(candidate.candidate_id for candidate in candidates)),
        generated_from="dashboard-fixture",
        candidate_ids=tuple(candidate.candidate_id for candidate in candidates),
        candidate_count=len(candidates),
        boundary_counts={BOUNDARY_OVIS: 1, BOUNDARY_OVC: 1, BOUNDARY_REVIEW_AMBIGUOUS: 1},
        pending_count=1,
        source_manifest_refs=("tests/fixtures/operating_hub/dashboard_manifest.json",),
    )
    status = build_hub_status(
        candidates,
        decisions=(approval,),
        promotion_outputs=(output,),
        review_queues=(queue,),
        open_cj_counts={BOUNDARY_OVIS: 1},
        generated_from=("tests/fixtures/operating_hub/dashboard_status.json",),
        active_bundle="Bundle 5 - Operating Hub v0.1",
        active_cj="CJ-B5-005_DAILY_SESSION_DASHBOARD",
        validation_posture="known_pass",
        external_side_effects="disabled",
    )
    return record_to_dict(status)


def _status_path(temp_dir: str) -> Path:
    path = Path(temp_dir) / "hub_status.json"
    path.write_text(json.dumps(_status_payload(), sort_keys=True), encoding="utf-8")
    return path


def test_dashboard_markdown_is_deterministic_and_contains_operating_surface() -> None:
    status = hub_status_from_dict(_status_payload())

    first = render_dashboard_markdown(status)
    second = render_dashboard_markdown(hub_status_from_dict(_status_payload()))

    assert first == second
    assert DAILY_DASHBOARD_RENDERER_VERSION in first
    assert "CJ-B5-005_DAILY_SESSION_DASHBOARD" in first
    assert "Validation posture: known_pass" in first
    assert "External side effects: disabled" in first
    assert "Review / Ambiguous: repair blocked evidence." in first
    assert "Blocked boundaries: Review / Ambiguous=1" in first
    assert "Promote only already-approved candidates to local output references." in first


def test_next_action_has_reason_and_local_source_refs() -> None:
    status = hub_status_from_dict(_status_payload())
    next_action = build_next_action(status)
    rendered = render_next_action_text(status)

    assert isinstance(next_action, HubNextAction)
    assert next_action.action == "Review / Ambiguous: repair blocked evidence."
    assert next_action.reason == "Blocked evidence takes priority before local promotion or CJ advancement."
    assert rendered.startswith("action: Review / Ambiguous: repair blocked evidence.")
    assert next_action.source_refs == ()


def test_load_and_write_dashboard_markdown_round_trip() -> None:
    with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as temp_dir:
        status_path = _status_path(temp_dir)
        status = load_hub_status_json(status_path)
        output_path = write_dashboard_markdown(status, Path(temp_dir) / "dashboard.md")

        rendered = output_path.read_text(encoding="utf-8")

    assert status.active_cj == "CJ-B5-005_DAILY_SESSION_DASHBOARD"
    assert rendered.startswith("# OVIS First Surface Daily Session Dashboard")
    assert "`tests/fixtures/operating_hub/dashboard_status.json`" in rendered


def test_cli_hub_render_and_next_use_local_status_json(capsys: pytest.CaptureFixture[str]) -> None:
    with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as temp_dir:
        status_path = _status_path(temp_dir)
        render_code = cli.main(["hub", "render", "--status-json", str(status_path)])
        render_output = capsys.readouterr().out
        next_code = cli.main(["hub", "next", "--status-json", str(status_path), "--json"])
        next_output = json.loads(capsys.readouterr().out)

    assert render_code == 0
    assert "# OVIS First Surface Daily Session Dashboard" in render_output
    assert "Project Status By Boundary" in render_output
    assert next_code == 0
    assert next_output["next_action"] == "Review / Ambiguous: repair blocked evidence."


def test_dashboard_rendering_does_not_require_socket_access(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_socket(*args: object, **kwargs: object) -> None:
        raise AssertionError("dashboard rendering attempted socket access")

    monkeypatch.setattr(socket, "socket", fail_socket)
    status = hub_status_from_dict(_status_payload())

    assert "Daily Operating Rhythm" in render_dashboard_markdown(status)
