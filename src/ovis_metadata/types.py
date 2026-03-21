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

    def as_dict(self) -> dict[str, Any]:
        return {
            "repo_roots": self.repo_roots,
            "complete": self.complete,
            "items": [item.as_dict() for item in self.items],
            "issues": [issue.as_dict() for issue in self.issues],
            "scanned_files": self.scanned_files,
        }


@dataclass(slots=True)
class RegistryState:
    allocator_path: Path
    entries_dir: Path
    aggregate_path: Path
    allocators: dict[str, Any]
    entries: dict[str, dict[str, Any]]
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
