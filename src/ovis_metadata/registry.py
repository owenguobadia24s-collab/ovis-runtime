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
"""Registry loading, deterministic candidate rendering, and controlled replacement helpers."""

from __future__ import annotations

from datetime import date, datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any

import yaml

from .types import CandidateArtifact, Issue, RegistryState


def load_registry_state(blueprint_root: Path) -> RegistryState:
    state, issues = read_registry_state(blueprint_root)
    if state is None:
        messages = "; ".join(issue.message for issue in issues) or "unknown registry read failure"
        raise ValueError(messages)
    return state


def read_registry_state(blueprint_root: Path) -> tuple[RegistryState | None, list[Issue]]:
    allocator_path = blueprint_root / "REGISTRIES" / "allocators.yaml"
    entries_dir = blueprint_root / "REGISTRIES" / "entries"
    aggregate_path = blueprint_root / "REGISTRIES" / "OVIS_FILE_REGISTRY.yaml"
    return read_registry_state_from_paths(
        allocator_path=allocator_path,
        entries_dir=entries_dir,
        aggregate_path=aggregate_path,
    )


def read_registry_state_from_paths(
    *,
    allocator_path: Path,
    entries_dir: Path,
    aggregate_path: Path,
) -> tuple[RegistryState | None, list[Issue]]:
    issues: list[Issue] = []

    if not allocator_path.exists():
        issues.append(Issue("ERROR", str(allocator_path), "Allocator working-state file is missing."))
    if not entries_dir.exists():
        issues.append(Issue("ERROR", str(entries_dir), "Registry entries directory is missing."))
    if not aggregate_path.exists():
        issues.append(Issue("ERROR", str(aggregate_path), "Aggregate registry working-state file is missing."))
    if issues:
        return None, issues

    try:
        allocators = yaml.safe_load(allocator_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        return None, [Issue("ERROR", str(allocator_path), f"Malformed allocator working-state YAML: {exc}")]
    if not isinstance(allocators, dict):
        return None, [Issue("ERROR", str(allocator_path), "Allocator working-state payload must decode to a mapping.")]

    entries: dict[str, dict[str, Any]] = {}
    for entry_path in sorted(entries_dir.glob("*.yaml")):
        try:
            entry = yaml.safe_load(entry_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            issues.append(Issue("ERROR", str(entry_path), f"Malformed registry entry YAML: {exc}"))
            continue
        if not isinstance(entry, dict):
            issues.append(Issue("ERROR", str(entry_path), "Registry entry payload must decode to a mapping."))
            continue
        if "id" not in entry:
            issues.append(Issue("ERROR", str(entry_path), "Registry entry payload is missing id."))
            continue
        entries[str(entry["id"])] = entry

    try:
        aggregate = yaml.safe_load(aggregate_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        issues.append(Issue("ERROR", str(aggregate_path), f"Malformed aggregate registry YAML: {exc}"))
        aggregate = {}
    if aggregate and not isinstance(aggregate, dict):
        issues.append(Issue("ERROR", str(aggregate_path), "Aggregate registry payload must decode to a mapping."))

    if issues:
        return None, issues

    return RegistryState(
        allocator_path=allocator_path,
        entries_dir=entries_dir,
        aggregate_path=aggregate_path,
        allocators=allocators,
        entries=entries,
        aggregate=aggregate if isinstance(aggregate, dict) else {},
        snapshot_hash=_hash_registry_payload(allocators, entries),
    ), []


def current_snapshot_hash(blueprint_root: Path) -> str:
    return load_registry_state(blueprint_root).snapshot_hash


def compile_candidate_aggregate(
    allocators: dict[str, Any],
    entries: dict[str, dict[str, Any]],
    *,
    source_refs: dict[str, str],
) -> dict[str, Any]:
    return {
        "registry_version": "0.1",
        "source_refs": {repo: source_refs[repo] for repo in sorted(source_refs)},
        "allocators": allocators.get("families", {}),
        "entries": {identifier: entries[identifier] for identifier in sorted(entries)},
    }


def render_candidate_artifact(payload: dict[str, Any], *, target_path: str) -> CandidateArtifact:
    text = _dump_yaml(payload)
    return CandidateArtifact(path=target_path, sha256=_sha256_text(text), text=text)


def compute_derivation_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def materialize_candidate_registry(
    candidate_artifacts: dict[str, CandidateArtifact],
    *,
    destination_root: Path,
) -> list[Path]:
    written_paths: list[Path] = []
    for artifact in sorted(candidate_artifacts.values(), key=lambda item: item.path):
        target = destination_root / artifact.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(artifact.text, encoding="utf-8")
        written_paths.append(target)
    return written_paths


def validate_materialized_registry(
    *,
    registry_root: Path,
    source_refs: dict[str, str],
) -> list[Issue]:
    allocators_path = registry_root / "REGISTRIES" / "allocators.yaml"
    entries_dir = registry_root / "REGISTRIES" / "entries"
    aggregate_path = registry_root / "REGISTRIES" / "OVIS_FILE_REGISTRY.yaml"
    state, issues = read_registry_state_from_paths(
        allocator_path=allocators_path,
        entries_dir=entries_dir,
        aggregate_path=aggregate_path,
    )
    if state is None:
        return issues

    for identifier, payload in sorted(state.entries.items()):
        expected_path = entries_dir / f"{identifier}.yaml"
        if not expected_path.exists():
            issues.append(Issue("ERROR", str(expected_path), "Candidate registry entry file is missing for its id."))
        if str(payload.get("id", "")) != identifier:
            issues.append(
                Issue(
                    "ERROR",
                    str(expected_path),
                    f"Candidate registry entry file id {payload.get('id')!r} does not match filename {identifier!r}.",
                )
            )

    expected_aggregate = compile_candidate_aggregate(
        state.allocators,
        state.entries,
        source_refs=source_refs,
    )
    if state.aggregate != expected_aggregate:
        issues.append(
            Issue(
                "ERROR",
                str(aggregate_path),
                "Candidate aggregate payload does not match allocator and entry candidates.",
            )
        )
    return issues


def replace_registry_authority(
    *,
    blueprint_root: Path,
    staging_registry_root: Path,
) -> tuple[list[str], bool]:
    registries_root = blueprint_root / "REGISTRIES"
    allocator_path = registries_root / "allocators.yaml"
    entries_dir = registries_root / "entries"
    aggregate_path = registries_root / "OVIS_FILE_REGISTRY.yaml"

    staged_allocator = staging_registry_root / "REGISTRIES" / "allocators.yaml"
    staged_entries = staging_registry_root / "REGISTRIES" / "entries"
    staged_aggregate = staging_registry_root / "REGISTRIES" / "OVIS_FILE_REGISTRY.yaml"

    if not staged_allocator.exists() or not staged_entries.exists() or not staged_aggregate.exists():
        raise ValueError("Staged registry candidates are incomplete; controlled replacement aborted.")

    backup_root = Path(
        tempfile.mkdtemp(
            prefix="ovis-registry-backup-",
            dir=str(blueprint_root.parent),
        )
    )
    rollback_performed = False
    backup_allocator = backup_root / "allocators.yaml"
    backup_entries = backup_root / "entries"
    backup_aggregate = backup_root / "OVIS_FILE_REGISTRY.yaml"

    try:
        os.replace(allocator_path, backup_allocator)
        os.replace(aggregate_path, backup_aggregate)
        entries_dir.rename(backup_entries)

        os.replace(staged_allocator, allocator_path)
        os.replace(staged_aggregate, aggregate_path)
        staged_entries.rename(entries_dir)
    except Exception:
        rollback_performed = True
        _restore_registry_component(allocator_path, backup_allocator)
        _restore_registry_component(aggregate_path, backup_aggregate)
        _restore_registry_directory(entries_dir, backup_entries)
        raise
    finally:
        shutil.rmtree(backup_root, ignore_errors=True)

    return (
        [
            str(allocator_path),
            str(entries_dir),
            str(aggregate_path),
        ],
        rollback_performed,
    )


def _dump_yaml(payload: dict[str, Any]) -> str:
    return yaml.safe_dump(_normalize_for_yaml(payload), sort_keys=False, allow_unicode=False)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _normalize_for_yaml(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _normalize_for_yaml(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_for_yaml(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _hash_registry_payload(allocators: dict[str, Any], entries: dict[str, dict[str, Any]]) -> str:
    encoded = json.dumps(
        {"allocators": allocators, "entries": entries},
        sort_keys=True,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _restore_registry_component(destination: Path, backup: Path) -> None:
    if destination.exists():
        destination.unlink()
    if backup.exists():
        os.replace(backup, destination)


def _restore_registry_directory(destination: Path, backup: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    if backup.exists():
        backup.rename(destination)
