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
import subprocess

from .parser import parse_metadata_file
from .schema import validate_item
from .types import Issue, ParsedMetadata, ScanReport

EXCLUDED_PATH_TOKENS = (
    "__pycache__/",
    ".pytest_cache/",
    ".ruff_cache/",
    "REGISTRIES/entries/",
    "REGISTRIES/OVIS_FILE_REGISTRY.yaml",
)
EXCLUDED_SUFFIXES = (".pyc", ".pyo", ".ovis.yaml")
IN_SCOPE_SUFFIXES = (".gitignore", ".markdown", ".md", ".py", ".toml", ".yaml", ".yml")


def scan_workspace(
    repo_roots: list[Path],
    *,
    migration_phase: str = "M2",
    allow_legacy: bool = False,
) -> ScanReport:
    issues: list[Issue] = []
    items: list[ParsedMetadata] = []
    scanned_files: list[str] = []
    complete = True

    for repo_root in repo_roots:
        try:
            tracked_files = _git_ls_files(repo_root)
        except subprocess.CalledProcessError as exc:
            issues.append(Issue("ERROR", str(repo_root), f"Failed to enumerate tracked files: {exc.stderr.strip()}"))
            complete = False
            continue

        for relative_path in tracked_files:
            if not _is_in_scope(relative_path):
                continue
            path = repo_root / relative_path
            scanned_files.append(f"{repo_root.name}:{relative_path}")
            parsed, parse_issues = parse_metadata_file(path, repo_root)
            issues.extend(parse_issues)
            if parsed is None:
                issues.append(Issue("ERROR", f"{repo_root.name}:{relative_path}", "Missing required metadata."))
                continue
            items.append(parsed)
            issues.extend(validate_item(parsed, migration_phase=migration_phase, allow_legacy=allow_legacy))

    issues.extend(_detect_duplicate_ids(items))
    return ScanReport(
        repo_roots=[str(root) for root in repo_roots],
        complete=complete,
        items=items,
        issues=issues,
        scanned_files=scanned_files,
    )


def _git_ls_files(repo_root: Path) -> list[str]:
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
    if any(token in normalized for token in EXCLUDED_PATH_TOKENS):
        return False
    if normalized.endswith(EXCLUDED_SUFFIXES):
        return False
    return normalized.endswith(IN_SCOPE_SUFFIXES)


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
