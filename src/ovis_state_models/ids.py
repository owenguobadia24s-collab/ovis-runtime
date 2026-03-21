# ---
# id: MODULE-STATE-0006
# title: Ids Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: state
# repo: ovis-runtime
# path: src/ovis_state_models/ids.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-STATE-0006.yaml
# module_id: MOD-WORK-OBJECT-REGISTRY-0001
# module_slug: work_object_registry
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
"""Compatibility re-exports for shared OVIS IDs."""

from ovis_ids import (
    ApprovalId,
    BranchId,
    BridgeActionId,
    CompactionId,
    CorrelationId,
    EventId,
    ExecuteJobId,
    PlanJobId,
    SignalId,
    WorkObjectId,
    generate_approval_id,
    generate_branch_id,
    generate_compaction_id,
    generate_correlation_id,
    generate_event_id,
    generate_execute_job_id,
    generate_plan_job_id,
    generate_prefixed_id,
    generate_signal_id,
    generate_work_object_id,
)

__all__ = [
    "ApprovalId",
    "BranchId",
    "BridgeActionId",
    "CompactionId",
    "CorrelationId",
    "EventId",
    "ExecuteJobId",
    "PlanJobId",
    "SignalId",
    "WorkObjectId",
    "generate_approval_id",
    "generate_branch_id",
    "generate_compaction_id",
    "generate_correlation_id",
    "generate_event_id",
    "generate_execute_job_id",
    "generate_plan_job_id",
    "generate_prefixed_id",
    "generate_signal_id",
    "generate_work_object_id",
]
