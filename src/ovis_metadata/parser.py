# ---
# id: MODULE-GOV-0003
# title: OVIS Metadata Parser
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: gov
# repo: ovis-runtime
# path: src/ovis_metadata/parser.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-GOV-0003.yaml
# ---
"""Metadata parsing for markdown, code headers, raw YAML, and sidecars."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .types import Issue, ParsedMetadata

COMMENT_PREFIXES = {
    ".py": "#",
    ".ps1": "#",
    ".sh": "#",
    ".js": "//",
    ".jsx": "//",
    ".ts": "//",
    ".tsx": "//",
}

LEGACY_FIELD_MAP = {
    "ov_id": "id",
    "ov_type": "type",
    "schema_version": "version",
}


def parse_metadata_file(path: Path, repo_root: Path) -> tuple[ParsedMetadata | None, list[Issue]]:
    suffix = path.suffix.lower()

    if suffix in {".md", ".markdown"}:
        return _parse_markdown(path, repo_root)

    if suffix in COMMENT_PREFIXES:
        parsed, issues = _parse_commented(path, repo_root, COMMENT_PREFIXES[suffix])
        if parsed is not None or issues:
            return parsed, issues

    if suffix in {".yaml", ".yml"}:
        parsed, issues = _parse_raw_yaml(path, repo_root)
        if parsed is not None or issues:
            return parsed, issues

    return _parse_sidecar(path, repo_root)


def _parse_markdown(path: Path, repo_root: Path) -> tuple[ParsedMetadata | None, list[Issue]]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return _parse_sidecar(path, repo_root)

    try:
        end_index = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration:
        return None, [Issue("ERROR", str(path), "Unterminated markdown frontmatter.")]

    raw_yaml = "\n".join(lines[1:end_index])
    try:
        data = yaml.safe_load(raw_yaml) or {}
    except yaml.YAMLError as exc:
        return None, [Issue("ERROR", str(path), f"Invalid markdown frontmatter YAML: {exc}")]

    if not isinstance(data, dict):
        return None, [Issue("ERROR", str(path), "Frontmatter must decode to a mapping.")]

    metadata, format_kind = _normalize_metadata(data)
    parsed = ParsedMetadata(
        path=path,
        repo_root=repo_root,
        relative_path=path.relative_to(repo_root).as_posix(),
        metadata=metadata,
        source_kind="frontmatter",
        format_kind=format_kind,
        body_text="\n".join(lines[end_index + 1 :]).lstrip("\n"),
        warnings=_format_warnings(path, format_kind),
    )
    return parsed, []


def _parse_commented(path: Path, repo_root: Path, comment_prefix: str) -> tuple[ParsedMetadata | None, list[Issue]]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    index = 0
    if lines and lines[0].startswith("#!"):
        index = 1
    while index < len(lines) and not lines[index].strip():
        index += 1

    expected = f"{comment_prefix} ---"
    if index >= len(lines) or lines[index].strip() != expected:
        return _parse_sidecar(path, repo_root)

    yaml_lines: list[str] = []
    index += 1
    while index < len(lines):
        if lines[index].strip() == expected:
            break
        prefixed = f"{comment_prefix} "
        if lines[index].startswith(prefixed):
            yaml_lines.append(lines[index][len(prefixed) :])
        elif lines[index].startswith(comment_prefix):
            yaml_lines.append(lines[index][len(comment_prefix) :].lstrip())
        else:
            return None, [Issue("ERROR", str(path), "Commented metadata header is malformed.")]
        index += 1

    if index >= len(lines):
        return None, [Issue("ERROR", str(path), "Unterminated commented metadata header.")]

    try:
        data = yaml.safe_load("\n".join(yaml_lines)) or {}
    except yaml.YAMLError as exc:
        return None, [Issue("ERROR", str(path), f"Invalid commented metadata YAML: {exc}")]

    if not isinstance(data, dict):
        return None, [Issue("ERROR", str(path), "Commented metadata must decode to a mapping.")]

    metadata, format_kind = _normalize_metadata(data)
    parsed = ParsedMetadata(
        path=path,
        repo_root=repo_root,
        relative_path=path.relative_to(repo_root).as_posix(),
        metadata=metadata,
        source_kind="commented_header",
        format_kind=format_kind,
        warnings=_format_warnings(path, format_kind),
    )
    return parsed, []


def _parse_raw_yaml(path: Path, repo_root: Path) -> tuple[ParsedMetadata | None, list[Issue]]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        return None, [Issue("ERROR", str(path), f"Invalid YAML file: {exc}")]

    if not isinstance(data, dict):
        return None, []
    if "id" not in data and "OVIS" not in data and "ov_id" not in data:
        return None, []

    metadata, format_kind = _normalize_metadata(data)
    parsed = ParsedMetadata(
        path=path,
        repo_root=repo_root,
        relative_path=path.relative_to(repo_root).as_posix(),
        metadata=metadata,
        source_kind="raw_yaml",
        format_kind=format_kind,
        warnings=_format_warnings(path, format_kind),
    )
    return parsed, []


def _parse_sidecar(path: Path, repo_root: Path) -> tuple[ParsedMetadata | None, list[Issue]]:
    sidecar = _find_sidecar(path)
    if sidecar is None:
        return None, []

    try:
        data = yaml.safe_load(sidecar.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        return None, [Issue("ERROR", str(sidecar), f"Invalid sidecar YAML: {exc}")]

    if not isinstance(data, dict):
        return None, [Issue("ERROR", str(sidecar), "Sidecar metadata must decode to a mapping.")]

    metadata, format_kind = _normalize_metadata(data)
    parsed = ParsedMetadata(
        path=path,
        repo_root=repo_root,
        relative_path=path.relative_to(repo_root).as_posix(),
        metadata=metadata,
        source_kind="sidecar",
        format_kind=format_kind,
        warnings=_format_warnings(sidecar, format_kind),
    )
    return parsed, []


def _find_sidecar(path: Path) -> Path | None:
    candidates = [
        path.with_name(path.name + ".ovis.yaml"),
        path.with_name(path.stem + ".ovis.yaml"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _normalize_metadata(data: dict[str, Any]) -> tuple[dict[str, Any], str]:
    if "OVIS" in data and isinstance(data["OVIS"], dict):
        return {str(key): value for key, value in data["OVIS"].items()}, "wrapped"

    if any(key.startswith("ov_") for key in data):
        mapped: dict[str, Any] = {}
        for key, value in data.items():
            mapped[LEGACY_FIELD_MAP.get(str(key), str(key))] = value
        if "authority" not in mapped:
            mapped["authority"] = "derived"
        return mapped, "legacy_flat"

    return {str(key): value for key, value in data.items()}, "canonical"


def _format_warnings(path: Path, format_kind: str) -> list[Issue]:
    if format_kind == "canonical":
        return []
    return [Issue("WARN", str(path), f"Non-canonical metadata format detected: {format_kind}")]