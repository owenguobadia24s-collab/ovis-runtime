"""Serializable chat ingestion record contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
import hashlib
import json
from typing import Any


PARSER_VERSION = "chat-transcript-v0"
CHATGPT_EXPORT_PARSER_VERSION = "chatgpt-export-v0"
IMPORT_MANIFEST_VERSION = "import-manifest-v0"
SOURCE_TYPE_TRANSCRIPT = "transcript"
SOURCE_TYPE_CHATGPT_EXPORT = "chatgpt_export"


@dataclass(frozen=True)
class ChatSource:
    source_id: str
    source_type: str
    path: str
    title: str | None
    created_at: str | None
    imported_at: str | None
    import_status: str
    parser_version: str
    raw_sha256: str
    message_count: int
    segment_count: int


@dataclass(frozen=True)
class ChatMessage:
    message_id: str
    source_id: str
    speaker: str
    text: str
    message_index: int
    timestamp: str | None = None
    raw_start_index: int | None = None
    raw_end_index: int | None = None


@dataclass(frozen=True)
class ChatSegment:
    segment_id: str
    source_id: str
    message_id: str | None
    speaker: str
    text: str
    start_index: int
    end_index: int
    segment_index: int
    timestamp: str | None = None


@dataclass(frozen=True)
class ImportManifest:
    manifest_version: str
    source_id: str
    source_type: str
    raw_path: str
    normalized_source_path: str
    normalized_segment_path: str
    parser_version: str
    import_status: str
    created_at: str | None
    raw_sha256: str
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


def raw_sha256_hexdigest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def short_sha256(value: bytes | str, length: int = 12) -> str:
    if length <= 0:
        raise ValueError("length must be positive")
    raw = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(raw).hexdigest()[:length]


def make_transcript_source_id(raw_sha256: str) -> str:
    return f"SRC-TRANSCRIPT-{raw_sha256[:12]}"


def make_chatgpt_export_source_id(conversation_id: str, raw_sha256: str) -> str:
    return f"SRC-CHATGPT-{short_sha256(f'{conversation_id}:{raw_sha256}')}"


def make_message_id(source_id: str, message_index: int) -> str:
    if message_index < 0:
        raise ValueError("message_index must be non-negative")
    return f"MSG-{source_id}-{message_index:04d}"


def make_segment_id(source_id: str, segment_index: int) -> str:
    if segment_index < 0:
        raise ValueError("segment_index must be non-negative")
    return f"SEG-{source_id}-{segment_index:04d}"


def dataclass_to_dict(record: Any) -> dict[str, Any]:
    if not is_dataclass(record):
        raise TypeError("record must be a dataclass instance")
    return asdict(record)


def record_to_json(record: Any) -> str:
    return json.dumps(dataclass_to_dict(record), ensure_ascii=False, sort_keys=True)


def record_to_jsonl_line(record: Any) -> str:
    return f"{record_to_json(record)}\n"
