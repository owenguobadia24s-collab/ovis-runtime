# ---
# id: MODULE-GOV-0012
# title: OVIS Metadata Normalizer
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: gov
# repo: ovis-runtime
# path: src/ovis_metadata/normalizer.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-GOV-0012.yaml
# ---
"""Controlled registry normalization from a pinned source snapshot."""

from __future__ import annotations

from collections import Counter
import tempfile
from pathlib import Path
from typing import Iterable

from .reconciler import reconcile_workspace
from .registry import (
    materialize_candidate_registry,
    replace_registry_authority,
    validate_materialized_registry,
)
from .source import GitRefSource
from .types import Issue, LegacyRegistryRetirementVerdict, NormalizationReport, ReconciliationReport

ALLOWED_PREWRITE_DRIFT = frozenset(
    {
        "payload_mismatch",
        "stale_entry",
        "allocator_family_unexpected",
        "aggregate_mismatch",
    }
)
EXPECTED_STALE_ENTRY_IDS = frozenset(
    {
        "CJ-SYS-0001",
        "CONFIG-RUN-0001",
        "DOC-ARC-0001",
        "DOC-RUN-0001",
        "DOC-RUN-0002",
        "DOC-SYS-0001",
        "REGISTRY-GOV-0001",
    }
)
WORKFLOW_PARENT_ENTRY_IDS = ("MANIFEST-GOV-0001", "MANIFEST-GOV-0002", "MANIFEST-GOV-0003")
WORKFLOW_PARENT_RELATIVE_PATH = ".github/workflows/ovis-metadata.yml"


def normalize_workspace(
    repo_roots: list[Path],
    *,
    blueprint_root: Path,
    exclusion_manifest: Path,
    source_ref: str = "HEAD",
    migration_phase: str = "M2",
    allow_legacy: bool = False,
) -> NormalizationReport:
    pre_write = reconcile_workspace(
        repo_roots,
        blueprint_root=blueprint_root,
        exclusion_manifest=exclusion_manifest,
        source_ref=source_ref,
        include_candidates="summary",
        migration_phase=migration_phase,
        allow_legacy=allow_legacy,
    )
    precondition_issues = _check_preconditions(pre_write, repo_roots, source_ref)
    evidence_package = _build_evidence_package(pre_write)
    legacy_registry = _assess_legacy_registry_retirement(blueprint_root, repo_roots)

    if precondition_issues:
        return NormalizationReport(
            requested_source_ref=source_ref,
            source_refs=pre_write.source_refs,
            preconditions_met=False,
            precondition_issues=precondition_issues,
            evidence_package=evidence_package,
            pre_write_reconcile=pre_write,
            swap_completed=False,
            rollback_performed=False,
            written_targets=[],
            post_write_validation_issues=[],
            post_write_reconcile=None,
            legacy_registry=legacy_registry,
        )

    post_write_validation_issues: list[Issue] = []
    written_targets: list[str] = []
    swap_completed = False
    rollback_performed = False
    with tempfile.TemporaryDirectory(prefix="ovis-registry-stage-", dir=str(blueprint_root.parent)) as temp_root_str:
        temp_root = Path(temp_root_str)
        materialize_candidate_registry(
            pre_write.derived.candidate_artifacts,
            destination_root=temp_root,
        )
        post_write_validation_issues.extend(
            validate_materialized_registry(
                registry_root=temp_root,
                source_refs=pre_write.source_refs,
            )
        )
        if not post_write_validation_issues:
            try:
                written_targets, rollback_performed = replace_registry_authority(
                    blueprint_root=blueprint_root,
                    staging_registry_root=temp_root,
                )
                swap_completed = True
            except Exception as exc:
                post_write_validation_issues.append(
                    Issue(
                        "ERROR",
                        str(blueprint_root / "REGISTRIES"),
                        f"Controlled registry replacement failed: {exc}",
                    )
                )

    post_write_reconcile: ReconciliationReport | None = None
    if swap_completed and not post_write_validation_issues:
        post_write_reconcile = reconcile_workspace(
            repo_roots,
            blueprint_root=blueprint_root,
            exclusion_manifest=exclusion_manifest,
            source_ref=source_ref,
            include_candidates="summary",
            migration_phase=migration_phase,
            allow_legacy=allow_legacy,
        )
        post_write_validation_issues.extend(_check_post_write_reconcile(post_write_reconcile))

    return NormalizationReport(
        requested_source_ref=source_ref,
        source_refs=pre_write.source_refs,
        preconditions_met=True,
        precondition_issues=[],
        evidence_package=evidence_package,
        pre_write_reconcile=pre_write,
        swap_completed=swap_completed,
        rollback_performed=rollback_performed,
        written_targets=written_targets,
        post_write_validation_issues=post_write_validation_issues,
        post_write_reconcile=post_write_reconcile,
        legacy_registry=legacy_registry,
    )


def _check_preconditions(
    report: ReconciliationReport,
    repo_roots: list[Path],
    source_ref: str,
) -> list[Issue]:
    issues: list[Issue] = []
    issues.extend(report.artifact_issues)

    if any(finding.severity == "ERROR" for finding in report.drift.findings):
        issues.append(Issue("ERROR", "reconcile", "Dry-run reconcile reported ERROR-severity drift."))

    disallowed_categories = sorted({finding.category for finding in report.drift.findings} - ALLOWED_PREWRITE_DRIFT)
    if disallowed_categories:
        issues.append(
            Issue(
                "ERROR",
                "reconcile",
                f"Dry-run reconcile reported unreviewed drift categories: {', '.join(disallowed_categories)}",
            )
        )

    stale_ids = {
        finding.path
        for finding in report.drift.findings
        if finding.category == "stale_entry"
    }
    stale_workflow_ids = sorted(stale_ids.intersection(WORKFLOW_PARENT_ENTRY_IDS))
    if stale_workflow_ids:
        issues.append(
            Issue(
                "ERROR",
                "reconcile",
                f"Workflow parent entries remain stale in the pinned cutover snapshot: {', '.join(stale_workflow_ids)}",
            )
        )

    unexpected_stale = sorted(stale_ids - EXPECTED_STALE_ENTRY_IDS)
    if unexpected_stale:
        issues.append(
            Issue(
                "ERROR",
                "reconcile",
                f"Dry-run reconcile reported stale entries outside the reviewed set: {', '.join(unexpected_stale)}",
            )
        )

    for repo_root in repo_roots:
        source = GitRefSource(repo_root, ref=source_ref)
        try:
            if source.read_text(WORKFLOW_PARENT_RELATIVE_PATH) is None:
                issues.append(
                    Issue(
                        "ERROR",
                        str(repo_root / WORKFLOW_PARENT_RELATIVE_PATH),
                        f"Workflow parent file is not tracked at {source_ref}.",
                    )
                )
        except Exception as exc:
            issues.append(
                Issue(
                    "ERROR",
                    str(repo_root / WORKFLOW_PARENT_RELATIVE_PATH),
                    f"Failed to resolve workflow parent file from {source_ref}: {exc}",
                )
            )

    return issues


def _check_post_write_reconcile(report: ReconciliationReport) -> list[Issue]:
    issues: list[Issue] = []
    if report.artifact_issues:
        issues.extend(report.artifact_issues)

    counts = Counter(finding.category for finding in report.drift.findings)
    required_zero = (
        "payload_mismatch",
        "stale_entry",
        "missing_entry",
        "allocator_family_unexpected",
        "allocator_family_missing",
        "allocator_next_number_mismatch",
        "aggregate_mismatch",
    )
    for category in required_zero:
        if counts.get(category, 0) != 0:
            issues.append(
                Issue(
                    "ERROR",
                    "reconcile",
                    f"Post-write reconcile still reports {counts[category]} {category} finding(s).",
                )
            )

    if any(finding.severity == "ERROR" for finding in report.drift.findings):
        issues.append(Issue("ERROR", "reconcile", "Post-write reconcile reported ERROR-severity drift."))

    return issues


def _build_evidence_package(report: ReconciliationReport) -> dict[str, object]:
    counts_by_category = Counter(finding.category for finding in report.drift.findings)
    accepted_rationale = {
        "payload_mismatch": "expected post-Wave-1 metadata advancement against non-canonical registry working state",
        "stale_entry": "reviewed exclusions and legacy working-state artifacts only",
        "allocator_family_unexpected": "legacy or non-canonical allocator family debt expected to collapse under regeneration",
        "aggregate_mismatch": "derived consequence of non-canonical working allocator and entry state",
    }
    return {
        "source_refs": dict(report.source_refs),
        "derivation_hash": report.derived.derivation_hash,
        "candidate_hashes": {
            key: artifact.sha256
            for key, artifact in sorted(report.derived.candidate_artifacts.items())
        },
        "reviewed_drift": {
            "counts_by_category": dict(counts_by_category),
            "accepted_rationale_by_category": {
                category: accepted_rationale[category]
                for category in sorted(set(counts_by_category).intersection(accepted_rationale))
            },
            "accepted_findings": [
                finding.as_dict()
                for finding in report.drift.findings
                if finding.category in ALLOWED_PREWRITE_DRIFT
            ],
        },
    }


def _assess_legacy_registry_retirement(
    blueprint_root: Path,
    repo_roots: Iterable[Path],
) -> LegacyRegistryRetirementVerdict:
    reasons: list[str] = []
    legacy_path = blueprint_root / "REGISTRIES" / "id_registry.yaml"
    if legacy_path.exists():
        reasons.append("REGISTRIES/id_registry.yaml still exists in the working tree.")

    references = _find_id_registry_references([blueprint_root, *repo_roots])
    if references:
        reasons.append("Policy, task, or tooling references to id_registry.yaml remain present.")

    return LegacyRegistryRetirementVerdict(
        ready=not reasons,
        reasons=reasons if reasons else ["Legacy registry retirement checks passed."],
    )


def _find_id_registry_references(roots: Iterable[Path]) -> list[str]:
    matches: set[str] = set()
    for root in roots:
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() in {".pyc", ".pyo"}:
                continue
            normalized = path.as_posix()
            if "__pycache__/" in normalized or "/.git/" in normalized or normalized.endswith("/REGISTRIES/id_registry.yaml"):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            if "id_registry.yaml" in text:
                matches.add(str(path))
    return sorted(matches)
