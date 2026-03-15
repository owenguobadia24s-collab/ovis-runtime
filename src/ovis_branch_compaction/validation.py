"""Pure validation helpers for branch compaction scaffolds."""

from __future__ import annotations

from ovis_state_models import Branch, ObjectRef, ObjectType

from .types import CompactionRequest, CompactionResponse, PreservedReferenceIndex


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

    if not request.source_range.strip():
        raise ValueError("Compaction request requires a non-empty source_range.")
    if not request.correlation_id.strip():
        raise ValueError("Compaction request requires a non-empty correlation_id.")
    validate_preserved_reference_index(request.preserved_reference_index, request.branch)


def validate_compaction_response(response: CompactionResponse) -> None:
    """Validate a branch compaction response."""

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
