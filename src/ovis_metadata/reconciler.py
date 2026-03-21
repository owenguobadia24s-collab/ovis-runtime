# ---
# id: MODULE-GOV-0007
# title: OVIS Metadata Reconciler
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: gov
# repo: ovis-runtime
# path: src/ovis_metadata/reconciler.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-GOV-0007.yaml
# ---
"""Fail-closed reconciliation between scanned metadata and canonical registry state."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from .registry import current_snapshot_hash, load_registry_state, write_registry_state
from .scanner import scan_workspace
from .types import Issue, ReconcileResult


def reconcile_workspace(
    repo_roots: list[Path],
    *,
    blueprint_root: Path,
    migration_phase: str = "M2",
    allow_legacy: bool = False,
) -> ReconcileResult:
    scan_report = scan_workspace(repo_roots, migration_phase=migration_phase, allow_legacy=allow_legacy)
    registry_state = load_registry_state(blueprint_root)
    issues = list(scan_report.issues)

    if not scan_report.complete:
        issues.append(Issue("ERROR", str(blueprint_root), "Scan incomplete; reconciliation aborted."))
        return ReconcileResult([], [], [], str(registry_state.aggregate_path), issues)

    if any(issue.severity == "ERROR" for issue in issues):
        issues.append(Issue("ERROR", str(blueprint_root), "Validation errors present; reconciliation aborted without writes."))
        return ReconcileResult([], [], [], str(registry_state.aggregate_path), issues)

    if current_snapshot_hash(blueprint_root) != registry_state.snapshot_hash:
        issues.append(Issue("ERROR", str(blueprint_root), "Allocator state changed since scan start; reconciliation aborted."))
        return ReconcileResult([], [], [], str(registry_state.aggregate_path), issues)

    allocators = deepcopy(registry_state.allocators)
    entries = deepcopy(registry_state.entries)
    families = allocators.setdefault("families", {})
    added_ids: list[str] = []
    updated_ids: list[str] = []
    removed_ids: list[str] = []

    path_to_id = {f"{entry['repo']}:{entry['path']}": identifier for identifier, entry in entries.items()}
    discovered = {str(item.metadata["id"]): item for item in scan_report.items}

    for identifier, item in discovered.items():
        location_key = f"{item.metadata['repo']}:{item.metadata['path']}"
        conflicting_identifier = path_to_id.get(location_key)
        if conflicting_identifier and conflicting_identifier != identifier:
            issues.append(Issue("ERROR", location_key, f"Path already registered to {conflicting_identifier}; reconciliation aborted."))
            continue

        family_key = _family_key(identifier)
        family_state = families.setdefault(family_key, {"next_number": 1, "retired_ids": []})
        sequence_number = int(identifier.rsplit("-", 1)[1])
        next_number = int(family_state["next_number"])
        if sequence_number > next_number:
            issues.append(Issue("ERROR", location_key, f"Allocator gap detected for {identifier}; reconciliation aborted."))
            continue

        payload = dict(item.metadata)
        existing = entries.get(identifier)
        if existing is None:
            entries[identifier] = payload
            added_ids.append(identifier)
            if sequence_number == next_number:
                family_state["next_number"] = sequence_number + 1
        elif existing != payload:
            entries[identifier] = payload
            updated_ids.append(identifier)

    if any(issue.severity == "ERROR" for issue in issues):
        return ReconcileResult([], [], [], str(registry_state.aggregate_path), issues)

    scanned_repo_names = {root.name for root in repo_roots}
    for identifier in sorted(set(entries) - set(discovered)):
        if entries[identifier].get("repo") in scanned_repo_names:
            removed_ids.append(identifier)
            entries.pop(identifier, None)

    write_registry_state(registry_state, allocators=allocators, entries=entries)
    return ReconcileResult(added_ids, updated_ids, removed_ids, str(registry_state.aggregate_path), issues)


def _family_key(identifier: str) -> str:
    family, sequence = identifier.rsplit("-", 1)
    if not sequence.isdigit():
        raise ValueError(f"Identifier does not end with a numeric sequence: {identifier}")
    return family
