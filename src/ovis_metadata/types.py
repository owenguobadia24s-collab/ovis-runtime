# ---
# id: MODULE-GOV-0002
# title: OVIS Metadata Types
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: gov
# repo: ovis-runtime
# path: src/ovis_metadata/types.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-GOV-0002.yaml
# ---
"""Types shared by workspace metadata tooling."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = (
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
)
STRUCTURAL_CORE_FIELDS = (
    "module_id",
    "module_slug",
    "system_id",
    "system_slug",
)
STRUCTURAL_RELATED_FIELDS = ("related_module_ids",)

DOCUMENT_TYPES = frozenset({"ADR", "DOC", "POLICY", "CJ", "TEMPLATE", "NOTE"})
ALLOWED_TYPES = frozenset(
    {
        "ADR",
        "CJ",
        "CONFIG",
        "DOC",
        "MANIFEST",
        "MODULE",
        "NOTE",
        "PACKAGE",
        "POLICY",
        "REGISTRY",
        "SCHEMA",
        "SCRIPT",
        "TEMPLATE",
        "TEST",
    }
)
ALLOWED_STATUS = frozenset(
    {
        "accepted",
        "active",
        "approved",
        "archived",
        "deprecated",
        "draft",
        "emerging",
        "implemented",
        "planned",
        "proposed",
        "stable",
        "superseded",
    }
)
ALLOWED_AUTHORITY = frozenset({"canonical", "derived", "operational"})
ALLOWED_MIGRATION_PHASES = frozenset({"M1", "M2", "M3"})


@dataclass(slots=True)
class Issue:
    severity: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"severity": self.severity, "path": self.path, "message": self.message}


@dataclass(slots=True)
class ParsedMetadata:
    path: Path
    repo_root: Path
    relative_path: str
    metadata: dict[str, Any]
    source_kind: str
    format_kind: str
    body_text: str = ""
    warnings: list[Issue] = field(default_factory=list)

    @property
    def repo_name(self) -> str:
        return self.repo_root.name

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "repo_root": str(self.repo_root),
            "relative_path": self.relative_path,
            "source_kind": self.source_kind,
            "format_kind": self.format_kind,
            "metadata": self.metadata,
            "warnings": [issue.as_dict() for issue in self.warnings],
        }


@dataclass(slots=True)
class ScanReport:
    repo_roots: list[str]
    complete: bool
    items: list[ParsedMetadata]
    issues: list[Issue]
    scanned_files: list[str]
    source_refs: dict[str, str] = field(default_factory=dict)
    excluded_files: list["ExcludedArtifact"] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "repo_roots": self.repo_roots,
            "complete": self.complete,
            "items": [item.as_dict() for item in self.items],
            "issues": [issue.as_dict() for issue in self.issues],
            "scanned_files": self.scanned_files,
            "source_refs": self.source_refs,
            "excluded_files": [item.as_dict() for item in self.excluded_files],
        }


@dataclass(slots=True)
class RegistryState:
    allocator_path: Path
    entries_dir: Path
    aggregate_path: Path
    allocators: dict[str, Any]
    entries: dict[str, dict[str, Any]]
    aggregate: dict[str, Any]
    snapshot_hash: str


@dataclass(slots=True)
class ReconcileResult:
    added_ids: list[str]
    updated_ids: list[str]
    removed_ids: list[str]
    compiled_aggregate_path: str
    issues: list[Issue]

    def as_dict(self) -> dict[str, Any]:
        return {
            "added_ids": self.added_ids,
            "updated_ids": self.updated_ids,
            "removed_ids": self.removed_ids,
            "compiled_aggregate_path": self.compiled_aggregate_path,
            "issues": [issue.as_dict() for issue in self.issues],
        }


@dataclass(slots=True)
class ExcludedArtifact:
    repo: str
    path: str
    reason: str

    def as_dict(self) -> dict[str, str]:
        return {
            "repo": self.repo,
            "path": self.path,
            "reason": self.reason,
        }


@dataclass(slots=True)
class NormalizationScope:
    manifest_path: str
    intentionally_unplaced: dict[str, str]

    def is_excluded(self, repo: str, relative_path: str) -> str | None:
        return self.intentionally_unplaced.get(f"{repo}:{relative_path}")

    def as_dict(self) -> dict[str, Any]:
        return {
            "manifest_path": self.manifest_path,
            "intentionally_unplaced": dict(self.intentionally_unplaced),
        }


@dataclass(slots=True)
class CandidateArtifact:
    path: str
    sha256: str
    text: str

    def as_dict(self, *, include_text: bool) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "path": self.path,
            "sha256": self.sha256,
        }
        if include_text:
            payload["text"] = self.text
        return payload


@dataclass(slots=True)
class DerivedRegistryState:
    allocators: dict[str, Any]
    entries: dict[str, dict[str, Any]]
    aggregate: dict[str, Any]
    candidate_artifacts: dict[str, CandidateArtifact]
    derivation_hash: str

    def as_dict(self, *, include_candidates: str) -> dict[str, Any]:
        include_text = include_candidates == "full"
        entry_candidates = {
            identifier: artifact.as_dict(include_text=include_text)
            for identifier, artifact in sorted(self.candidate_artifacts.items())
            if identifier.startswith("entry:")
        }
        summary = {
            "allocator_family_count": len(self.allocators.get("families", {})),
            "entry_count": len(self.entries),
            "aggregate_entry_count": len(self.aggregate.get("entries", {})),
            "derivation_hash": self.derivation_hash,
            "candidate_hashes": {
                key: artifact.sha256
                for key, artifact in sorted(self.candidate_artifacts.items())
            },
        }
        if include_candidates == "summary":
            return summary
        return {
            **summary,
            "allocators": self.candidate_artifacts["allocators"].as_dict(include_text=True),
            "entries": entry_candidates,
            "aggregate": self.candidate_artifacts["aggregate"].as_dict(include_text=True),
        }


@dataclass(slots=True)
class DriftFinding:
    category: str
    severity: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "category": self.category,
            "severity": self.severity,
            "path": self.path,
            "message": self.message,
        }


@dataclass(slots=True)
class DriftReport:
    findings: list[DriftFinding]

    def as_dict(self) -> dict[str, Any]:
        by_category: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        for finding in self.findings:
            by_category[finding.category] = by_category.get(finding.category, 0) + 1
            by_severity[finding.severity] = by_severity.get(finding.severity, 0) + 1
        return {
            "findings": [finding.as_dict() for finding in self.findings],
            "counts_by_category": by_category,
            "counts_by_severity": by_severity,
        }


@dataclass(slots=True)
class ReconciliationReport:
    source_refs: dict[str, str]
    scope_summary: dict[str, Any]
    artifact_issues: list[Issue]
    derived: DerivedRegistryState
    drift: DriftReport

    def as_dict(self, *, include_candidates: str = "summary") -> dict[str, Any]:
        return {
            "source_refs": dict(self.source_refs),
            "scope_summary": dict(self.scope_summary),
            "artifact_issues": [issue.as_dict() for issue in self.artifact_issues],
            "derived": self.derived.as_dict(include_candidates=include_candidates),
            "drift": self.drift.as_dict(),
        }


@dataclass(slots=True)
class LegacyRegistryRetirementVerdict:
    ready: bool
    reasons: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "reasons": list(self.reasons),
        }


@dataclass(slots=True)
class NormalizationReport:
    requested_source_ref: str
    source_refs: dict[str, str]
    preconditions_met: bool
    precondition_issues: list[Issue]
    evidence_package: dict[str, Any]
    pre_write_reconcile: ReconciliationReport
    swap_completed: bool
    rollback_performed: bool
    written_targets: list[str]
    post_write_validation_issues: list[Issue]
    post_write_reconcile: ReconciliationReport | None
    legacy_registry: LegacyRegistryRetirementVerdict

    def as_dict(self, *, include_candidates: str = "summary") -> dict[str, Any]:
        return {
            "requested_source_ref": self.requested_source_ref,
            "source_refs": dict(self.source_refs),
            "preconditions_met": self.preconditions_met,
            "precondition_issues": [issue.as_dict() for issue in self.precondition_issues],
            "evidence_package": dict(self.evidence_package),
            "pre_write_reconcile": self.pre_write_reconcile.as_dict(include_candidates=include_candidates),
            "swap_completed": self.swap_completed,
            "rollback_performed": self.rollback_performed,
            "written_targets": list(self.written_targets),
            "post_write_validation_issues": [issue.as_dict() for issue in self.post_write_validation_issues],
            "post_write_reconcile": (
                None
                if self.post_write_reconcile is None
                else self.post_write_reconcile.as_dict(include_candidates=include_candidates)
            ),
            "legacy_registry": self.legacy_registry.as_dict(),
        }
