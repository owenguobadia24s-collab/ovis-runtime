import socket
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_refinement import (  # noqa: E402
    BOUNDARY_CODEX_VITAE,
    BOUNDARY_GENERAL_INQUIRY,
    BOUNDARY_LIFE_OPS,
    BOUNDARY_OVC,
    BOUNDARY_OVIS,
    BOUNDARY_REVIEW_AMBIGUOUS,
    RefinementSegment,
    attach_classification_evidence,
    attach_search_results_evidence,
    build_chat_retrieval_index,
    build_theme_clusters,
    chunk_refinement_segments,
    classify_refinement_item,
    route_boundary_label,
)


def _validation_segments() -> tuple[RefinementSegment, ...]:
    texts = (
        "Update the CJ register and retrieval evidence ledger before validation close.",
        "Review chart auction context before any trade planning or market execution.",
        "Preserve the invocation as ritual doctrine rather than a daily checklist.",
        "Protect sleep by moving screens away and keeping the routine simple.",
        "Explain the difference between weather and climate with public evidence examples.",
        "Make the operating hub feel like a ritual threshold for every work session.",
    )
    return tuple(
        RefinementSegment(
            segment_id=f"SEG-VALIDATION-{index:04d}",
            source_id="SRC-VALIDATION-PACK",
            message_id=f"MSG-VALIDATION-{index:04d}",
            speaker="User",
            text=text,
            start_index=index * 100,
            end_index=(index * 100) + len(text),
            segment_index=index,
            source_path="tests/fixtures/refinement/validation_pack.md",
            manifest_ref="tests/fixtures/refinement/validation_manifest.json",
        )
        for index, text in enumerate(texts)
    )


def test_validation_pack_represents_all_b1_boundaries_and_review_route() -> None:
    segments = _validation_segments()
    labels = tuple(classify_refinement_item(segment) for segment in segments)

    assert [label.boundary for label in labels] == [
        BOUNDARY_OVIS,
        BOUNDARY_OVC,
        BOUNDARY_CODEX_VITAE,
        BOUNDARY_LIFE_OPS,
        BOUNDARY_GENERAL_INQUIRY,
        BOUNDARY_REVIEW_AMBIGUOUS,
    ]
    assert labels == tuple(classify_refinement_item(segment) for segment in segments)

    review_evidence = attach_classification_evidence(labels[-1], segments[-1]).evidence_link
    route = route_boundary_label(labels[-1], evidence_link=review_evidence)

    assert route.route == BOUNDARY_REVIEW_AMBIGUOUS
    assert route.review_required is True
    assert route.evidence_id == review_evidence.evidence_id


def test_validation_pack_search_results_are_deterministic_and_cited() -> None:
    chunks = chunk_refinement_segments(_validation_segments(), max_words=20)
    index = build_chat_retrieval_index(chunks)

    first = index.search("retrieval evidence", limit=5)
    second = index.search("retrieval evidence", limit=5)
    cited = attach_search_results_evidence(first)

    assert first == second
    assert [result.rank for result in first] == list(range(1, len(first) + 1))
    assert first[0].chunk_id == "SEG-VALIDATION-0000:chunk_0000"
    assert all(result.evidence_link.chunk_id == result.search_result.chunk_id for result in cited)
    assert all(result.evidence_link.source_id == "SRC-VALIDATION-PACK" for result in cited)


def test_validation_pack_theme_grouping_is_deterministic_and_evidence_linked() -> None:
    chunks = chunk_refinement_segments(_validation_segments(), max_words=20)

    first = build_theme_clusters(chunks)
    second = build_theme_clusters(reversed(chunks))
    evidence_cluster = next(cluster for cluster in first if cluster.key == "evidence")

    assert first == second
    assert evidence_cluster.member_count == 2
    assert evidence_cluster.member_ids == (
        "SEG-VALIDATION-0000:chunk_0000",
        "SEG-VALIDATION-0004:chunk_0000",
    )
    assert all(member.evidence_link.evidence_id.startswith("EVID-") for member in evidence_cluster.members)


def test_validation_pack_requires_no_socket_access(monkeypatch) -> None:
    def fail_socket(*args: object, **kwargs: object) -> None:
        raise AssertionError("validation pack attempted socket access")

    monkeypatch.setattr(socket, "socket", fail_socket)
    segments = _validation_segments()
    chunks = chunk_refinement_segments(segments, max_words=20)
    labels = tuple(classify_refinement_item(segment) for segment in segments)
    cited_results = attach_search_results_evidence(build_chat_retrieval_index(chunks).search("evidence"))
    themes = build_theme_clusters(chunks)

    assert labels[0].boundary == BOUNDARY_OVIS
    assert cited_results
    assert themes
