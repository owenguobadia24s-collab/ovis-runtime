"""Explicit continuation helpers for the runtime scaffold."""

from __future__ import annotations

from .types import RuntimeContinuationRef


def build_root_continuation(branch_id: str, correlation_id: str) -> RuntimeContinuationRef:
    """Build a root continuation anchor with no previous response."""

    return RuntimeContinuationRef(
        previous_response_id=None,
        branch_id=branch_id,
        correlation_id=correlation_id,
    )


def build_chained_continuation(
    previous_response_id: str,
    branch_id: str,
    correlation_id: str,
) -> RuntimeContinuationRef:
    """Build an explicit chained continuation reference."""

    return RuntimeContinuationRef(
        previous_response_id=previous_response_id,
        branch_id=branch_id,
        correlation_id=correlation_id,
    )


def has_explicit_continuation(ref: RuntimeContinuationRef | None) -> bool:
    """Return whether a continuation reference is explicitly chained."""

    return bool(ref and ref.previous_response_id)
