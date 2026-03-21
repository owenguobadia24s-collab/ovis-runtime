# ---
# id: MODULE-GOV-0006
# title: OVIS Metadata Registry IO
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: gov
# repo: ovis-runtime
# path: src/ovis_metadata/registry.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-GOV-0006.yaml
# ---
"""Canonical registry loading, writing, and aggregate compilation."""

from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from .types import RegistryState


def load_registry_state(blueprint_root: Path) -> RegistryState:
    allocator_path = blueprint_root / "REGISTRIES" / "allocators.yaml"
    entries_dir = blueprint_root / "REGISTRIES" / "entries"
    aggregate_path = blueprint_root / "REGISTRIES" / "OVIS_FILE_REGISTRY.yaml"

    allocators = yaml.safe_load(allocator_path.read_text(encoding="utf-8")) or {}
    entries: dict[str, dict[str, Any]] = {}
    if entries_dir.exists():
        for entry_path in sorted(entries_dir.glob("*.yaml")):
            entry = yaml.safe_load(entry_path.read_text(encoding="utf-8")) or {}
            if isinstance(entry, dict) and "id" in entry:
                entries[str(entry["id"])] = entry

    return RegistryState(
        allocator_path=allocator_path,
        entries_dir=entries_dir,
        aggregate_path=aggregate_path,
        allocators=allocators,
        entries=entries,
        snapshot_hash=_hash_registry_payload(allocators, entries),
    )


def current_snapshot_hash(blueprint_root: Path) -> str:
    return load_registry_state(blueprint_root).snapshot_hash


def write_registry_state(
    state: RegistryState,
    *,
    allocators: dict[str, Any],
    entries: dict[str, dict[str, Any]],
) -> None:
    state.entries_dir.mkdir(parents=True, exist_ok=True)
    state.allocator_path.parent.mkdir(parents=True, exist_ok=True)
    state.allocator_path.write_text(_dump_yaml(allocators), encoding="utf-8")

    stale = {path.stem: path for path in state.entries_dir.glob("*.yaml")}
    for identifier, entry in entries.items():
        target = state.entries_dir / f"{identifier}.yaml"
        target.write_text(_dump_yaml(entry), encoding="utf-8")
        stale.pop(identifier, None)

    for path in stale.values():
        path.unlink()

    aggregate = compile_aggregate(allocators, entries)
    state.aggregate_path.write_text(_dump_yaml(aggregate), encoding="utf-8")


def compile_aggregate(allocators: dict[str, Any], entries: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "generated_at": date.today().isoformat(),
        "registry_version": "0.1",
        "allocators": allocators.get("families", {}),
        "entries": {identifier: entries[identifier] for identifier in sorted(entries)},
    }


def _dump_yaml(payload: dict[str, Any]) -> str:
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=False)


def _hash_registry_payload(allocators: dict[str, Any], entries: dict[str, dict[str, Any]]) -> str:
    encoded = json.dumps(
        {"allocators": allocators, "entries": entries},
        sort_keys=True,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()