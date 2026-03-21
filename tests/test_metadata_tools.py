# ---
# id: TEST-GOV-0001
# title: Metadata Tooling Tests
# type: TEST
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: gov
# repo: ovis-runtime
# path: tests/test_metadata_tools.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/TEST-GOV-0001.yaml
# ---
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_metadata.parser import parse_metadata_file  # noqa: E402
from ovis_metadata.normalizer import normalize_workspace  # noqa: E402
from ovis_metadata.reconciler import reconcile_workspace  # noqa: E402
from ovis_metadata.registry import read_registry_state  # noqa: E402
from ovis_metadata.scanner import scan_workspace  # noqa: E402
from ovis_metadata.schema import validate_item  # noqa: E402
from ovis_metadata.source import GitRefSource  # noqa: E402
from ovis_operator import cli  # noqa: E402


def test_parse_markdown_frontmatter_detects_canonical_metadata(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    path = repo_root / "README.md"
    path.write_text(
        """---
id: DOC-SYS-0001
title: Example Readme
type: DOC
status: active
authority: canonical
version: 0.1
layer: blueprint
domain: sys
repo: repo
path: README.md
owner: Owen Vitae
created: 2026-03-21
last_updated: 2026-03-21
registry: ovis-blueprint/REGISTRIES/entries/DOC-SYS-0001.yaml
---

# Purpose

Example purpose.

# Scope

Example scope.

# Content

Example content.

# References

None.
""",
        encoding="utf-8",
    )

    parsed, issues = parse_metadata_file(path, repo_root)
    assert not issues
    assert parsed is not None
    assert parsed.metadata["id"] == "DOC-SYS-0001"
    assert parsed.format_kind == "canonical"


def test_scan_workspace_reports_missing_metadata(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "README.md").write_text("# missing metadata\n", encoding="utf-8")
    _git_init(repo_root)

    report = scan_workspace([repo_root])
    assert any("Missing required metadata" in issue.message for issue in report.issues)


def test_reconcile_workspace_reports_dry_run_candidates_without_writing(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    blueprint_root = workspace_root / "ovis-blueprint"
    runtime_root = workspace_root / "ovis-runtime"
    entries_dir = blueprint_root / "REGISTRIES" / "entries"
    entries_dir.mkdir(parents=True)
    aggregate_path = blueprint_root / "REGISTRIES" / "OVIS_FILE_REGISTRY.yaml"
    (blueprint_root / "REGISTRIES" / "allocators.yaml").write_text(
        """id: REGISTRY-GOV-0001
title: OVIS Metadata Allocators
type: REGISTRY
status: active
authority: canonical
version: 0.1
layer: blueprint
domain: gov
repo: ovis-blueprint
path: REGISTRIES/allocators.yaml
owner: Owen Vitae
created: 2026-03-21
last_updated: 2026-03-21
registry: ovis-blueprint/REGISTRIES/entries/REGISTRY-GOV-0001.yaml
families:
  DOC-SYS:
    next_number: 2
    retired_ids: []
  DOC-REPO-ROLE:
    next_number: 2
    retired_ids: []
""",
        encoding="utf-8",
    )
    aggregate_path.write_text(
        """registry_version: 0.1
allocators: {}
entries: {}
""",
        encoding="utf-8",
    )
    manifest_path = blueprint_root / "POLICIES" / "REGISTRY_NORMALIZATION_EXCLUSIONS.yaml"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text("version: '0.1'\nintentionally_unplaced: []\n", encoding="utf-8")
    runtime_root.mkdir(parents=True)
    (runtime_root / "README.md").write_text(
        """---
id: DOC-REPO-ROLE-0001
title: Runtime Readme
type: DOC
status: active
authority: operational
version: 0.1
layer: runtime
domain: repo_role
repo: ovis-runtime
path: README.md
owner: Owen Vitae
created: 2026-03-21
last_updated: 2026-03-21
registry: ovis-blueprint/REGISTRIES/entries/DOC-REPO-ROLE-0001.yaml
---

# Purpose

Purpose.

# Scope

Scope.

# Content

Content.

# References

None.
""",
        encoding="utf-8",
    )
    _git_init(runtime_root)

    before_entries = sorted(entries_dir.glob("*.yaml"))
    before_aggregate = aggregate_path.read_text(encoding="utf-8")

    result = reconcile_workspace(
        [runtime_root],
        blueprint_root=blueprint_root,
        exclusion_manifest=manifest_path,
    )
    payload = result.as_dict(include_candidates="full")
    assert not any(issue["severity"] == "ERROR" for issue in payload["artifact_issues"])
    assert payload["scope_summary"]["included_count"] == 1
    assert payload["derived"]["entry_count"] == 1
    assert "entry:DOC-REPO-ROLE-0001" in payload["derived"]["candidate_hashes"]
    assert sorted(entries_dir.glob("*.yaml")) == before_entries
    assert aggregate_path.read_text(encoding="utf-8") == before_aggregate


def test_metadata_validate_cli_returns_nonzero_on_invalid_document(
    tmp_path: Path,
    capsys,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "README.md").write_text(
        """---
id: DOC-SYS-0001
title: Invalid
type: DOC
status: active
authority: canonical
version: 0.1
layer: blueprint
domain: sys
repo: repo
path: README.md
owner: Owen Vitae
created: 2026-03-21
last_updated: 2026-03-21
registry: ovis-blueprint/REGISTRIES/entries/DOC-SYS-0001.yaml
---

# Purpose

Only purpose.
""",
        encoding="utf-8",
    )
    _git_init(repo_root)

    exit_code = cli.main(["metadata", "validate", "--root", str(repo_root), "--json"])
    output = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert any("Missing required section heading" in issue["message"] for issue in output["issues"])


def test_scan_workspace_reads_committed_head_instead_of_working_tree(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    readme = repo_root / "README.md"
    readme.write_text(
        """---
id: DOC-SYS-0001
title: Stable Readme
type: DOC
status: active
authority: canonical
version: 0.1
layer: blueprint
domain: sys
repo: repo
path: README.md
owner: Owen Vitae
created: 2026-03-21
last_updated: 2026-03-21
registry: ovis-blueprint/REGISTRIES/entries/DOC-SYS-0001.yaml
---

# Purpose

Purpose.

# Scope

Scope.

# Content

Content.

# References

None.
""",
        encoding="utf-8",
    )
    _git_init(repo_root)
    readme.write_text("# broken working tree copy\n", encoding="utf-8")

    report = scan_workspace([repo_root], source_ref="HEAD")
    assert report.complete is True
    assert any(item.metadata["id"] == "DOC-SYS-0001" for item in report.items)
    assert not any(issue.severity == "ERROR" for issue in report.issues)


def test_parse_metadata_source_reads_sidecar_backed_parent_from_git_ref(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "pyproject.toml").write_text("[project]\nname='example'\n", encoding="utf-8")
    (repo_root / "pyproject.toml.ovis.yaml").write_text(
        """id: CONFIG-RUN-0001
title: Runtime Config
type: CONFIG
status: active
authority: canonical
version: 0.1
layer: runtime
domain: run
repo: repo
path: pyproject.toml
owner: Owen Vitae
created: 2026-03-21
last_updated: 2026-03-21
registry: ovis-blueprint/REGISTRIES/entries/CONFIG-RUN-0001.yaml
""",
        encoding="utf-8",
    )
    _git_init(repo_root)

    source = GitRefSource(repo_root, "HEAD")
    from ovis_metadata.parser import parse_metadata_source  # noqa: E402

    parsed, issues = parse_metadata_source("pyproject.toml", repo_root, source.read_text)
    assert parsed is not None
    assert not issues
    assert parsed.source_kind == "sidecar"
    assert parsed.metadata["id"] == "CONFIG-RUN-0001"


def test_scan_workspace_respects_normalization_exclusion_manifest(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    blueprint_root = workspace_root / "ovis-blueprint"
    repo_root = workspace_root / "repo"
    blueprint_root.mkdir(parents=True)
    repo_root.mkdir(parents=True)
    (repo_root / "README.md").write_text(
        """---
id: DOC-SYS-0001
title: Repo Readme
type: DOC
status: active
authority: canonical
version: 0.1
layer: blueprint
domain: sys
repo: repo
path: README.md
owner: Owen Vitae
created: 2026-03-21
last_updated: 2026-03-21
registry: ovis-blueprint/REGISTRIES/entries/DOC-SYS-0001.yaml
---

# Purpose

Purpose.

# Scope

Scope.

# Content

Content.

# References

None.
""",
        encoding="utf-8",
    )
    manifest_path = blueprint_root / "POLICIES" / "REGISTRY_NORMALIZATION_EXCLUSIONS.yaml"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        """version: '0.1'
intentionally_unplaced:
  - repo: repo
    path: README.md
    reason: repo_surface_overview
""",
        encoding="utf-8",
    )
    _git_init(repo_root)

    report = scan_workspace([repo_root], source_ref="HEAD", exclusion_manifest=manifest_path)
    assert not report.items
    assert report.excluded_files
    assert report.excluded_files[0].reason == "manifest:repo_surface_overview"


def test_validate_item_accepts_structural_containment_fields(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    path = repo_root / "SYSTEM_TAXONOMY.md"
    path.write_text(
        """---
id: DOC-STRUCTURE-0001
title: System Taxonomy
type: DOC
status: active
authority: canonical
version: 0.1
layer: blueprint
domain: structure
repo: repo
path: SYSTEM_TAXONOMY.md
owner: Owen Vitae
created: 2026-03-21
last_updated: 2026-03-21
registry: ovis-blueprint/REGISTRIES/entries/DOC-STRUCTURE-0001.yaml
module_id: MOD-META-REGISTRY-0001
module_slug: meta_registry
system_id: SYS-METADATA-0001
system_slug: metadata_system
related_module_ids:
  - MOD-META-SCHEMA-POLICY-0001
---

# Purpose

Purpose.

# Scope

Scope.

# Content

Content.

# References

None.
""",
        encoding="utf-8",
    )

    parsed, issues = parse_metadata_file(path, repo_root)
    assert parsed is not None
    assert not issues
    validation_issues = validate_item(parsed)
    assert not [issue for issue in validation_issues if issue.severity == "ERROR"]


def test_validate_item_rejects_partial_structural_containment_fields(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    path = repo_root / "README.md"
    path.write_text(
        """---
id: DOC-STRUCTURE-0001
title: Invalid Structure
type: DOC
status: active
authority: canonical
version: 0.1
layer: blueprint
domain: structure
repo: repo
path: README.md
owner: Owen Vitae
created: 2026-03-21
last_updated: 2026-03-21
registry: ovis-blueprint/REGISTRIES/entries/DOC-STRUCTURE-0001.yaml
module_id: MOD-META-REGISTRY-0001
system_id: SYS-METADATA-0001
---

# Purpose

Purpose.

# Scope

Scope.

# Content

Content.

# References

None.
""",
        encoding="utf-8",
    )

    parsed, issues = parse_metadata_file(path, repo_root)
    assert parsed is not None
    assert not issues
    validation_issues = validate_item(parsed)
    assert any("Incomplete structural containment metadata" in issue.message for issue in validation_issues)


def test_validate_item_rejects_duplicate_related_module_ids(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    path = repo_root / "README.md"
    path.write_text(
        """---
id: DOC-STRUCTURE-0002
title: Duplicate Related Modules
type: DOC
status: active
authority: canonical
version: 0.1
layer: blueprint
domain: structure
repo: repo
path: README.md
owner: Owen Vitae
created: 2026-03-21
last_updated: 2026-03-21
registry: ovis-blueprint/REGISTRIES/entries/DOC-STRUCTURE-0002.yaml
module_id: MOD-META-REGISTRY-0001
module_slug: meta_registry
system_id: SYS-METADATA-0001
system_slug: metadata_system
related_module_ids:
  - MOD-META-SCHEMA-POLICY-0001
  - MOD-META-SCHEMA-POLICY-0001
---

# Purpose

Purpose.

# Scope

Scope.

# Content

Content.

# References

None.
""",
        encoding="utf-8",
    )

    parsed, issues = parse_metadata_file(path, repo_root)
    assert parsed is not None
    assert not issues
    validation_issues = validate_item(parsed)
    assert any("Duplicate related module id" in issue.message for issue in validation_issues)


def test_validate_item_rejects_primary_module_in_related_module_ids(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    path = repo_root / "README.md"
    path.write_text(
        """---
id: DOC-STRUCTURE-0003
title: Self Related Module
type: DOC
status: active
authority: canonical
version: 0.1
layer: blueprint
domain: structure
repo: repo
path: README.md
owner: Owen Vitae
created: 2026-03-21
last_updated: 2026-03-21
registry: ovis-blueprint/REGISTRIES/entries/DOC-STRUCTURE-0003.yaml
module_id: MOD-META-REGISTRY-0001
module_slug: meta_registry
system_id: SYS-METADATA-0001
system_slug: metadata_system
related_module_ids:
  - MOD-META-REGISTRY-0001
---

# Purpose

Purpose.

# Scope

Scope.

# Content

Content.

# References

None.
""",
        encoding="utf-8",
    )

    parsed, issues = parse_metadata_file(path, repo_root)
    assert parsed is not None
    assert not issues
    validation_issues = validate_item(parsed)
    assert any("must not repeat the primary module_id" in issue.message for issue in validation_issues)


def test_normalize_workspace_replaces_registry_authority_from_pinned_snapshot(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    blueprint_root = workspace_root / "ovis-blueprint"
    runtime_root = workspace_root / "ovis-runtime"
    knowledge_root = workspace_root / "ovis-knowledge"

    _prepare_registry_workspace(blueprint_root)
    _write_workflow_parent(
        blueprint_root,
        repo="ovis-blueprint",
        identifier="MANIFEST-GOV-0001",
        title="Blueprint Metadata Workflow",
        layer="blueprint",
    )
    _write_workflow_parent(
        runtime_root,
        repo="ovis-runtime",
        identifier="MANIFEST-GOV-0002",
        title="Runtime Metadata Workflow",
        layer="runtime",
    )
    _write_workflow_parent(
        knowledge_root,
        repo="ovis-knowledge",
        identifier="MANIFEST-GOV-0003",
        title="Knowledge Metadata Workflow",
        layer="knowledge",
    )

    _git_init(blueprint_root)
    _git_init(runtime_root)
    _git_init(knowledge_root)

    report = normalize_workspace(
        [blueprint_root, runtime_root, knowledge_root],
        blueprint_root=blueprint_root,
        exclusion_manifest=blueprint_root / "POLICIES" / "REGISTRY_NORMALIZATION_EXCLUSIONS.yaml",
        source_ref="HEAD",
    )

    assert report.preconditions_met is True
    assert not report.precondition_issues
    assert report.swap_completed is True
    assert report.rollback_performed is False
    assert not report.post_write_validation_issues
    assert report.post_write_reconcile is not None
    assert not report.post_write_reconcile.artifact_issues
    assert not report.post_write_reconcile.drift.findings
    assert report.pre_write_reconcile.derived.entries["MANIFEST-GOV-0001"]["module_id"] == "MOD-META-SCHEMA-POLICY-0001"

    registry_state, issues = read_registry_state(blueprint_root)
    assert registry_state is not None
    assert not issues
    assert sorted(registry_state.entries) == [
        "MANIFEST-GOV-0001",
        "MANIFEST-GOV-0002",
        "MANIFEST-GOV-0003",
    ]
    assert registry_state.entries["MANIFEST-GOV-0002"]["system_id"] == "SYS-METADATA-0001"
    assert registry_state.aggregate["entries"]["MANIFEST-GOV-0003"]["repo"] == "ovis-knowledge"


def test_normalize_workspace_fails_closed_when_workflow_parents_are_not_tracked(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    blueprint_root = workspace_root / "ovis-blueprint"
    runtime_root = workspace_root / "ovis-runtime"
    knowledge_root = workspace_root / "ovis-knowledge"

    _prepare_registry_workspace(blueprint_root)
    _write_workflow_sidecar_only(
        blueprint_root,
        repo="ovis-blueprint",
        identifier="MANIFEST-GOV-0001",
        title="Blueprint Metadata Workflow",
        layer="blueprint",
    )
    _write_workflow_sidecar_only(
        runtime_root,
        repo="ovis-runtime",
        identifier="MANIFEST-GOV-0002",
        title="Runtime Metadata Workflow",
        layer="runtime",
    )
    _write_workflow_sidecar_only(
        knowledge_root,
        repo="ovis-knowledge",
        identifier="MANIFEST-GOV-0003",
        title="Knowledge Metadata Workflow",
        layer="knowledge",
    )

    _git_init(blueprint_root)
    _git_init(runtime_root)
    _git_init(knowledge_root)

    before_state, issues = read_registry_state(blueprint_root)
    assert before_state is not None
    assert not issues
    before_hash = before_state.snapshot_hash

    report = normalize_workspace(
        [blueprint_root, runtime_root, knowledge_root],
        blueprint_root=blueprint_root,
        exclusion_manifest=blueprint_root / "POLICIES" / "REGISTRY_NORMALIZATION_EXCLUSIONS.yaml",
        source_ref="HEAD",
    )

    assert report.preconditions_met is False
    assert report.precondition_issues
    assert report.swap_completed is False
    assert not report.written_targets
    assert report.post_write_reconcile is None

    after_state, issues = read_registry_state(blueprint_root)
    assert after_state is not None
    assert not issues
    assert after_state.snapshot_hash == before_hash


def _prepare_registry_workspace(blueprint_root: Path) -> None:
    entries_dir = blueprint_root / "REGISTRIES" / "entries"
    entries_dir.mkdir(parents=True, exist_ok=True)
    (blueprint_root / "POLICIES").mkdir(parents=True, exist_ok=True)
    (blueprint_root / "POLICIES" / "REGISTRY_NORMALIZATION_EXCLUSIONS.yaml").write_text(
        "version: '0.1'\nintentionally_unplaced: []\n",
        encoding="utf-8",
    )
    (blueprint_root / "REGISTRIES" / "allocators.yaml").write_text(
        """id: REGISTRY-GOV-0001
title: OVIS Metadata Allocators
type: REGISTRY
status: active
authority: canonical
version: 0.1
layer: blueprint
domain: gov
repo: ovis-blueprint
path: REGISTRIES/allocators.yaml
owner: Owen Vitae
created: 2026-03-21
last_updated: 2026-03-21
registry: ovis-blueprint/REGISTRIES/entries/REGISTRY-GOV-0001.yaml
families:
  MANIFEST-GOV:
    next_number: 4
    retired_ids: []
""",
        encoding="utf-8",
    )
    for identifier, repo, title, layer in (
        ("MANIFEST-GOV-0001", "ovis-blueprint", "Blueprint Metadata Workflow", "blueprint"),
        ("MANIFEST-GOV-0002", "ovis-runtime", "Runtime Metadata Workflow", "runtime"),
        ("MANIFEST-GOV-0003", "ovis-knowledge", "Knowledge Metadata Workflow", "knowledge"),
    ):
        (entries_dir / f"{identifier}.yaml").write_text(
            f"""id: {identifier}
title: {title}
type: MANIFEST
status: active
authority: operational
version: '0.1'
layer: {layer}
domain: gov
repo: {repo}
path: .github/workflows/ovis-metadata.yml
owner: Owen Vitae
created: '2026-03-21'
last_updated: '2026-03-21'
registry: ovis-blueprint/REGISTRIES/entries/{identifier}.yaml
""",
            encoding="utf-8",
        )
    (blueprint_root / "REGISTRIES" / "OVIS_FILE_REGISTRY.yaml").write_text(
        "registry_version: '0.1'\nsource_refs: {}\nallocators: {}\nentries: {}\n",
        encoding="utf-8",
    )


def _write_workflow_parent(repo_root: Path, *, repo: str, identifier: str, title: str, layer: str) -> None:
    workflow_dir = repo_root / ".github" / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    (workflow_dir / "ovis-metadata.yml").write_text(
        """name: ovis-metadata

on:
  pull_request:
  workflow_dispatch:

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo validate
""",
        encoding="utf-8",
    )
    _write_workflow_sidecar_only(
        repo_root,
        repo=repo,
        identifier=identifier,
        title=title,
        layer=layer,
    )


def _write_workflow_sidecar_only(repo_root: Path, *, repo: str, identifier: str, title: str, layer: str) -> None:
    workflow_dir = repo_root / ".github" / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    (workflow_dir / "ovis-metadata.yml.ovis.yaml").write_text(
        f"""id: {identifier}
title: {title}
type: MANIFEST
status: active
authority: operational
version: '0.1'
layer: {layer}
domain: gov
repo: {repo}
path: .github/workflows/ovis-metadata.yml
owner: Owen Vitae
created: '2026-03-21'
last_updated: '2026-03-21'
registry: ovis-blueprint/REGISTRIES/entries/{identifier}.yaml
module_id: MOD-META-SCHEMA-POLICY-0001
module_slug: meta_schema_policy
system_id: SYS-METADATA-0001
system_slug: metadata_system
""",
        encoding="utf-8",
    )


def _git_init(repo_root: Path) -> None:
    subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "codex@example.com"], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Codex"], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_root, check=True, capture_output=True)
