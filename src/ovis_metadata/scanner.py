# ---
# id: MODULE-GOV-0005
# title: OVIS Metadata Scanner
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: gov
# repo: ovis-runtime
# path: src/ovis_metadata/scanner.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-GOV-0005.yaml
# ---
"""Workspace scanning for canonical metadata coverage."""

from __future__ import annotations

from pathlib import Path

from .parser import parse_metadata_file, parse_metadata_source
from .scope import load_normalization_scope
from .source import GitRefSource
from .schema import validate_item
from .types import ExcludedArtifact, Issue, ParsedMetadata, ScanReport

EXCLUDED_PATH_TOKENS = (
    "__pycache__/",
    ".pytest_cache/",
    ".ruff_cache/",
    "REGISTRIES/allocators.yaml",
    "REGISTRIES/entries/",
    "REGISTRIES/OVIS_FILE_REGISTRY.yaml",
    "REGISTRIES/id_registry.yaml",
)
EXCLUDED_SUFFIXES = (".pyc", ".pyo", ".ovis.yaml")
IN_SCOPE_SUFFIXES = (".gitignore", ".markdown", ".md", ".py", ".toml", ".yaml", ".yml")
STATIC_EXCLUDED_PATHS = frozenset({"POLICIES/REGISTRY_NORMALIZATION_EXCLUSIONS.yaml"})


def scan_workspace(
    repo_roots: list[Path],
    *,
    migration_phase: str = "M2",
    allow_legacy: bool = False,
    source_ref: str | None = None,
    exclusion_manifest: Path | None = None,
) -> ScanReport:
    issues: list[Issue] = []
    items: list[ParsedMetadata] = []
    scanned_files: list[str] = []
    excluded_files: list[ExcludedArtifact] = []
    source_refs: dict[str, str] = {}
    complete = True

    scope = None
    if exclusion_manifest is not None:
        scope, scope_issues = load_normalization_scope(exclusion_manifest)
        issues.extend(scope_issues)
        if scope is None:
            complete = False

    for repo_root in repo_roots:
        tracked_files: list[str]
        repo_source = None
        if source_ref is None:
            try:
                tracked_files = _git_ls_files(repo_root)
            except Exception as exc:
                issues.append(Issue("ERROR", str(repo_root), f"Failed to enumerate tracked files: {exc}"))
                complete = False
                continue
        else:
            repo_source = GitRefSource(repo_root, ref=source_ref)
            try:
                source_refs[repo_root.name] = repo_source.resolve_ref()
                tracked_files = repo_source.list_tracked_files()
            except Exception as exc:
                issues.append(Issue("ERROR", str(repo_root), f"Failed to enumerate tracked files from {source_ref}: {exc}"))
                complete = False
                continue

        for relative_path in tracked_files:
            exclusion_reason = _excluded_reason(relative_path, repo_root.name, scope)
            if exclusion_reason is not None:
                excluded_files.append(
                    ExcludedArtifact(
                        repo=repo_root.name,
                        path=relative_path,
                        reason=exclusion_reason,
                    )
                )
                continue
            if not _is_in_scope(relative_path):
                continue
            path = repo_root / relative_path
            scanned_files.append(f"{repo_root.name}:{relative_path}")
            if repo_source is None:
                parsed, parse_issues = parse_metadata_file(path, repo_root)
            else:
                parsed, parse_issues = parse_metadata_source(relative_path, repo_root, repo_source.read_text)
            issues.extend(parse_issues)
            if parsed is None:
                issues.append(Issue("ERROR", f"{repo_root.name}:{relative_path}", "Missing required metadata."))
                continue
            items.append(parsed)
            issues.extend(validate_item(parsed, migration_phase=migration_phase, allow_legacy=allow_legacy))

    issues.extend(_detect_duplicate_ids(items))
    issues.extend(_detect_duplicate_paths(items))
    return ScanReport(
        repo_roots=[str(root) for root in repo_roots],
        complete=complete,
        items=items,
        issues=issues,
        scanned_files=scanned_files,
        source_refs=source_refs,
        excluded_files=excluded_files,
    )


def _git_ls_files(repo_root: Path) -> list[str]:
    import subprocess

    result = subprocess.run(
        ["git", "ls-files"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return [
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip() and (repo_root / line.strip()).exists()
    ]


def _is_in_scope(relative_path: str) -> bool:
    normalized = relative_path.replace("\\", "/")
    return normalized.endswith(IN_SCOPE_SUFFIXES)


def _excluded_reason(
    relative_path: str,
    repo_name: str,
    scope,
) -> str | None:
    normalized = relative_path.replace("\\", "/")
    if normalized in STATIC_EXCLUDED_PATHS:
        return "normalization_exclusion_manifest"
    if any(token in normalized for token in EXCLUDED_PATH_TOKENS):
        return "registry_state"
    if normalized.endswith(EXCLUDED_SUFFIXES):
        return "generated_or_sidecar_storage"
    if scope is not None:
        scope_reason = scope.is_excluded(repo_name, normalized)
        if scope_reason is not None:
            return f"manifest:{scope_reason}"
    return None


def _detect_duplicate_ids(items: list[ParsedMetadata]) -> list[Issue]:
    issues: list[Issue] = []
    seen: dict[str, str] = {}
    for item in items:
        identifier = str(item.metadata.get("id", ""))
        display_path = f"{item.repo_name}:{item.relative_path}"
        if not identifier:
            continue
        previous = seen.get(identifier)
        if previous and previous != display_path:
            issues.append(Issue("ERROR", display_path, f"Duplicate metadata id {identifier!r}; first seen at {previous}"))
        else:
            seen[identifier] = display_path
    return issues


def _detect_duplicate_paths(items: list[ParsedMetadata]) -> list[Issue]:
    issues: list[Issue] = []
    seen: dict[str, str] = {}
    for item in items:
        display_path = f"{item.repo_name}:{item.relative_path}"
        identifier = str(item.metadata.get("id", ""))
        previous = seen.get(display_path)
        if previous and previous != identifier:
            issues.append(
                Issue(
                    "ERROR",
                    display_path,
                    f"Artifact path collision across ids: {previous!r} and {identifier!r}",
                )
            )
        else:
            seen[display_path] = identifier
    return issues
