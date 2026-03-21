# ---
# id: TEST-GOV-0002
# title: Metadata Scaffold Tests
# type: TEST
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: gov
# repo: ovis-runtime
# path: tests/test_metadata_scaffold.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/TEST-GOV-0002.yaml
# ---
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_metadata.scaffold import init_file  # noqa: E402


def test_markdown_scaffold_creation(tmp_path: Path) -> None:
    repo_root = tmp_path / "ovis-runtime"
    repo_root.mkdir()

    result = init_file(
        root=repo_root,
        repo="ovis-runtime",
        relative_path="docs/example.md",
        title="Example",
        metadata_type="DOC",
        layer="runtime",
        domain="run",
        document_class=True,
    )

    text = (repo_root / "docs/example.md").read_text(encoding="utf-8")
    assert result.mode == "frontmatter"
    assert "id: TBD" in text
    assert result.metadata["registry"] == "ovis-blueprint/REGISTRIES/entries/"
    assert "# Purpose" in text
    assert "# References" in text


def test_code_scaffold_creation_for_python(tmp_path: Path) -> None:
    repo_root = tmp_path / "ovis-runtime"
    repo_root.mkdir()

    result = init_file(
        root=repo_root,
        repo="ovis-runtime",
        relative_path="src/example.py",
        title="Example Module",
        metadata_type="MODULE",
        layer="runtime",
        domain="run",
    )

    text = (repo_root / "src/example.py").read_text(encoding="utf-8")
    assert result.mode == "commented_header"
    assert text.startswith("# ---")
    assert "provisional_id_hint: MODULE-RUN" in text


def test_sidecar_creation_for_strict_file(tmp_path: Path) -> None:
    repo_root = tmp_path / "ovis-runtime"
    repo_root.mkdir()

    result = init_file(
        root=repo_root,
        repo="ovis-runtime",
        relative_path="pyproject.toml",
        title="Runtime Config",
        metadata_type="CONFIG",
        layer="runtime",
        domain="run",
    )

    assert result.mode == "sidecar"
    assert (repo_root / "pyproject.toml.ovis.yaml").exists()


def test_refusal_when_canonical_id_requested_without_authority(tmp_path: Path) -> None:
    repo_root = tmp_path / "ovis-runtime"
    repo_root.mkdir()

    with pytest.raises(ValueError, match="trusted allocator authority"):
        init_file(
            root=repo_root,
            repo="ovis-runtime",
            relative_path="docs/example.md",
            title="Example",
            metadata_type="DOC",
            layer="runtime",
            domain="run",
            identifier="DOC-RUN-0001",
        )


def test_refusal_on_ambiguous_file_type(tmp_path: Path) -> None:
    repo_root = tmp_path / "ovis-runtime"
    repo_root.mkdir()

    with pytest.raises(ValueError, match="classified safely"):
        init_file(
            root=repo_root,
            repo="ovis-runtime",
            relative_path="notes/example.unknown",
            title="Example",
            metadata_type="DOC",
            layer="runtime",
            domain="run",
        )


def test_document_class_section_order(tmp_path: Path) -> None:
    repo_root = tmp_path / "ovis-runtime"
    repo_root.mkdir()

    init_file(
        root=repo_root,
        repo="ovis-runtime",
        relative_path="docs/ordered.md",
        title="Ordered",
        metadata_type="DOC",
        layer="runtime",
        domain="run",
        document_class=True,
    )

    body = (repo_root / "docs/ordered.md").read_text(encoding="utf-8")
    assert body.index("# Purpose") < body.index("# Scope") < body.index("# Content") < body.index("# References")


def test_structural_containment_is_written_when_provided(tmp_path: Path) -> None:
    repo_root = tmp_path / "ovis-runtime"
    repo_root.mkdir()

    result = init_file(
        root=repo_root,
        repo="ovis-runtime",
        relative_path="docs/structured.md",
        title="Structured",
        metadata_type="DOC",
        layer="runtime",
        domain="structure",
        document_class=True,
        module_id="MOD-META-SCAFFOLD-0001",
        module_slug="meta_scaffold",
        system_id="SYS-METADATA-0001",
        system_slug="metadata_system",
        related_module_ids=["MOD-META-HEADER-0001"],
    )

    body = (repo_root / "docs/structured.md").read_text(encoding="utf-8")
    assert result.metadata["related_module_ids"] == ["MOD-META-HEADER-0001"]
    assert "module_id: MOD-META-SCAFFOLD-0001" in body
    assert "related_module_ids:" in body
    assert "- MOD-META-HEADER-0001" in body


def test_provisional_registry_placeholder_is_only_used_with_tbd_id(tmp_path: Path) -> None:
    repo_root = tmp_path / "ovis-runtime"
    repo_root.mkdir()

    result = init_file(
        root=repo_root,
        repo="ovis-runtime",
        relative_path="docs/provisional.md",
        title="Provisional",
        metadata_type="DOC",
        layer="runtime",
        domain="run",
    )

    assert result.metadata["id"] == "TBD"
    assert result.metadata["registry"] == "ovis-blueprint/REGISTRIES/entries/"


def test_refusal_on_partial_structural_containment(tmp_path: Path) -> None:
    repo_root = tmp_path / "ovis-runtime"
    repo_root.mkdir()

    with pytest.raises(ValueError, match="Structural containment requires all core fields"):
        init_file(
            root=repo_root,
            repo="ovis-runtime",
            relative_path="docs/partial.md",
            title="Partial",
            metadata_type="DOC",
            layer="runtime",
            domain="structure",
            module_id="MOD-META-SCAFFOLD-0001",
            system_id="SYS-METADATA-0001",
        )


def test_refusal_when_conflicting_metadata_already_exists(tmp_path: Path) -> None:
    repo_root = tmp_path / "ovis-runtime"
    repo_root.mkdir()
    target = repo_root / "docs/existing.md"
    target.parent.mkdir(parents=True)
    target.write_text(
        """---
id: DOC-RUN-0001
title: Existing
type: DOC
status: active
authority: canonical
version: 0.1
layer: runtime
domain: run
repo: ovis-runtime
path: docs/existing.md
owner: Owen Vitae
created: 2026-03-21
last_updated: 2026-03-21
registry: ovis-blueprint/REGISTRIES/entries/DOC-RUN-0001.yaml
---
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Metadata already exists"):
        init_file(
            root=repo_root,
            repo="ovis-runtime",
            relative_path="docs/existing.md",
            title="Replacement",
            metadata_type="DOC",
            layer="runtime",
            domain="run",
        )
