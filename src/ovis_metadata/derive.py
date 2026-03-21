# ---
# id: MODULE-GOV-0010
# title: OVIS Metadata Registry Derivation
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: gov
# repo: ovis-runtime
# path: src/ovis_metadata/derive.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-GOV-0010.yaml
# ---
"""In-memory derivation of registry candidates from canonical artifact metadata."""

from __future__ import annotations

from collections import OrderedDict
from typing import Any

from .types import DerivedRegistryState, Issue, ParsedMetadata

ENTRY_FIELD_ORDER = (
    "id",
    "title",
    "type",
    "status",
    "authority",
    "version",
    "layer",
    "domain",
    "repo",
    "path",
    "owner",
    "created",
    "last_updated",
    "registry",
    "module_id",
    "module_slug",
    "system_id",
    "system_slug",
    "related_module_ids",
)


def derive_registry_state(
    items: list[ParsedMetadata],
    *,
    current_allocators: dict[str, Any],
    build_candidate_artifact,
    build_aggregate_payload,
    compute_hash,
) -> tuple[DerivedRegistryState | None, list[Issue]]:
    issues: list[Issue] = []
    entries: dict[str, dict[str, Any]] = {}
    sequence_max_by_family: dict[str, int] = {}

    for item in sorted(items, key=lambda candidate: str(candidate.metadata["id"])):
        identifier = str(item.metadata["id"])
        entries[identifier] = _entry_payload(item.metadata)
        family = _family_key(identifier)
        sequence_max_by_family[family] = max(sequence_max_by_family.get(family, 0), _sequence(identifier))

    current_families = current_allocators.get("families", {}) if isinstance(current_allocators, dict) else {}
    for family, current_family in sorted(current_families.items()):
        retired_ids = current_family.get("retired_ids", [])
        if retired_ids not in (None, []):
            issues.append(
                Issue(
                    "ERROR",
                    family,
                    "retired_ids cannot be verified from artifact metadata and require manual review.",
                )
            )

    families: OrderedDict[str, dict[str, Any]] = OrderedDict()
    for family in sorted(sequence_max_by_family):
        families[family] = {
            "next_number": sequence_max_by_family[family] + 1,
            "retired_ids": [],
        }

    if issues:
        return None, issues

    allocator_payload = OrderedDict()
    for key, value in current_allocators.items():
        if key == "families":
            continue
        allocator_payload[key] = value
    allocator_payload["families"] = families

    aggregate_payload = build_aggregate_payload(allocator_payload, entries)
    candidate_artifacts = {}
    candidate_artifacts["allocators"] = build_candidate_artifact(
        allocator_payload,
        target_path="REGISTRIES/allocators.yaml",
    )
    for identifier, payload in sorted(entries.items()):
        candidate_artifacts[f"entry:{identifier}"] = build_candidate_artifact(payload, target_path=f"REGISTRIES/entries/{identifier}.yaml")
    candidate_artifacts["aggregate"] = build_candidate_artifact(
        aggregate_payload,
        target_path="REGISTRIES/OVIS_FILE_REGISTRY.yaml",
    )

    derivation_hash = compute_hash({key: artifact.text for key, artifact in candidate_artifacts.items()})
    return (
        DerivedRegistryState(
            allocators=allocator_payload,
            entries=entries,
            aggregate=aggregate_payload,
            candidate_artifacts=candidate_artifacts,
            derivation_hash=derivation_hash,
        ),
        [],
    )


def _entry_payload(metadata: dict[str, Any]) -> dict[str, Any]:
    payload: OrderedDict[str, Any] = OrderedDict()
    for field in ENTRY_FIELD_ORDER:
        if field not in metadata:
            continue
        value = metadata[field]
        if value in (None, "", []):
            continue
        payload[field] = value
    return payload


def _family_key(identifier: str) -> str:
    family, sequence = identifier.rsplit("-", 1)
    if not sequence.isdigit():
        raise ValueError(f"Identifier does not end with a numeric sequence: {identifier}")
    return family


def _sequence(identifier: str) -> int:
    return int(identifier.rsplit("-", 1)[1])
