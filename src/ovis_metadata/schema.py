# ---
# id: MODULE-GOV-0004
# title: OVIS Metadata Schema Validation
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: gov
# repo: ovis-runtime
# path: src/ovis_metadata/schema.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-GOV-0004.yaml
# ---
"""Schema validation for canonical workspace metadata."""

from __future__ import annotations

import re
from typing import Iterable

from .types import (
    ALLOWED_AUTHORITY,
    ALLOWED_MIGRATION_PHASES,
    ALLOWED_STATUS,
    ALLOWED_TYPES,
    DOCUMENT_TYPES,
    Issue,
    ParsedMetadata,
    REQUIRED_FIELDS,
    STRUCTURAL_CORE_FIELDS,
)

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ID_PATTERN = re.compile(r"^[A-Z]+(?:-[A-Z0-9]+)+-\d{4}$")
DOMAIN_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
MODULE_ID_PATTERN = re.compile(r"^MOD-(?:[A-Z0-9]+-)*[A-Z0-9]+-\d{4}$")
SYSTEM_ID_PATTERN = re.compile(r"^SYS-(?:[A-Z0-9]+-)*[A-Z0-9]+-\d{4}$")
SLUG_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
SECTION_PATTERN = re.compile(r"^\s{0,3}(?P<marks>#{1,6})\s+(?P<title>[^#].*?)\s*$")
REQUIRED_SECTIONS = ("purpose", "scope", "content", "references")


def validate_item(
    item: ParsedMetadata,
    *,
    migration_phase: str = "M2",
    allow_legacy: bool = False,
) -> list[Issue]:
    issues: list[Issue] = list(item.warnings)
    display_path = f"{item.repo_name}:{item.relative_path}"

    if migration_phase not in ALLOWED_MIGRATION_PHASES:
        issues.append(Issue("ERROR", display_path, f"Unknown migration phase: {migration_phase}"))
        return issues

    for field in REQUIRED_FIELDS:
        value = item.metadata.get(field)
        if value is None or value == "":
            issues.append(Issue("ERROR", display_path, f"Missing required field: {field}"))

    metadata_type = str(item.metadata.get("type", ""))
    if metadata_type and metadata_type not in ALLOWED_TYPES:
        issues.append(Issue("ERROR", display_path, f"Invalid type: {metadata_type}"))

    status = str(item.metadata.get("status", ""))
    if status and status not in ALLOWED_STATUS:
        issues.append(Issue("ERROR", display_path, f"Invalid status: {status}"))

    authority = str(item.metadata.get("authority", ""))
    if authority and authority not in ALLOWED_AUTHORITY:
        issues.append(Issue("ERROR", display_path, f"Invalid authority: {authority}"))

    identifier = str(item.metadata.get("id", ""))
    if identifier and not ID_PATTERN.match(identifier):
        issues.append(Issue("ERROR", display_path, f"Invalid id format: {identifier}"))

    for field in ("created", "last_updated"):
        value = str(item.metadata.get(field, ""))
        if value and not DATE_PATTERN.match(value):
            issues.append(Issue("ERROR", display_path, f"Invalid date for {field}: {value}"))

    domain = str(item.metadata.get("domain", ""))
    if domain and not DOMAIN_PATTERN.match(domain):
        issues.append(Issue("ERROR", display_path, f"Invalid domain token: {domain}"))

    declared_repo = str(item.metadata.get("repo", ""))
    if declared_repo and declared_repo != item.repo_name:
        issues.append(
            Issue(
                "ERROR",
                display_path,
                f"Declared repo {declared_repo!r} does not match scanned repo {item.repo_name!r}",
            )
        )

    declared_path = str(item.metadata.get("path", ""))
    if declared_path and declared_path != item.relative_path:
        issues.append(
            Issue(
                "ERROR",
                display_path,
                f"Declared path {declared_path!r} does not match actual path {item.relative_path!r}",
            )
        )

    issues.extend(
        _validate_format_policy(
            item,
            display_path,
            migration_phase=migration_phase,
            allow_legacy=allow_legacy,
        )
    )
    issues.extend(_validate_structural_containment(item, display_path))

    if metadata_type in DOCUMENT_TYPES:
        issues.extend(_validate_document_sections(item.body_text, display_path))

    return issues


def _validate_format_policy(
    item: ParsedMetadata,
    display_path: str,
    *,
    migration_phase: str,
    allow_legacy: bool,
) -> Iterable[Issue]:
    if item.format_kind == "canonical":
        return []
    if migration_phase == "M1":
        return []
    if migration_phase == "M2" and allow_legacy:
        return []
    return [
        Issue(
            "ERROR",
            display_path,
            f"Legacy metadata format is not allowed in phase {migration_phase}: {item.format_kind}",
        )
    ]


def _validate_document_sections(body_text: str, display_path: str) -> list[Issue]:
    issues: list[Issue] = []
    lines = body_text.splitlines()
    matches: list[tuple[str, int, int]] = []

    for index, line in enumerate(lines):
        match = SECTION_PATTERN.match(line)
        if match:
            matches.append((match.group("title").strip().lower(), index, len(match.group("marks"))))

    positions: list[int] = []
    required_levels: list[int] = []
    for section in REQUIRED_SECTIONS:
        found = [(index, level) for title, index, level in matches if title == section]
        if not found:
            issues.append(Issue("ERROR", display_path, f"Missing required section heading: {section.title()}"))
            continue
        if len(found) > 1:
            issues.append(Issue("ERROR", display_path, f"Duplicate required section heading: {section.title()}"))
            continue
        positions.append(found[0][0])
        required_levels.append(found[0][1])

    if len(positions) != len(REQUIRED_SECTIONS):
        return issues

    if positions != sorted(positions):
        issues.append(Issue("ERROR", display_path, "Required document sections are out of order."))
        return issues

    if len(set(required_levels)) != 1:
        issues.append(Issue("ERROR", display_path, "Required document sections must use a consistent heading level."))
        return issues

    section_level = required_levels[0]
    references_index = positions[-1]
    if any(
        title not in REQUIRED_SECTIONS and index < references_index and level <= section_level
        for title, index, level in matches
    ):
        issues.append(Issue("ERROR", display_path, "Additional headings are only allowed after References."))

    for section_name, start_index in zip(REQUIRED_SECTIONS, positions):
        next_positions = [index for index in positions if index > start_index]
        next_index = min(next_positions) if next_positions else len(lines)
        nonblank = [line for line in lines[start_index + 1 : next_index] if line.strip()]
        if not nonblank:
            issues.append(Issue("ERROR", display_path, f"Required section is empty: {section_name.title()}"))

    return issues


def _validate_structural_containment(item: ParsedMetadata, display_path: str) -> list[Issue]:
    issues: list[Issue] = []
    metadata = item.metadata
    present_core = {
        field
        for field in STRUCTURAL_CORE_FIELDS
        if metadata.get(field) not in (None, "", [])
    }
    related_modules = metadata.get("related_module_ids")

    if related_modules not in (None, "", []) and "module_id" not in present_core:
        issues.append(
            Issue(
                "ERROR",
                display_path,
                "related_module_ids cannot be declared without a primary module_id.",
            )
        )

    if present_core and present_core != set(STRUCTURAL_CORE_FIELDS):
        missing = ", ".join(sorted(set(STRUCTURAL_CORE_FIELDS) - present_core))
        issues.append(
            Issue(
                "ERROR",
                display_path,
                f"Incomplete structural containment metadata; missing: {missing}",
            )
        )
        return issues

    if not present_core:
        return issues

    module_id = str(metadata.get("module_id", ""))
    if not MODULE_ID_PATTERN.match(module_id):
        issues.append(Issue("ERROR", display_path, f"Invalid module_id format: {module_id}"))

    system_id = str(metadata.get("system_id", ""))
    if not SYSTEM_ID_PATTERN.match(system_id):
        issues.append(Issue("ERROR", display_path, f"Invalid system_id format: {system_id}"))

    for field in ("module_slug", "system_slug"):
        value = str(metadata.get(field, ""))
        if value and not SLUG_PATTERN.match(value):
            issues.append(Issue("ERROR", display_path, f"Invalid {field}: {value}"))

    if related_modules in (None, "", []):
        return issues

    if not isinstance(related_modules, list):
        issues.append(Issue("ERROR", display_path, "related_module_ids must be a list when declared."))
        return issues

    seen_related: set[str] = set()
    for raw_value in related_modules:
        related_module_id = str(raw_value)
        if not MODULE_ID_PATTERN.match(related_module_id):
            issues.append(
                Issue(
                    "ERROR",
                    display_path,
                    f"Invalid related module id format: {related_module_id}",
                )
            )
            continue
        if related_module_id == module_id:
            issues.append(
                Issue(
                    "ERROR",
                    display_path,
                    "related_module_ids must not repeat the primary module_id.",
                )
            )
        if related_module_id in seen_related:
            issues.append(
                Issue(
                    "ERROR",
                    display_path,
                    f"Duplicate related module id: {related_module_id}",
                )
            )
        seen_related.add(related_module_id)

    return issues
