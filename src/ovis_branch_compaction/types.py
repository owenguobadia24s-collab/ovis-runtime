# ---
# id: MODULE-COMPACTION-0007
# title: Types Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: compaction
# repo: ovis-runtime
# path: src/ovis_branch_compaction/types.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-COMPACTION-0007.yaml
# module_id: MOD-BRANCH-COMPACTION-0001
# module_slug: branch_compaction
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# related_module_ids:
# - MOD-BRANCH-CONTINUITY-0001
# ---
"""Request, response, and output structures for branch compaction."""

from __future__ import annotations

from dataclasses import dataclass

from ovis_state_models import Branch, CompactionRecord, ObjectRef

from .triggers import CompactionTriggerClass


@dataclass(frozen=True)
class PreservedReferenceIndex:
    """Thin wrapper for preserved canonical references."""

    references: tuple[ObjectRef, ...]


@dataclass(frozen=True)
class CompactedStateOutput:
    """Output descriptor for the governed compacted state artifact."""

    compacted_state_ref: str
    preserved_reference_index: PreservedReferenceIndex
    source_range: str


@dataclass(frozen=True)
class CompactionRequest:
    """Canonical request surface for a branch compaction operation."""

    branch: Branch
    trigger: CompactionTriggerClass
    source_range: str
    preserved_reference_index: PreservedReferenceIndex
    correlation_id: str | None = None
    parent_event_id: str | None = None


@dataclass(frozen=True)
class CompactionResponse:
    """Canonical response surface for a branch compaction operation."""

    branch: Branch
    record: CompactionRecord
    output: CompactedStateOutput
