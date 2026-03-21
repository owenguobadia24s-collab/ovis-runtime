# ---
# id: MODULE-GOV-0013
# title: OVIS Metadata Git Source
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: gov
# repo: ovis-runtime
# path: src/ovis_metadata/source.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-GOV-0013.yaml
# ---
"""Git-backed source access for committed metadata reconciliation."""

from __future__ import annotations

from pathlib import Path
import subprocess


class GitRefSource:
    """Read committed repository content from a stable git ref."""

    def __init__(self, repo_root: Path, ref: str = "HEAD") -> None:
        self.repo_root = repo_root
        self.ref = ref
        self._text_cache: dict[str, str | None] = {}
        self._tracked_files: list[str] | None = None
        self._resolved_ref: str | None = None

    def resolve_ref(self) -> str:
        if self._resolved_ref is None:
            result = self._run_git("rev-parse", self.ref)
            self._resolved_ref = result.stdout.strip()
        return self._resolved_ref

    def list_tracked_files(self) -> list[str]:
        if self._tracked_files is None:
            result = self._run_git("ls-tree", "-r", "--name-only", self.ref)
            self._tracked_files = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return list(self._tracked_files)

    def read_text(self, relative_path: str) -> str | None:
        normalized = relative_path.replace("\\", "/")
        if normalized in self._text_cache:
            return self._text_cache[normalized]

        try:
            result = self._run_git("show", f"{self.ref}:{normalized}")
        except subprocess.CalledProcessError:
            self._text_cache[normalized] = None
            return None

        self._text_cache[normalized] = result.stdout
        return result.stdout

    def _run_git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=self.repo_root,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
