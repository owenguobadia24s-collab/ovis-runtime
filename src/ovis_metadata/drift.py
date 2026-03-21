# ---
# id: MODULE-GOV-0011
# title: OVIS Metadata Registry Drift Detection
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: gov
# repo: ovis-runtime
# path: src/ovis_metadata/drift.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-GOV-0011.yaml
# ---
"""Compare derived registry candidates to current held registry working state."""

from __future__ import annotations

from typing import Any

from .types import DerivedRegistryState, DriftFinding, DriftReport, RegistryState


def detect_registry_drift(
    current_state: RegistryState,
    derived_state: DerivedRegistryState,
    *,
    aggregate_renderer,
) -> DriftReport:
    findings: list[DriftFinding] = []
    current_entries = current_state.entries
    derived_entries = derived_state.entries

    for identifier, payload in sorted(derived_entries.items()):
        current_payload = current_entries.get(identifier)
        if current_payload is None:
            findings.append(
                DriftFinding(
                    category="missing_entry",
                    severity="WARN",
                    path=identifier,
                    message="Entry is present in derived state but missing from current registry working state.",
                )
            )
            continue
        if current_payload != payload:
            findings.append(
                DriftFinding(
                    category="payload_mismatch",
                    severity="WARN",
                    path=identifier,
                    message="Entry payload differs between derived state and current registry working state.",
                )
            )

    for identifier in sorted(set(current_entries) - set(derived_entries)):
        findings.append(
            DriftFinding(
                category="stale_entry",
                severity="WARN",
                path=identifier,
                message="Entry exists in current registry working state but not in derived state.",
            )
        )

    _detect_allocator_drift(current_state.allocators, derived_state.allocators, findings)
    _detect_entry_path_collisions(current_entries, findings)

    current_aggregate = aggregate_renderer(current_state.allocators, current_state.entries)
    if current_aggregate != derived_state.aggregate:
        findings.append(
            DriftFinding(
                category="aggregate_mismatch",
                severity="WARN",
                path="REGISTRIES/OVIS_FILE_REGISTRY.yaml",
                message="Aggregate registry payload differs between derived state and current registry working state.",
            )
        )

    return DriftReport(findings=findings)


def _detect_allocator_drift(
    current_allocators: dict[str, Any],
    derived_allocators: dict[str, Any],
    findings: list[DriftFinding],
) -> None:
    current_families = current_allocators.get("families", {}) if isinstance(current_allocators, dict) else {}
    derived_families = derived_allocators.get("families", {}) if isinstance(derived_allocators, dict) else {}

    for family in sorted(derived_families):
        current_family = current_families.get(family)
        if current_family is None:
            findings.append(
                DriftFinding(
                    category="allocator_family_missing",
                    severity="WARN",
                    path=family,
                    message="Allocator family is present in derived state but missing from current working state.",
                )
            )
            continue
        if current_family.get("next_number") != derived_families[family].get("next_number"):
            findings.append(
                DriftFinding(
                    category="allocator_next_number_mismatch",
                    severity="WARN",
                    path=family,
                    message="Allocator next_number differs between derived state and current working state.",
                )
            )
        retired_ids = current_family.get("retired_ids", [])
        if retired_ids not in (None, []):
            findings.append(
                DriftFinding(
                    category="unverified_retired_ids",
                    severity="ERROR",
                    path=family,
                    message="Current allocator retired_ids are non-empty and cannot be verified from artifact metadata.",
                )
            )

    for family in sorted(set(current_families) - set(derived_families)):
        findings.append(
            DriftFinding(
                category="allocator_family_unexpected",
                severity="WARN",
                path=family,
                message="Allocator family exists in current working state but is absent from derived state.",
            )
        )


def _detect_entry_path_collisions(
    current_entries: dict[str, dict[str, Any]],
    findings: list[DriftFinding],
) -> None:
    seen: dict[str, str] = {}
    for identifier, payload in sorted(current_entries.items()):
        repo = str(payload.get("repo", ""))
        relative_path = str(payload.get("path", ""))
        location = f"{repo}:{relative_path}"
        previous = seen.get(location)
        if previous is not None and previous != identifier:
            findings.append(
                DriftFinding(
                    category="path_id_collision",
                    severity="ERROR",
                    path=location,
                    message=f"Current registry working state maps the same repo/path to both {previous} and {identifier}.",
                )
            )
        else:
            seen[location] = identifier
