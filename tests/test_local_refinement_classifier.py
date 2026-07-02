from pathlib import Path
import socket
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_chat_ingestion import parse_transcript_file  # noqa: E402
from ovis_refinement import (  # noqa: E402
    BOUNDARY_CODEX_VITAE,
    BOUNDARY_GENERAL_INQUIRY,
    BOUNDARY_LIFE_OPS,
    BOUNDARY_OVC,
    BOUNDARY_OVIS,
    BOUNDARY_REVIEW_AMBIGUOUS,
    CLASSIFIER_VERSION,
    BoundaryLabel,
    adapt_chat_segments,
    classify_refinement_item,
    classify_text,
)


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "chat_ingestion"


@pytest.mark.parametrize(
    ("text", "expected_boundary", "expected_rule"),
    [
        (
            "Update the B1 CJ register after the taxonomy doc closes and record validation evidence.",
            BOUNDARY_OVIS,
            "OVIS-CJ-REGISTER",
        ),
        (
            "Add a rule that chart review must identify the active auction condition before trade planning.",
            BOUNDARY_OVC,
            "OVC-CHART",
        ),
        (
            "Capture the morning invocation as a ritual text, not a productivity checklist.",
            BOUNDARY_CODEX_VITAE,
            "CODEX-RITUAL",
        ),
        (
            "Move screens out of reach after 10:30 p.m. to protect sleep.",
            BOUNDARY_LIFE_OPS,
            "LIFE-SLEEP",
        ),
        (
            "Explain the difference between weather and climate.",
            BOUNDARY_GENERAL_INQUIRY,
            "GEN-EXPLAIN",
        ),
    ],
)
def test_classifier_assigns_b1_seed_boundaries(
    text: str,
    expected_boundary: str,
    expected_rule: str,
) -> None:
    label = classify_text(text, item_id="fixture")

    assert isinstance(label, BoundaryLabel)
    assert label.boundary == expected_boundary
    assert label.confidence > 0
    assert expected_rule in label.matched_rules
    assert label.classifier_version == CLASSIFIER_VERSION
    assert label.is_ambiguous is False
    assert label.review_required is False
    assert label.reason


@pytest.mark.parametrize(
    "text",
    [
        "Make the operating hub feel like a ritual threshold for every work session.",
        "My poor trade entries are probably a discipline problem, so build a morning routine around entry patience.",
        "This belongs in the system somewhere, probably as a task or doctrine.",
    ],
)
def test_classifier_routes_mixed_or_insufficient_material_to_review(text: str) -> None:
    label = classify_text(text, item_id="mixed")

    assert label.boundary == BOUNDARY_REVIEW_AMBIGUOUS
    assert label.is_ambiguous is True
    assert label.review_required is True
    assert label.classifier_version == CLASSIFIER_VERSION
    assert label.reason


def test_classifier_is_deterministic_for_fixed_text() -> None:
    text = "Repair metadata registry authority so reconcile reports zero drift before bundle close."

    assert classify_text(text, item_id="same") == classify_text(text, item_id="same")


def test_classifier_accepts_refinement_segments() -> None:
    parsed = parse_transcript_file(FIXTURE_ROOT / "sample_transcript.md")
    segment = adapt_chat_segments(parsed.source, parsed.segments, manifest=parsed.manifest)[0]

    label = classify_refinement_item(segment)

    assert label.item_id == segment.segment_id
    assert label.classifier_version == CLASSIFIER_VERSION
    assert label.boundary in {
        BOUNDARY_OVIS,
        BOUNDARY_OVC,
        BOUNDARY_CODEX_VITAE,
        BOUNDARY_LIFE_OPS,
        BOUNDARY_GENERAL_INQUIRY,
        BOUNDARY_REVIEW_AMBIGUOUS,
    }


def test_classifier_does_not_require_socket_access(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_socket(*args: object, **kwargs: object) -> None:
        raise AssertionError("classifier attempted socket access")

    monkeypatch.setattr(socket, "socket", fail_socket)

    label = classify_text("Define how local retrieval results preserve citation evidence for later review.")

    assert label.boundary == BOUNDARY_OVIS
