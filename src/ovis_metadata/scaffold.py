# ---
# id: MODULE-GOV-0008
# title: OVIS Metadata Scaffold Helper
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: gov
# repo: ovis-runtime
# path: src/ovis_metadata/scaffold.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-GOV-0008.yaml
# ---
"""Thin local metadata scaffold helper for file-birth hygiene."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

from .parser import COMMENT_PREFIXES, parse_metadata_file
from .types import REQUIRED_FIELDS

STRICT_SIDECAR_SUFFIXES = {".gitignore", ".json", ".toml", ".yaml", ".yml"}
TEXT_FRONTMATTER_SUFFIXES = {".markdown", ".md", ".txt"}
MetadataValue = str | list[str]
MetadataPayload = dict[str, MetadataValue]


@dataclass(slots=True)
class ScaffoldResult:
    target_path: str
    metadata_path: str
    mode: str
    created: bool
    metadata: MetadataPayload

    def as_dict(self) -> dict[str, object]:
        return {
            "target_path": self.target_path,
            "metadata_path": self.metadata_path,
            "mode": self.mode,
            "created": self.created,
            "metadata": self.metadata,
        }


def init_file(
    *,
    root: Path,
    repo: str,
    relative_path: str,
    title: str,
    metadata_type: str,
    layer: str,
    domain: str,
    owner: str | None = None,
    document_class: bool = False,
    sidecar: bool = False,
    identifier: str | None = None,
    trusted_id_authority: bool = False,
    module_id: str | None = None,
    module_slug: str | None = None,
    system_id: str | None = None,
    system_slug: str | None = None,
    related_module_ids: list[str] | None = None,
) -> ScaffoldResult:
    root = root.resolve()
    if root.name != repo:
        raise ValueError("Target repo cannot be determined safely from --root and --repo.")

    target = (root / relative_path).resolve()
    if not str(target).startswith(str(root)):
        raise ValueError("Target path is ambiguous or escapes the repo root.")

    existing, parse_issues = parse_metadata_file(target, root) if target.exists() else (None, [])
    if parse_issues:
        raise ValueError("Existing metadata is structurally invalid; refusing scaffold insertion.")
    if existing is not None:
        raise ValueError("Metadata already exists for the target file; refusing conflicting scaffold insertion.")

    chosen_id = _resolve_identifier(identifier, trusted_id_authority)
    metadata = _build_metadata(
        repo=repo,
        relative_path=Path(relative_path).as_posix(),
        title=title,
        metadata_type=metadata_type,
        layer=layer,
        domain=domain,
        owner=owner or "unknown",
        identifier=chosen_id,
        module_id=module_id,
        module_slug=module_slug,
        system_id=system_id,
        system_slug=system_slug,
        related_module_ids=related_module_ids or [],
    )
    _validate_scaffold_metadata(metadata)

    mode = _determine_mode(target, sidecar=sidecar)
    target.parent.mkdir(parents=True, exist_ok=True)

    if mode == "frontmatter":
        _write_frontmatter(target, metadata, document_class=document_class)
        metadata_path = str(target)
    elif mode == "commented_header":
        _write_commented_header(target, metadata, comment_prefix=COMMENT_PREFIXES[target.suffix.lower()])
        metadata_path = str(target)
    elif mode == "sidecar":
        if target.suffix.lower() in {".yaml", ".yml"} and not sidecar:
            target.write_text("", encoding="utf-8")
        sidecar_path = target.with_name(target.name + ".ovis.yaml")
        if target.exists() and target.read_text(encoding="utf-8") and not sidecar_path.exists():
            raise ValueError("Strict files with existing content require explicit --sidecar handling only.")
        sidecar_path.write_text(yaml.safe_dump(metadata, sort_keys=False), encoding="utf-8")
        if not target.exists():
            target.write_text("", encoding="utf-8")
        metadata_path = str(sidecar_path)
    else:
        raise ValueError("Unsupported metadata insertion mode.")

    return ScaffoldResult(
        target_path=str(target),
        metadata_path=metadata_path,
        mode=mode,
        created=True,
        metadata=metadata,
    )


def _resolve_identifier(identifier: str | None, trusted_id_authority: bool) -> str:
    if not identifier or identifier == "TBD":
        return "TBD"
    if not trusted_id_authority:
        raise ValueError("Canonical IDs require explicit trusted allocator authority.")
    return identifier


def _build_metadata(
    *,
    repo: str,
    relative_path: str,
    title: str,
    metadata_type: str,
    layer: str,
    domain: str,
    owner: str,
    identifier: str,
    module_id: str | None,
    module_slug: str | None,
    system_id: str | None,
    system_slug: str | None,
    related_module_ids: list[str],
) -> MetadataPayload:
    today = date.today().isoformat()
    payload = {
        "id": identifier,
        "title": title,
        "type": metadata_type,
        "status": "draft",
        "authority": "operational",
        "version": "0.1",
        "layer": layer,
        "domain": domain,
        "repo": repo,
        "path": relative_path,
        "owner": owner,
        "created": today,
        "last_updated": today,
        # Transitional placeholder only. Canonical entry paths are assigned after a
        # governed artifact receives a non-provisional ID.
        "registry": "ovis-blueprint/REGISTRIES/entries/",
    }
    structural_values = {
        "module_id": module_id,
        "module_slug": module_slug,
        "system_id": system_id,
        "system_slug": system_slug,
    }
    present_structural = {key for key, value in structural_values.items() if value}
    if present_structural and present_structural != set(structural_values):
        missing = ", ".join(sorted(set(structural_values) - present_structural))
        raise ValueError(f"Structural containment requires all core fields; missing: {missing}")
    payload.update({key: value for key, value in structural_values.items() if value})
    if related_module_ids:
        payload["related_module_ids"] = related_module_ids
    if identifier == "TBD":
        payload["provisional_id_hint"] = f"{metadata_type}-{domain}".replace("_", "-").upper()
    return payload


def _validate_scaffold_metadata(metadata: MetadataPayload) -> None:
    missing = [field for field in REQUIRED_FIELDS if field not in metadata or metadata[field] == ""]
    if missing:
        raise ValueError(f"Missing required scaffold fields: {', '.join(missing)}")
    if metadata["id"] == "TBD" and "provisional_id_hint" not in metadata:
        raise ValueError("Provisional scaffold must include provisional_id_hint when id is TBD.")


def _determine_mode(target: Path, *, sidecar: bool) -> str:
    suffix = target.suffix.lower()
    name = target.name.lower()
    if sidecar:
        return "sidecar"
    if suffix in TEXT_FRONTMATTER_SUFFIXES:
        return "frontmatter"
    if suffix in COMMENT_PREFIXES:
        return "commented_header"
    if suffix in {".json", ".toml", ".yaml", ".yml"} or name == ".gitignore":
        return "sidecar"
    raise ValueError("File type cannot be classified safely; use --sidecar for explicit sidecar mode.")


def _write_frontmatter(target: Path, metadata: MetadataPayload, *, document_class: bool) -> None:
    body = ""
    if target.exists():
        body = target.read_text(encoding="utf-8")
    elif document_class:
        body = _document_sections()

    frontmatter = f"---\n{yaml.safe_dump(metadata, sort_keys=False).strip()}\n---\n\n"
    target.write_text(frontmatter + body.lstrip("\n"), encoding="utf-8")


def _write_commented_header(target: Path, metadata: MetadataPayload, *, comment_prefix: str) -> None:
    body = target.read_text(encoding="utf-8") if target.exists() else ""
    raw_yaml = yaml.safe_dump(metadata, sort_keys=False).splitlines()
    header_lines = [f"{comment_prefix} ---", *[f"{comment_prefix} {line}" for line in raw_yaml], f"{comment_prefix} ---", ""]
    target.write_text("\n".join(header_lines) + body, encoding="utf-8")


def _document_sections() -> str:
    return (
        "# Purpose\n\n"
        "TBD.\n\n"
        "# Scope\n\n"
        "TBD.\n\n"
        "# Content\n\n"
        "TBD.\n\n"
        "# References\n\n"
        "None.\n"
    )
