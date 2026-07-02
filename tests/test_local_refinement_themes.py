from dataclasses import replace
from pathlib import Path
import socket
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_chat_ingestion import parse_transcript_file  # noqa: E402
from ovis_refinement import (  # noqa: E402
    THEME_PASS_VERSION,
    ThemeCluster,
    adapt_chat_segments,
    build_segment_evidence_link,
    build_theme_clusters,
    chunk_refinement_segments,
)


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "chat_ingestion"


def _segments_with_repeated_topics():
    parsed = parse_transcript_file(FIXTURE_ROOT / "sample_transcript.md")
    segments = adapt_chat_segments(parsed.source, parsed.segments, manifest=parsed.manifest)
    return (
        replace(segments[0], text="Local retrieval evidence keeps source citations stable."),
        replace(segments[1], text="Review retrieval evidence before promotion decisions."),
        replace(segments[2], text="Hydration routine planning belongs in life ops."),
    )


def test_theme_clusters_are_deterministic_and_source_preserving() -> None:
    segments = _segments_with_repeated_topics()

    first = build_theme_clusters(segments)
    second = build_theme_clusters(reversed(segments))

    assert first == second
    evidence_cluster = next(cluster for cluster in first if cluster.key == "evidence")
    assert isinstance(evidence_cluster, ThemeCluster)
    assert evidence_cluster.cluster_id.startswith("THEME-")
    assert evidence_cluster.member_count == 2
    assert evidence_cluster.member_ids == (segments[0].segment_id, segments[1].segment_id)
    assert evidence_cluster.source_ids == (segments[0].source_id,)
    assert evidence_cluster.segment_ids == (segments[0].segment_id, segments[1].segment_id)
    assert all(member.evidence_link.created_by == THEME_PASS_VERSION for member in evidence_cluster.members)
    assert all(member.evidence_link.segment_id == member.segment_id for member in evidence_cluster.members)
    assert THEME_PASS_VERSION == "theme-dedup-v0"


def test_theme_clusters_ignore_singletons() -> None:
    segments = _segments_with_repeated_topics()

    clusters = build_theme_clusters(segments)

    keys = {cluster.key for cluster in clusters}
    assert "hydration" not in keys
    assert "routine" not in keys
    assert {"evidence", "retrieval"}.issubset(keys)


def test_theme_clusters_accept_prebuilt_evidence_links() -> None:
    segments = _segments_with_repeated_topics()
    evidence_links = {segment.segment_id: build_segment_evidence_link(segment) for segment in segments}

    clusters = build_theme_clusters(segments, evidence_links=evidence_links)
    evidence_cluster = next(cluster for cluster in clusters if cluster.key == "evidence")

    assert [member.evidence_link for member in evidence_cluster.members] == [
        evidence_links[segments[0].segment_id],
        evidence_links[segments[1].segment_id],
    ]


def test_theme_clusters_support_chunks() -> None:
    segments = _segments_with_repeated_topics()
    chunks = chunk_refinement_segments(segments, max_words=20)

    clusters = build_theme_clusters(chunks)
    retrieval_cluster = next(cluster for cluster in clusters if cluster.key == "retrieval")

    assert retrieval_cluster.member_count == 2
    assert all(member.chunk_id is not None for member in retrieval_cluster.members)
    assert all(member.evidence_link.chunk_id == member.chunk_id for member in retrieval_cluster.members)


def test_theme_clusters_validate_thresholds() -> None:
    with pytest.raises(ValueError, match="min_members"):
        build_theme_clusters(_segments_with_repeated_topics(), min_members=1)

    with pytest.raises(ValueError, match="max_terms_per_item"):
        build_theme_clusters(_segments_with_repeated_topics(), max_terms_per_item=0)


def test_theme_grouping_does_not_require_socket_access(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_socket(*args: object, **kwargs: object) -> None:
        raise AssertionError("theme grouping attempted socket access")

    monkeypatch.setattr(socket, "socket", fail_socket)
    clusters = build_theme_clusters(_segments_with_repeated_topics())

    assert any(cluster.key == "retrieval" for cluster in clusters)
