"""Shared scaffold types for the OVIS tool gateway."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Mapping

SideEffectClass = Literal[
    "read-only",
    "state-write",
    "local-exec",
    "external-bridge",
    "approval-required",
]

PolicyDisposition = Literal["allow", "deny", "defer"]
RiskClass = Literal["R0", "R1", "R2", "R3", "R4"]
ExecutionStatus = Literal["placeholder", "success", "blocked", "error"]
IdempotencyOutcome = Literal["not-evaluated", "accepted", "duplicate", "conflict"]


@dataclass(frozen=True)
class CapabilityDefinition:
    name: str
    version: str
    schema_ref: str
    side_effect_class: SideEffectClass


@dataclass(frozen=True)
class ExecutionRequest:
    capability_name: str
    input_payload: Mapping[str, Any]
    correlation_id: str
    idempotency_key: str
    object_context: Mapping[str, str] = field(default_factory=dict)
    branch_context: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class PolicyDecision:
    disposition: PolicyDisposition
    risk_class: RiskClass
    policy_profile: str
    approval_required: bool
    rationale: str


@dataclass(frozen=True)
class ExecutionResultEnvelope:
    capability_name: str
    execution_status: ExecutionStatus
    correlation_id: str
    idempotency_outcome: IdempotencyOutcome
    policy_disposition: PolicyDisposition
    object_refs: Mapping[str, str] = field(default_factory=dict)
    branch_ref: str | None = None
    output_ref: str | None = None
    result_payload: Any | None = None
    payload_hash: str | None = None
    error_details: str | None = None
