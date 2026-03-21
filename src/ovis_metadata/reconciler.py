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
"""Read-only reconciliation between canonical artifact metadata and held registry working state."""

from __future__ import annotations

from pathlib import Path

from .derive import derive_registry_state
from .drift import detect_registry_drift
from .registry import (
    compile_candidate_aggregate,
    compute_derivation_hash,
    read_registry_state,
    render_candidate_artifact,
)
from .scanner import scan_workspace
from .types import DriftReport, Issue, ReconciliationReport


def reconcile_workspace(
    repo_roots: list[Path],
    *,
    blueprint_root: Path,
    exclusion_manifest: Path,
    source_ref: str = "HEAD",
    include_candidates: str = "summary",
    migration_phase: str = "M2",
    allow_legacy: bool = False,
) -> ReconciliationReport:
    scan_report = scan_workspace(
        repo_roots,
        migration_phase=migration_phase,
        allow_legacy=allow_legacy,
        source_ref=source_ref,
        exclusion_manifest=exclusion_manifest,
    )
    current_state, registry_issues = read_registry_state(blueprint_root)

    artifact_issues = list(scan_report.issues)
    artifact_issues.extend(registry_issues)

    scope_summary = {
        "included_count": len(scan_report.items),
        "scanned_count": len(scan_report.scanned_files),
        "excluded_count": len(scan_report.excluded_files),
        "excluded_by_reason": _count_excluded(scan_report.excluded_files),
    }

    if not scan_report.complete:
        artifact_issues.append(Issue("ERROR", str(blueprint_root), "Scan incomplete; reconciliation aborted."))
        return _error_report(scan_report.source_refs, scope_summary, artifact_issues)

    if current_state is None:
        artifact_issues.append(Issue("ERROR", str(blueprint_root), "Current registry working state could not be loaded."))
        return _error_report(scan_report.source_refs, scope_summary, artifact_issues)

    if any(issue.severity == "ERROR" for issue in artifact_issues):
        artifact_issues.append(
            Issue("ERROR", str(blueprint_root), "Artifact or registry input errors present; dry-run reconciliation aborted.")
        )
        return _error_report(scan_report.source_refs, scope_summary, artifact_issues)

    derived_state, derivation_issues = derive_registry_state(
        scan_report.items,
        current_allocators=current_state.allocators,
        build_candidate_artifact=render_candidate_artifact,
        build_aggregate_payload=lambda allocators, entries: compile_candidate_aggregate(
            allocators,
            entries,
            source_refs=scan_report.source_refs,
        ),
        compute_hash=compute_derivation_hash,
    )
    artifact_issues.extend(derivation_issues)
    if derived_state is None:
        artifact_issues.append(Issue("ERROR", str(blueprint_root), "Registry derivation failed before drift detection."))
        return _error_report(scan_report.source_refs, scope_summary, artifact_issues)

    aggregate_candidate = compile_candidate_aggregate(
        derived_state.allocators,
        derived_state.entries,
        source_refs=scan_report.source_refs,
    )
    derived_state.aggregate = aggregate_candidate
    derived_state.candidate_artifacts["aggregate"] = render_candidate_artifact(
        aggregate_candidate,
        target_path="REGISTRIES/OVIS_FILE_REGISTRY.yaml",
    )
    derived_state.derivation_hash = compute_derivation_hash(
        {key: artifact.text for key, artifact in derived_state.candidate_artifacts.items()}
    )

    determinism_issues = _ensure_deterministic_render(derived_state)
    artifact_issues.extend(determinism_issues)
    if any(issue.severity == "ERROR" for issue in artifact_issues):
        artifact_issues.append(Issue("ERROR", str(blueprint_root), "Determinism checks failed; reconciliation aborted."))
        return _error_report(scan_report.source_refs, scope_summary, artifact_issues)

    drift = detect_registry_drift(
        current_state,
        derived_state,
        aggregate_renderer=lambda allocators, entries: compile_candidate_aggregate(
            allocators,
            entries,
            source_refs=scan_report.source_refs,
        ),
    )
    return ReconciliationReport(
        source_refs=scan_report.source_refs,
        scope_summary=scope_summary,
        artifact_issues=artifact_issues,
        derived=derived_state,
        drift=drift,
    )


def _ensure_deterministic_render(derived_state) -> list[Issue]:
    issues: list[Issue] = []
    rerendered = {
        "allocators": render_candidate_artifact(
            derived_state.allocators,
            target_path="REGISTRIES/allocators.yaml",
        ),
        "aggregate": render_candidate_artifact(
            derived_state.aggregate,
            target_path="REGISTRIES/OVIS_FILE_REGISTRY.yaml",
        ),
    }
    for identifier, payload in sorted(derived_state.entries.items()):
        rerendered[f"entry:{identifier}"] = render_candidate_artifact(
            payload,
            target_path=f"REGISTRIES/entries/{identifier}.yaml",
        )
    first = {key: artifact.sha256 for key, artifact in derived_state.candidate_artifacts.items()}
    second = {key: artifact.sha256 for key, artifact in rerendered.items()}
    if first != second:
        issues.append(Issue("ERROR", "reconcile", "Candidate rendering is not deterministic across repeated checks."))
    return issues


def _count_excluded(excluded_files) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in excluded_files:
        counts[item.reason] = counts.get(item.reason, 0) + 1
    return counts


def _error_report(source_refs: dict[str, str], scope_summary: dict[str, int], issues: list[Issue]) -> ReconciliationReport:
    empty_drift = DriftReport(findings=[])
    empty_derived = derive_registry_state(
        [],
        current_allocators={"families": {}},
        build_candidate_artifact=render_candidate_artifact,
        build_aggregate_payload=lambda allocators, entries: compile_candidate_aggregate(
            allocators,
            entries,
            source_refs=source_refs,
        ),
        compute_hash=compute_derivation_hash,
    )[0]
    assert empty_derived is not None
    return ReconciliationReport(
        source_refs=source_refs,
        scope_summary=scope_summary,
        artifact_issues=issues,
        derived=empty_derived,
        drift=empty_drift,
    )
