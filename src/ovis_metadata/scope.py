# ---
# id: MODULE-GOV-0009
# title: OVIS Metadata Normalization Scope
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: gov
# repo: ovis-runtime
# path: src/ovis_metadata/scope.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-GOV-0009.yaml
# ---
"""Governance-owned scope and exclusion loading for normalization."""

from __future__ import annotations

from pathlib import Path

import yaml

from .types import Issue, NormalizationScope


def load_normalization_scope(manifest_path: Path) -> tuple[NormalizationScope | None, list[Issue]]:
    if not manifest_path.exists():
        return None, [Issue("ERROR", str(manifest_path), "Normalization exclusion manifest not found.")]

    try:
        payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        return None, [Issue("ERROR", str(manifest_path), f"Invalid normalization exclusion manifest YAML: {exc}")]

    if not isinstance(payload, dict):
        return None, [Issue("ERROR", str(manifest_path), "Normalization exclusion manifest must decode to a mapping.")]

    raw_items = payload.get("intentionally_unplaced", [])
    if not isinstance(raw_items, list):
        return None, [Issue("ERROR", str(manifest_path), "intentionally_unplaced must be a list of repo/path mappings.")]

    exclusions: dict[str, str] = {}
    issues: list[Issue] = []
    for index, raw_item in enumerate(raw_items):
        location = f"{manifest_path}:{index + 1}"
        if not isinstance(raw_item, dict):
            issues.append(Issue("ERROR", location, "Each intentionally_unplaced item must be a mapping."))
            continue
        repo = str(raw_item.get("repo", "")).strip()
        relative_path = str(raw_item.get("path", "")).strip().replace("\\", "/")
        reason = str(raw_item.get("reason", "")).strip() or "intentionally_unplaced"
        if not repo or not relative_path:
            issues.append(Issue("ERROR", location, "Each intentionally_unplaced item must include repo and path."))
            continue
        key = f"{repo}:{relative_path}"
        if key in exclusions:
            issues.append(Issue("ERROR", location, f"Duplicate normalization exclusion entry: {key}"))
            continue
        exclusions[key] = reason

    if issues:
        return None, issues

    return NormalizationScope(manifest_path=str(manifest_path), intentionally_unplaced=exclusions), []
