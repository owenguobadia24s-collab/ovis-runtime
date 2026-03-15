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
    correlation_id: str
    preserved_reference_index: PreservedReferenceIndex
    parent_event_id: str | None = None


@dataclass(frozen=True)
class CompactionResponse:
    """Canonical response surface for a branch compaction operation."""

    branch: Branch
    record: CompactionRecord
    output: CompactedStateOutput
