# ---
# id: MODULE-COMPACTION-0008
# title: Validation Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: compaction
# repo: ovis-runtime
# path: src/ovis_branch_compaction/validation.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-COMPACTION-0008.yaml
# module_id: MOD-BRANCH-COMPACTION-0001
# module_slug: branch_compaction
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# related_module_ids:
# - MOD-BRANCH-CONTINUITY-0001
# ---
"""Pure validation helpers for branch compaction scaffolds."""

from __future__ import annotations

from ovis_state_models import Branch, ObjectRef, ObjectType

from .types import CompactionRequest, CompactionResponse, PreservedReferenceIndex


def _validate_prefix(field_name: str, value: str, prefix: str) -> None:
    if not value.startswith(prefix):
        raise ValueError(f"{field_name} must use the canonical {prefix} prefix.")


def validate_preserved_reference_index(index: PreservedReferenceIndex, branch: Branch) -> None:
    """Validate minimum preserved-reference continuity requirements."""

    if not index.references:
        raise ValueError("Preserved reference index must contain at least one reference.")

    root_signal_ref = ObjectRef(
        object_type=ObjectType.SIGNAL,
        object_id=branch.root_signal_id,
    )
    if root_signal_ref not in index.references:
        raise ValueError("Preserved reference index must retain the branch root signal.")


def validate_compaction_request(request: CompactionRequest) -> None:
    """Validate a branch compaction request."""

    _validate_prefix("branch.branch_id", str(request.branch.branch_id), "br_")
    if not request.source_range.strip():
        raise ValueError("Compaction request requires a non-empty source_range.")
    if request.correlation_id is not None:
        if not request.correlation_id.strip():
            raise ValueError("Compaction request correlation_id cannot be blank.")
        _validate_prefix("correlation_id", request.correlation_id, "corr_")
    if request.parent_event_id is not None:
        _validate_prefix("parent_event_id", request.parent_event_id, "evt_")
    validate_preserved_reference_index(request.preserved_reference_index, request.branch)


def validate_compaction_response(response: CompactionResponse) -> None:
    """Validate a branch compaction response."""

    _validate_prefix("branch.branch_id", str(response.branch.branch_id), "br_")
    _validate_prefix("record.compaction_id", str(response.record.compaction_id), "cmp_")
    _validate_prefix("record.branch_id", str(response.record.branch_id), "br_")
    if response.record.branch_id != response.branch.branch_id:
        raise ValueError("Compaction response record must match the branch_id.")
    if response.record.compacted_state_ref != response.output.compacted_state_ref:
        raise ValueError("Compacted state ref must match between record and output.")
    if response.record.source_range != response.output.source_range:
        raise ValueError("Source range must match between record and output.")
    if response.record.preserved_reference_index != response.output.preserved_reference_index.references:
        raise ValueError("Preserved reference index must match between record and output.")


def is_compaction_request_valid(request: object) -> bool:
    """Return whether a compaction request passes scaffold validation."""

    try:
        if not isinstance(request, CompactionRequest):
            return False
        validate_compaction_request(request)
    except ValueError:
        return False
    return True


def is_compaction_response_valid(response: object) -> bool:
    """Return whether a compaction response passes scaffold validation."""

    try:
        if not isinstance(response, CompactionResponse):
            return False
        validate_compaction_response(response)
    except ValueError:
        return False
    return True
