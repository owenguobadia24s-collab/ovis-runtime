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
from ovis_metadata.reconciler import reconcile_workspace  # noqa: E402
from ovis_metadata.scanner import scan_workspace  # noqa: E402
from ovis_metadata.schema import validate_item  # noqa: E402
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


def test_reconcile_workspace_updates_split_registry(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    blueprint_root = workspace_root / "ovis-blueprint"
    runtime_root = workspace_root / "ovis-runtime"
    entries_dir = blueprint_root / "REGISTRIES" / "entries"
    entries_dir.mkdir(parents=True)
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

    result = reconcile_workspace([runtime_root], blueprint_root=blueprint_root)
    assert not any(issue.severity == "ERROR" for issue in result.issues)
    assert "DOC-REPO-ROLE-0001" in result.added_ids
    assert (entries_dir / "DOC-REPO-ROLE-0001.yaml").exists()
    assert (blueprint_root / "REGISTRIES" / "OVIS_FILE_REGISTRY.yaml").exists()


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


def test_scan_workspace_ignores_deleted_tracked_files(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    stale = repo_root / "stale.yaml"
    stale.write_text("placeholder: true\n", encoding="utf-8")
    _git_init(repo_root)
    stale.unlink()

    report = scan_workspace([repo_root])
    assert report.complete is True
    assert all("stale.yaml" not in path for path in report.scanned_files)


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


def _git_init(repo_root: Path) -> None:
    subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=repo_root, check=True, capture_output=True)
