# ---
# id: MODULE-LOOP-0003
# title: Types Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: loop
# repo: ovis-runtime
# path: src/ovis_loop/types.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-LOOP-0003.yaml
# module_id: MOD-PLANNING-EXECUTION-LOOP-0001
# module_slug: planning_execution_loop
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
"""Thin request and result types for the first recursive branch loop."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any, Mapping

from ovis_branch import BranchState
from ovis_branch_compaction import CompactionResponse
from ovis_responses_runtime import RuntimeResponse
from ovis_state_models import (
    Approval,
    PolicyProfile,
    RiskClass,
    Signal,
    ExecuteJob,
    PlanJob,
    WorkObject,
)
from ovis_tool_gateway import ExecutionResultEnvelope


class LoopExecutionMode(StrEnum):
    RUNTIME = "runtime"
    CAPABILITY = "capability"


@dataclass(frozen=True)
class LoopSignalInput:
    source_type: str
    source_ref: str
    raw_input_ref: str | None
    raw_input_hash: str | None
    compressed_summary: str
    extracted_signals: tuple[str, ...] = ()
    nuance: str | None = None
    created_by: str = "ovis_loop"


@dataclass(frozen=True)
class LoopApprovalInput:
    approved: bool
    reviewer_id: str
    rationale: str
    risk_class: RiskClass
    policy_profile: PolicyProfile
    approval_scope: str
    expires_at: datetime | None = None


@dataclass(frozen=True)
class LoopRequest:
    signal: Signal | LoopSignalInput
    objective: str
    branch_id: str | None = None
    correlation_id: str | None = None
    execution_mode: LoopExecutionMode = LoopExecutionMode.RUNTIME
    runtime_input: Mapping[str, Any] | None = None
    capability_name: str | None = None
    capability_payload: Mapping[str, Any] | None = None
    approval: LoopApprovalInput | None = None
    title: str | None = None
    priority: str = "normal"
    owner: str = "ovis_loop"
    compact_after_run: bool = False
    close_branch_after_run: bool = False


class LoopStage(StrEnum):
    INPUT = "input"
    APPROVAL = "approval"
    EXECUTION = "execution"
    COMPACTION = "compaction"


@dataclass(frozen=True)
class LoopResult:
    branch_id: str
    correlation_id: str
    execution_mode: LoopExecutionMode
    success: bool
    execution_succeeded: bool
    approval: Approval
    signal: Signal
    work_object: WorkObject
    plan_job: PlanJob
    execute_job: ExecuteJob | None
    runtime_response: RuntimeResponse | None
    capability_result: ExecutionResultEnvelope | None
    compaction_response: CompactionResponse | None
    branch_state: BranchState
    error_stage: LoopStage | None = None
    error_message: str | None = None
