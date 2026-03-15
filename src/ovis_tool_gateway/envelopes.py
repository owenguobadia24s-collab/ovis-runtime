"""Result-envelope helpers for the scaffolded tool gateway."""

from __future__ import annotations

from .types import ExecutionResultEnvelope


def placeholder_result(capability_name: str, correlation_id: str) -> ExecutionResultEnvelope:
    """Return a placeholder result envelope for import and wiring checks."""

    return ExecutionResultEnvelope(
        capability_name=capability_name,
        execution_status="placeholder",
        correlation_id=correlation_id,
        idempotency_outcome="not-evaluated",
        policy_disposition="defer",
        error_details="CJ-001 scaffold only: no execution performed.",
    )
