# ---
# id: MODULE-COMPACTION-0002
# title: Commands Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: compaction
# repo: ovis-runtime
# path: src/ovis_branch_compaction/commands.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-COMPACTION-0002.yaml
# module_id: MOD-BRANCH-COMPACTION-0001
# module_slug: branch_compaction
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# related_module_ids:
# - MOD-BRANCH-CONTINUITY-0001
# ---
"""Command surfaces for branch compaction scaffolds."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .types import CompactionRequest, CompactionResponse


@dataclass(frozen=True)
class CompactionCommand:
    """Thin wrapper for one compaction request."""

    request: CompactionRequest


class BranchCompactionCommandRunner(Protocol):
    """Command interface compatible with Branch and CompactionRecord."""

    def compact(self, command: CompactionCommand) -> CompactionResponse:
        """Execute one compaction command through a canonical runner."""


class PlaceholderBranchCompactionCommandRunner:
    """Placeholder-only command runner with no compaction execution."""

    def compact(self, command: CompactionCommand) -> CompactionResponse:
        raise NotImplementedError("CJ-005 scaffold only: no compaction execution implementation.")
