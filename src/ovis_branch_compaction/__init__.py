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
