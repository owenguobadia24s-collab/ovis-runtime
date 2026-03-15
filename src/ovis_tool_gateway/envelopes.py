"""Result-envelope helpers for the scaffolded tool gateway."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

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


def _compute_payload_hash(result_payload: Any) -> str | None:
    try:
        serialized = json.dumps(result_payload, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError):
        return None
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def build_success_envelope(
    *,
    capability_name: str,
    correlation_id: str,
    policy_disposition: str,
    object_refs: Mapping[str, str],
    branch_ref: str | None,
    result_payload: Any,
) -> ExecutionResultEnvelope:
    return ExecutionResultEnvelope(
        capability_name=capability_name,
        execution_status="success",
        correlation_id=correlation_id,
        idempotency_outcome="accepted",
        policy_disposition=policy_disposition,
        object_refs=dict(object_refs),
        branch_ref=branch_ref,
        result_payload=result_payload,
        payload_hash=_compute_payload_hash(result_payload),
    )


def build_blocked_envelope(
    *,
    capability_name: str,
    correlation_id: str,
    policy_disposition: str,
    object_refs: Mapping[str, str],
    branch_ref: str | None,
    error_details: str,
) -> ExecutionResultEnvelope:
    return ExecutionResultEnvelope(
        capability_name=capability_name,
        execution_status="blocked",
        correlation_id=correlation_id,
        idempotency_outcome="not-evaluated",
        policy_disposition=policy_disposition,
        object_refs=dict(object_refs),
        branch_ref=branch_ref,
        error_details=error_details,
    )


def build_error_envelope(
    *,
    capability_name: str,
    correlation_id: str,
    policy_disposition: str,
    object_refs: Mapping[str, str],
    branch_ref: str | None,
    error_details: str,
) -> ExecutionResultEnvelope:
    return ExecutionResultEnvelope(
        capability_name=capability_name,
        execution_status="error",
        correlation_id=correlation_id,
        idempotency_outcome="not-evaluated",
        policy_disposition=policy_disposition,
        object_refs=dict(object_refs),
        branch_ref=branch_ref,
        error_details=error_details,
    )
