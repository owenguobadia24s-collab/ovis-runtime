"""Parser for explicit-speaker markdown/plain-text chat transcripts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .types import (
    IMPORT_MANIFEST_VERSION,
    PARSER_VERSION,
    SOURCE_TYPE_TRANSCRIPT,
    ChatMessage,
    ChatSegment,
    ChatSource,
    ImportManifest,
    make_message_id,
    make_segment_id,
    make_transcript_source_id,
    raw_sha256_hexdigest,
)


SPEAKER_MARKER_RE = re.compile(r"^(User|Assistant):(?:\s?(.*))$")


@dataclass(frozen=True)
class ParsedTranscript:
    source: ChatSource
    messages: tuple[ChatMessage, ...]
    segments: tuple[ChatSegment, ...]
    manifest: ImportManifest


@dataclass(frozen=True)
class _MessageDraft:
    speaker: str
    text: str
    start_index: int
    end_index: int


def parse_transcript_file(path: str | Path) -> ParsedTranscript:
    source_path = Path(path)
    return parse_transcript_text(source_path.read_text(encoding="utf-8"), source_path=str(source_path))


def parse_transcript_text(raw_text: str, *, source_path: str = "<memory>") -> ParsedTranscript:
    raw_sha256 = raw_sha256_hexdigest(raw_text.encode("utf-8"))
    source_id = make_transcript_source_id(raw_sha256)
    title, body_start = _extract_title(raw_text)
    drafts, warnings = _parse_message_drafts(raw_text, body_start)
    errors: tuple[str, ...] = () if drafts else ("no User:/Assistant: messages found",)
    import_status = "imported" if not errors else "error"

    messages = tuple(
        ChatMessage(
            message_id=make_message_id(source_id, index),
            source_id=source_id,
            speaker=draft.speaker,
            text=draft.text,
            message_index=index,
            raw_start_index=draft.start_index,
            raw_end_index=draft.end_index,
        )
        for index, draft in enumerate(drafts)
    )
    segments = tuple(
        ChatSegment(
            segment_id=make_segment_id(source_id, index),
            source_id=source_id,
            message_id=message.message_id,
            speaker=message.speaker,
            text=message.text,
            start_index=message.raw_start_index if message.raw_start_index is not None else 0,
            end_index=message.raw_end_index if message.raw_end_index is not None else 0,
            segment_index=index,
            timestamp=message.timestamp,
        )
        for index, message in enumerate(messages)
    )
    source = ChatSource(
        source_id=source_id,
        source_type=SOURCE_TYPE_TRANSCRIPT,
        path=source_path,
        title=title,
        created_at=None,
        imported_at=None,
        import_status=import_status,
        parser_version=PARSER_VERSION,
        raw_sha256=raw_sha256,
        message_count=len(messages),
        segment_count=len(segments),
    )
    manifest = ImportManifest(
        manifest_version=IMPORT_MANIFEST_VERSION,
        source_id=source_id,
        source_type=SOURCE_TYPE_TRANSCRIPT,
        raw_path=source_path,
        normalized_source_path=f"data/ovis-first-surface/chat-sources/{source_id}.json",
        normalized_segment_path=f"data/ovis-first-surface/chat-segments/{source_id}.jsonl",
        parser_version=PARSER_VERSION,
        import_status=import_status,
        created_at=None,
        raw_sha256=raw_sha256,
        errors=errors,
        warnings=tuple(warnings),
    )
    return ParsedTranscript(source=source, messages=messages, segments=segments, manifest=manifest)


def _extract_title(raw_text: str) -> tuple[str | None, int]:
    for match in re.finditer(r"(?m)^[^\S\r\n]*(\S.*)$", raw_text):
        line = match.group(1).strip()
        if line.startswith("# "):
            return line[2:].strip() or None, _line_end(raw_text, match.end())
        return None, 0
    return None, 0


def _parse_message_drafts(raw_text: str, start_offset: int) -> tuple[tuple[_MessageDraft, ...], list[str]]:
    drafts: list[_MessageDraft] = []
    warnings: list[str] = []
    current_speaker: str | None = None
    current_parts: list[str] = []
    current_start: int | None = None
    current_end: int | None = None

    for line_start, line_end, line in _iter_lines_with_offsets(raw_text[start_offset:], start_offset):
        marker_match = SPEAKER_MARKER_RE.match(line.rstrip("\r\n"))
        if marker_match:
            if current_speaker is not None and current_start is not None and current_end is not None:
                drafts.append(_MessageDraft(current_speaker, "\n".join(current_parts).strip(), current_start, current_end))
            current_speaker = marker_match.group(1)
            current_parts = [marker_match.group(2) or ""]
            current_start = line_start
            current_end = line_end
            continue

        if current_speaker is None:
            if line.strip():
                warnings.append(f"ignored text before first speaker marker at offset {line_start}")
            continue

        current_parts.append(line.rstrip("\r\n"))
        current_end = line_end

    if current_speaker is not None and current_start is not None and current_end is not None:
        drafts.append(_MessageDraft(current_speaker, "\n".join(current_parts).strip(), current_start, current_end))

    return tuple(drafts), warnings


def _iter_lines_with_offsets(text: str, base_offset: int) -> tuple[tuple[int, int, str], ...]:
    lines: list[tuple[int, int, str]] = []
    offset = base_offset
    for line in text.splitlines(keepends=True):
        line_end = offset + len(line)
        lines.append((offset, line_end, line))
        offset = line_end
    if text and not text.endswith(("\n", "\r")):
        return tuple(lines)
    return tuple(lines)


def _line_end(raw_text: str, offset: int) -> int:
    newline_index = raw_text.find("\n", offset)
    return len(raw_text) if newline_index == -1 else newline_index + 1
