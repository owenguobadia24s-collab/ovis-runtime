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
