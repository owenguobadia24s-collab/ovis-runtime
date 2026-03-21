# ---
# id: MODULE-COMPACTION-0001
# title: Ovis Branch Compaction Package Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: compaction
# repo: ovis-runtime
# path: src/ovis_branch_compaction/__init__.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-COMPACTION-0001.yaml
# module_id: MOD-BRANCH-COMPACTION-0001
# module_slug: branch_compaction
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# related_module_ids:
# - MOD-BRANCH-CONTINUITY-0001
# ---
"""Canonical branch compaction scaffold for OVIS."""

from .commands import (
    BranchCompactionCommandRunner,
    CompactionCommand,
    PlaceholderBranchCompactionCommandRunner,
)
from .executor import BranchCompactionExecutor
from .hooks import CompactionHookContext, CompactionHooks, build_compaction_created_event
from .runtime_compactor import RuntimeBranchCompactor
from .triggers import CompactionTriggerClass
from .types import (
    CompactedStateOutput,
    CompactionRequest,
    CompactionResponse,
    PreservedReferenceIndex,
)
from .validation import (
    is_compaction_request_valid,
    is_compaction_response_valid,
    validate_compaction_request,
    validate_compaction_response,
    validate_preserved_reference_index,
)

__all__ = [
    "BranchCompactionCommandRunner",
    "BranchCompactionExecutor",
    "CompactedStateOutput",
    "CompactionCommand",
    "CompactionHookContext",
    "CompactionHooks",
    "CompactionRequest",
    "CompactionResponse",
    "CompactionTriggerClass",
    "PlaceholderBranchCompactionCommandRunner",
    "PreservedReferenceIndex",
    "RuntimeBranchCompactor",
    "build_compaction_created_event",
    "is_compaction_request_valid",
    "is_compaction_response_valid",
    "validate_compaction_request",
    "validate_compaction_response",
    "validate_preserved_reference_index",
]
