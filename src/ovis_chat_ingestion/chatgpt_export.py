"""Structural parser for official-style ChatGPT export JSON."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .types import (
    CHATGPT_EXPORT_PARSER_VERSION,
    IMPORT_MANIFEST_VERSION,
    SOURCE_TYPE_CHATGPT_EXPORT,
    ChatMessage,
    ChatSegment,
    ChatSource,
    ImportManifest,
    make_chatgpt_export_source_id,
    make_message_id,
    make_segment_id,
    raw_sha256_hexdigest,
)


@dataclass(frozen=True)
class ParsedChatGPTExport:
    sources: tuple[ChatSource, ...]
    messages: tuple[ChatMessage, ...]
    segments: tuple[ChatSegment, ...]
    manifests: tuple[ImportManifest, ...]
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


def parse_chatgpt_export_file(path: str | Path) -> ParsedChatGPTExport:
    source_path = Path(path)
    return parse_chatgpt_export_text(source_path.read_text(encoding="utf-8"), source_path=str(source_path))


def parse_chatgpt_export_text(raw_text: str, *, source_path: str = "<memory>") -> ParsedChatGPTExport:
    raw_sha256 = raw_sha256_hexdigest(raw_text.encode("utf-8"))
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        return ParsedChatGPTExport(
            sources=(),
            messages=(),
            segments=(),
            manifests=(),
            errors=(f"invalid JSON at line {exc.lineno}, column {exc.colno}",),
        )

    if not isinstance(payload, list):
        return ParsedChatGPTExport(
            sources=(),
            messages=(),
            segments=(),
            manifests=(),
            errors=("expected top-level JSON array of conversations",),
        )

    return parse_chatgpt_export_conversations(payload, raw_sha256=raw_sha256, source_path=source_path)


def parse_chatgpt_export_conversations(
    conversations: list[Any],
    *,
    raw_sha256: str,
    source_path: str = "<memory>",
) -> ParsedChatGPTExport:
    sources: list[ChatSource] = []
    messages: list[ChatMessage] = []
    segments: list[ChatSegment] = []
    manifests: list[ImportManifest] = []
    export_warnings: list[str] = []
    export_errors: list[str] = []

    for conversation_index, conversation in enumerate(conversations):
        if not isinstance(conversation, dict):
            export_warnings.append(f"conversation {conversation_index} is not an object; skipped")
            continue

        parsed = _parse_conversation(conversation, conversation_index, raw_sha256=raw_sha256, source_path=source_path)
        sources.append(parsed.sources[0])
        messages.extend(parsed.messages)
        segments.extend(parsed.segments)
        manifests.extend(parsed.manifests)
        export_warnings.extend(parsed.warnings)
        export_errors.extend(parsed.errors)

    return ParsedChatGPTExport(
        sources=tuple(sources),
        messages=tuple(messages),
        segments=tuple(segments),
        manifests=tuple(manifests),
        warnings=tuple(export_warnings),
        errors=tuple(export_errors),
    )


def _parse_conversation(
    conversation: dict[str, Any],
    conversation_index: int,
    *,
    raw_sha256: str,
    source_path: str,
) -> ParsedChatGPTExport:
    warnings: list[str] = []
    errors: list[str] = []
    conversation_id = _string_or_none(conversation.get("id") or conversation.get("conversation_id"))
    if conversation_id is None:
        conversation_id = f"conversation-{conversation_index:04d}"
        warnings.append("conversation missing id; used positional fallback identity")

    source_id = make_chatgpt_export_source_id(conversation_id, raw_sha256)
    source_path_with_anchor = f"{source_path}#{conversation_id}"
    mapping = conversation.get("mapping")
    if not isinstance(mapping, dict):
        mapping = {}
        errors.append("conversation mapping missing or not an object")

    node_ids = _ordered_node_ids(mapping, conversation.get("current_node"), warnings)
    drafts = tuple(_message_drafts(mapping, node_ids, warnings))

    if not drafts:
        errors.append("no supported text messages found in conversation mapping")

    conversation_messages = tuple(
        ChatMessage(
            message_id=make_message_id(source_id, message_index),
            source_id=source_id,
            speaker=draft["speaker"],
            text=draft["text"],
            message_index=message_index,
            timestamp=draft["timestamp"],
        )
        for message_index, draft in enumerate(drafts)
    )
    conversation_segments = tuple(
        ChatSegment(
            segment_id=make_segment_id(source_id, segment_index),
            source_id=source_id,
            message_id=message.message_id,
            speaker=message.speaker,
            text=message.text,
            start_index=0,
            end_index=len(message.text),
            segment_index=segment_index,
            timestamp=message.timestamp,
        )
        for segment_index, message in enumerate(conversation_messages)
    )
    import_status = "imported" if not errors else "error"

    source = ChatSource(
        source_id=source_id,
        source_type=SOURCE_TYPE_CHATGPT_EXPORT,
        path=source_path_with_anchor,
        title=_string_or_none(conversation.get("title")),
        created_at=_timestamp_to_string(conversation.get("create_time")),
        imported_at=None,
        import_status=import_status,
        parser_version=CHATGPT_EXPORT_PARSER_VERSION,
        raw_sha256=raw_sha256,
        message_count=len(conversation_messages),
        segment_count=len(conversation_segments),
    )
    manifest = ImportManifest(
        manifest_version=IMPORT_MANIFEST_VERSION,
        source_id=source_id,
        source_type=SOURCE_TYPE_CHATGPT_EXPORT,
        raw_path=source_path,
        normalized_source_path=f"data/ovis-first-surface/chat-sources/{source_id}.json",
        normalized_segment_path=f"data/ovis-first-surface/chat-segments/{source_id}.jsonl",
        parser_version=CHATGPT_EXPORT_PARSER_VERSION,
        import_status=import_status,
        created_at=_timestamp_to_string(conversation.get("update_time")),
        raw_sha256=raw_sha256,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )
    return ParsedChatGPTExport(
        sources=(source,),
        messages=conversation_messages,
        segments=conversation_segments,
        manifests=(manifest,),
        warnings=tuple(warnings),
        errors=tuple(errors),
    )


def _ordered_node_ids(mapping: dict[str, Any], current_node: Any, warnings: list[str]) -> tuple[str, ...]:
    current_node_id = _string_or_none(current_node)
    if current_node_id:
        active_path = _active_path_node_ids(mapping, current_node_id)
        if active_path:
            message_node_count = sum(1 for node in mapping.values() if isinstance(node, dict) and node.get("message"))
            if message_node_count > len(active_path):
                warnings.append("non-current conversation branches are not emitted by chatgpt-export-v0")
            return active_path
        warnings.append("current_node did not resolve to a complete path; used mapping order")

    ordered_ids: list[str] = []
    for node_id, node in mapping.items():
        if isinstance(node_id, str) and isinstance(node, dict):
            ordered_ids.append(node_id)
    return tuple(ordered_ids)


def _active_path_node_ids(mapping: dict[str, Any], current_node_id: str) -> tuple[str, ...]:
    path: list[str] = []
    seen: set[str] = set()
    node_id: str | None = current_node_id

    while node_id and node_id not in seen:
        seen.add(node_id)
        node = mapping.get(node_id)
        if not isinstance(node, dict):
            return ()
        path.append(node_id)
        parent = node.get("parent")
        node_id = parent if isinstance(parent, str) else None

    path.reverse()
    return tuple(path)


def _message_drafts(
    mapping: dict[str, Any],
    node_ids: tuple[str, ...],
    warnings: list[str],
) -> tuple[dict[str, str | None], ...]:
    drafts: list[dict[str, str | None]] = []
    for node_id in node_ids:
        node = mapping.get(node_id)
        if not isinstance(node, dict):
            warnings.append(f"node {node_id} is not an object; skipped")
            continue
        message = node.get("message")
        if not isinstance(message, dict):
            continue

        author = message.get("author")
        speaker = None
        if isinstance(author, dict):
            speaker = _string_or_none(author.get("role")) or _string_or_none(author.get("name"))
        if speaker is None:
            warnings.append(f"node {node_id} message missing author role/name; skipped")
            continue

        content = message.get("content")
        if not isinstance(content, dict):
            warnings.append(f"node {node_id} message content missing or not an object; skipped")
            continue
        content_type = _string_or_none(content.get("content_type"))
        parts = content.get("parts")
        text = _parts_to_text(parts)
        if content_type != "text" and text:
            warnings.append(f"node {node_id} content_type {content_type!r} parsed from text parts")
        if not text:
            continue

        drafts.append(
            {
                "speaker": speaker,
                "text": text,
                "timestamp": _timestamp_to_string(message.get("create_time") or message.get("update_time")),
            }
        )

    return tuple(drafts)


def _parts_to_text(parts: Any) -> str:
    if not isinstance(parts, list):
        return ""
    text_parts = [part for part in parts if isinstance(part, str)]
    return "\n".join(text_parts).strip()


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _timestamp_to_string(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)
