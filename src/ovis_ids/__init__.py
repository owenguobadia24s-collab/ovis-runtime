# ---
# id: MODULE-IDS-0001
# title: Ovis Ids Package Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: ids
# repo: ovis-runtime
# path: src/ovis_ids/__init__.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-IDS-0001.yaml
# module_id: MOD-WORK-OBJECT-REGISTRY-0001
# module_slug: work_object_registry
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# related_module_ids:
# - MOD-BRANCH-CONTINUITY-0001
# - MOD-EVENT-LOG-0001
# ---
"""Authoritative shared ID aliases and generators for OVIS."""

from __future__ import annotations

from typing import NewType
from uuid import uuid4

SignalId = NewType("SignalId", str)
WorkObjectId = NewType("WorkObjectId", str)
PlanJobId = NewType("PlanJobId", str)
ApprovalId = NewType("ApprovalId", str)
ExecuteJobId = NewType("ExecuteJobId", str)
EventId = NewType("EventId", str)
BridgeActionId = NewType("BridgeActionId", str)
BranchId = NewType("BranchId", str)
CompactionId = NewType("CompactionId", str)
CorrelationId = NewType("CorrelationId", str)


def generate_prefixed_id(prefix: str) -> str:
    """Generate a canonical prefixed OVIS ID using a lowercase UUID4 suffix."""

    return f"{prefix}{uuid4()}"


def generate_signal_id() -> SignalId:
    return SignalId(generate_prefixed_id("sig_"))


def generate_work_object_id() -> WorkObjectId:
    return WorkObjectId(generate_prefixed_id("wo_"))


def generate_plan_job_id() -> PlanJobId:
    return PlanJobId(generate_prefixed_id("job_plan_"))


def generate_approval_id() -> ApprovalId:
    return ApprovalId(generate_prefixed_id("approval_"))


def generate_execute_job_id() -> ExecuteJobId:
    return ExecuteJobId(generate_prefixed_id("job_execute_"))


def generate_event_id() -> EventId:
    return EventId(generate_prefixed_id("evt_"))


def generate_branch_id() -> BranchId:
    return BranchId(generate_prefixed_id("br_"))


def generate_compaction_id() -> CompactionId:
    return CompactionId(generate_prefixed_id("cmp_"))


def generate_correlation_id() -> CorrelationId:
    return CorrelationId(generate_prefixed_id("corr_"))


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
