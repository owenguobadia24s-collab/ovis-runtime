from pathlib import Path
import socket
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_chat_ingestion import (  # noqa: E402
    CHATGPT_EXPORT_PARSER_VERSION,
    PARSER_VERSION,
    SOURCE_TYPE_CHATGPT_EXPORT,
    SOURCE_TYPE_TRANSCRIPT,
    parse_chatgpt_export_file,
    parse_transcript_file,
    parse_transcript_text,
    record_to_json,
)


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "chat_ingestion"


def test_transcript_fixture_import_is_deterministic_and_source_preserving() -> None:
    fixture = FIXTURE_ROOT / "sample_transcript.md"

    first = parse_transcript_file(fixture)
    second = parse_transcript_file(fixture)

    assert first.source == second.source
    assert first.messages == second.messages
    assert first.segments == second.segments
    assert first.manifest == second.manifest
    assert first.source.source_type == SOURCE_TYPE_TRANSCRIPT
    assert first.source.title == "Synthetic Intake Check"
    assert first.source.path == str(fixture)
    assert first.source.parser_version == PARSER_VERSION
    assert first.source.import_status == "imported"
    assert first.source.message_count == 3
    assert first.source.segment_count == 3
    assert first.manifest.raw_path == str(fixture)
    assert first.manifest.parser_version == PARSER_VERSION
    assert first.manifest.import_status == "imported"
    assert [message.message_index for message in first.messages] == [0, 1, 2]
    assert [segment.segment_index for segment in first.segments] == [0, 1, 2]
    assert record_to_json(first.source) == record_to_json(second.source)


def test_transcript_malformed_input_returns_visible_error_manifest() -> None:
    parsed = parse_transcript_text("This has no explicit speaker markers.", source_path="bad.md")

    assert parsed.source.import_status == "error"
    assert parsed.manifest.import_status == "error"
    assert parsed.messages == ()
    assert parsed.segments == ()
    assert parsed.manifest.errors == ("no User:/Assistant: messages found",)


def test_chatgpt_export_fixture_import_is_deterministic_and_source_preserving() -> None:
    fixture = FIXTURE_ROOT / "sample_chatgpt_export.json"

    first = parse_chatgpt_export_file(fixture)
    second = parse_chatgpt_export_file(fixture)

    assert first.sources == second.sources
    assert first.messages == second.messages
    assert first.segments == second.segments
    assert first.manifests == second.manifests
    assert first.errors == ()
    assert len(first.sources) == 1
    assert len(first.messages) == 2
    assert len(first.segments) == 2
    assert len(first.manifests) == 1
    assert first.sources[0].source_type == SOURCE_TYPE_CHATGPT_EXPORT
    assert first.sources[0].path == f"{fixture}#synthetic-conversation-001"
    assert first.sources[0].parser_version == CHATGPT_EXPORT_PARSER_VERSION
    assert first.sources[0].import_status == "imported"
    assert first.manifests[0].raw_path == str(fixture)
    assert first.manifests[0].parser_version == CHATGPT_EXPORT_PARSER_VERSION
    assert first.manifests[0].import_status == "imported"
    assert [message.speaker for message in first.messages] == ["user", "assistant"]
    assert [message.message_index for message in first.messages] == [0, 1]
    assert [segment.segment_index for segment in first.segments] == [0, 1]
    assert record_to_json(first.sources[0]) == record_to_json(second.sources[0])


def test_ingestion_parsers_do_not_require_socket_access(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_socket(*args: object, **kwargs: object) -> None:
        raise AssertionError("ingestion parser attempted socket access")

    monkeypatch.setattr(socket, "socket", fail_socket)

    transcript = parse_transcript_file(FIXTURE_ROOT / "sample_transcript.md")
    export = parse_chatgpt_export_file(FIXTURE_ROOT / "sample_chatgpt_export.json")

    assert transcript.manifest.import_status == "imported"
    assert export.manifests[0].import_status == "imported"
