# ---
# id: MODULE-RUNTIME-0004
# title: Continuation Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: runtime
# repo: ovis-runtime
# path: src/ovis_responses_runtime/continuation.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-RUNTIME-0004.yaml
# module_id: MOD-RUNTIME-GATEWAY-0001
# module_slug: runtime_gateway
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
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
