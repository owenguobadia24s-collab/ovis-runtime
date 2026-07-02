import json
from pathlib import Path
import socket
import sys
import tempfile

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_operator import cli  # noqa: E402
from ovis_refinement import EvidenceLink  # noqa: E402
from ovis_review_promotion import (  # noqa: E402
    REVIEW_DECISION_APPROVE,
    REVIEW_DECISION_ARCHIVE,
    REVIEW_ROUTE_CJ_CANDIDATE,
    REVIEW_STATE_PROMOTED_LOCAL,
    PromotionCandidate,
    ReviewDecision,
    build_candidate_id,
    build_review_queue,
    record_review_decision,
    record_to_dict,
    render_review_queue_json,
)
from ovis_operating_hub import (  # noqa: E402
    DEFAULT_PROMOTION_GENERATOR,
    DEFAULT_PROMOTION_OUTPUT_TYPE,
    load_review_candidates_from_queue_json,
    load_review_decisions_json,
    prepare_local_promotion,
    render_promotion_output_text,
)


def _evidence_link() -> EvidenceLink:
    return EvidenceLink(
        evidence_id="EVID-HUB-PROMOTE-0001",
        source_ref="tests/fixtures/operating_hub/promotion_source.md#SEG-HUB-PROMOTE-0001:chunk_0000",
        source_id="SRC-HUB-PROMOTE",
        segment_id="SEG-HUB-PROMOTE-0001",
        chunk_id="SEG-HUB-PROMOTE-0001:chunk_0000",
        path="tests/fixtures/operating_hub/promotion_source.md",
        quote_span_or_chunk_id="SEG-HUB-PROMOTE-0001:chunk_0000",
        snippet="Promote this only after local operator approval.",
        created_by="evidence-link-v0",
        manifest_ref="tests/fixtures/operating_hub/promotion_manifest.json",
    )


def _candidate(*, evidence_links: tuple[EvidenceLink, ...] | None = None, route: str = REVIEW_ROUTE_CJ_CANDIDATE) -> PromotionCandidate:
    links = (_evidence_link(),) if evidence_links is None else evidence_links
    candidate_id = build_candidate_id(
        source_id="SRC-HUB-PROMOTE",
        segment_id="SEG-HUB-PROMOTE-0001",
        chunk_id="SEG-HUB-PROMOTE-0001:chunk_0000",
        boundary="OVIS",
        recommended_route=route,
        evidence_links=links,
    )
    return PromotionCandidate(
        candidate_id=candidate_id,
        source_type="b4_review_fixture",
        source_id="SRC-HUB-PROMOTE",
        segment_id="SEG-HUB-PROMOTE-0001",
        chunk_id="SEG-HUB-PROMOTE-0001:chunk_0000",
        boundary="OVIS",
        recommended_route=route,
        candidate_title="Prepare local promotion command candidate",
        candidate_text="Promote this only after local operator approval.",
        classifier_reason="Matched OVIS CJ route with source evidence.",
        ambiguity_status=None,
        evidence_links=links,
    )


def _queue_path(candidate: PromotionCandidate, temp_dir: str) -> Path:
    queue = build_review_queue((candidate,), generated_from="hub-promotion-fixture")
    path = Path(temp_dir) / "review_queue.json"
    path.write_text(json.dumps(render_review_queue_json(queue, (candidate,)), sort_keys=True), encoding="utf-8")
    return path


def _decision_path(decisions: tuple[ReviewDecision, ...], temp_dir: str) -> Path:
    path = Path(temp_dir) / "review_decisions.json"
    path.write_text(json.dumps([record_to_dict(decision) for decision in decisions], sort_keys=True), encoding="utf-8")
    return path


def test_prepare_local_promotion_requires_approved_decision_and_preserves_evidence() -> None:
    candidate = _candidate()
    approval = record_review_decision(
        candidate,
        decision=REVIEW_DECISION_APPROVE,
        reviewer="operator",
        reason_or_notes="Approved for local promotion reference.",
    )

    output = prepare_local_promotion(
        (candidate,),
        (approval,),
        candidate_id=candidate.candidate_id,
        output_path_or_ref="data/ovis-first-surface/promotions/local/CAND.md",
    )

    assert output.promotion_id.startswith("PROMO-")
    assert output.candidate_id == candidate.candidate_id
    assert output.route == REVIEW_ROUTE_CJ_CANDIDATE
    assert output.source_evidence_links == candidate.evidence_links
    assert output.decision_id == approval.decision_id
    assert output.generated_by == DEFAULT_PROMOTION_GENERATOR
    assert output.output_type == DEFAULT_PROMOTION_OUTPUT_TYPE
    assert output.promotion_status == REVIEW_STATE_PROMOTED_LOCAL


def test_prepare_local_promotion_refuses_unapproved_and_missing_evidence_candidates() -> None:
    candidate = _candidate()
    archive = record_review_decision(
        candidate,
        decision=REVIEW_DECISION_ARCHIVE,
        reviewer="operator",
        reason_or_notes="Archive only.",
    )

    with pytest.raises(ValueError, match="no approved decision"):
        prepare_local_promotion(
            (candidate,),
            (archive,),
            candidate_id=candidate.candidate_id,
            output_path_or_ref="local/promotions/archive.md",
        )

    missing_evidence = _candidate(evidence_links=())
    missing_approval = record_review_decision(
        missing_evidence,
        decision=REVIEW_DECISION_APPROVE,
        reviewer="operator",
        reason_or_notes="This approval must still be blocked by missing evidence.",
    )
    with pytest.raises(ValueError, match="blocked_missing_evidence"):
        prepare_local_promotion(
            (missing_evidence,),
            (missing_approval,),
            candidate_id=missing_evidence.candidate_id,
            output_path_or_ref="local/promotions/missing.md",
        )


def test_prepare_local_promotion_refuses_blocked_route_and_route_mismatch() -> None:
    candidate = _candidate()
    approval = record_review_decision(
        candidate,
        decision=REVIEW_DECISION_APPROVE,
        reviewer="operator",
        reason_or_notes="Approved with a valid route.",
    )
    blocked_route = ReviewDecision(
        **{
            **record_to_dict(approval),
            "route": "not_allowed",
            "evidence_links": approval.evidence_links,
        }
    )

    with pytest.raises(ValueError, match="not allowed"):
        prepare_local_promotion(
            (candidate,),
            (blocked_route,),
            candidate_id=candidate.candidate_id,
            output_path_or_ref="local/promotions/blocked.md",
        )

    with pytest.raises(ValueError, match="does not match"):
        prepare_local_promotion(
            (candidate,),
            (approval,),
            candidate_id=candidate.candidate_id,
            route="doctrine_candidate",
            output_path_or_ref="local/promotions/mismatch.md",
        )


def test_loaders_and_cli_promote_emit_local_output_without_candidate_text(capsys: pytest.CaptureFixture[str]) -> None:
    candidate = _candidate()
    approval = record_review_decision(
        candidate,
        decision=REVIEW_DECISION_APPROVE,
        reviewer="operator",
        reason_or_notes="Approved for CLI promotion reference.",
    )
    with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as temp_dir:
        queue_path = _queue_path(candidate, temp_dir)
        decision_path = _decision_path((approval,), temp_dir)

        assert load_review_candidates_from_queue_json(queue_path) == (candidate,)
        assert load_review_decisions_json(decision_path) == (approval,)
        exit_code = cli.main(
            [
                "review",
                "promote",
                candidate.candidate_id,
                "--queue-json",
                str(queue_path),
                "--decision-json",
                str(decision_path),
                "--output-ref",
                "data/ovis-first-surface/promotions/local/CAND.md",
                "--json",
            ]
        )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output["candidate_id"] == candidate.candidate_id
    assert output["decision_id"] == approval.decision_id
    assert output["source_evidence_links"][0]["evidence_id"] == "EVID-HUB-PROMOTE-0001"
    assert "candidate_text" not in output


def test_rendered_promotion_text_and_command_do_not_require_socket_access(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_socket(*args: object, **kwargs: object) -> None:
        raise AssertionError("promotion command attempted socket access")

    monkeypatch.setattr(socket, "socket", fail_socket)
    candidate = _candidate()
    approval = record_review_decision(
        candidate,
        decision=REVIEW_DECISION_APPROVE,
        reviewer="operator",
        reason_or_notes="Approved without external calls.",
    )

    output = prepare_local_promotion(
        (candidate,),
        (approval,),
        candidate_id=candidate.candidate_id,
        output_path_or_ref="data/ovis-first-surface/promotions/local/CAND.md",
    )
    rendered = render_promotion_output_text(output)

    assert output.source_evidence_links == candidate.evidence_links
    assert "EVID-HUB-PROMOTE-0001" in rendered
    assert "Promote this only after local operator approval" not in rendered
