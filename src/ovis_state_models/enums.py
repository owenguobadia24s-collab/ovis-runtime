"""Canonical enums for OVIS state models."""

from __future__ import annotations

from enum import StrEnum


class ObjectType(StrEnum):
    SIGNAL = "signal"
    WORK_OBJECT = "work_object"
    PLAN_JOB = "plan_job"
    APPROVAL = "approval"
    EXECUTE_JOB = "execute_job"
    EVENT = "event"
    BRIDGE_ACTION = "bridge_action"
    BRANCH = "branch"
    COMPACTION_RECORD = "compaction_record"


class ActorType(StrEnum):
    HUMAN = "human"
    SYSTEM = "system"
    MODEL = "model"
    TOOL = "tool"
    BRIDGE = "bridge"


class WorkObjectStatus(StrEnum):
    INBOX = "inbox"
    ROUTED = "routed"
    PLANNING = "planning"
    AWAITING_REVIEW = "awaiting_review"
    APPROVED = "approved"
    EXECUTING = "executing"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class PlanJobStatus(StrEnum):
    DRAFT = "draft"
    READY_FOR_REVIEW = "ready_for_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class ApprovalDecision(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    REVISE = "revise"
    DEFER = "defer"


class ExecuteJobStatus(StrEnum):
    DRAFT = "draft"
    PLANNED = "planned"
    READY = "ready"
    RUNNING = "running"
    REVIEW = "review"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BridgeActionStatus(StrEnum):
    PENDING = "pending"
    DISPATCHED = "dispatched"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RiskClass(StrEnum):
    R0 = "R0"
    R1 = "R1"
    R2 = "R2"
    R3 = "R3"
    R4 = "R4"


class PolicyProfile(StrEnum):
    READ_ONLY = "read-only"
    PATCH_ONLY = "patch-only"
    LOCAL_EXEC = "local-exec"
    NETWORK_ESCALATED = "network-escalated"
    HUMAN_APPROVED = "human-approved"


class SideEffectClass(StrEnum):
    READ_ONLY = "read-only"
    STATE_WRITE = "state-write"
    LOCAL_EXEC = "local-exec"
    EXTERNAL_BRIDGE = "external-bridge"
    APPROVAL_REQUIRED = "approval-required"


class EventType(StrEnum):
    SIGNAL_CREATED = "signal.created"
    SIGNAL_COMPRESSED = "signal.compressed"
    WORK_OBJECT_CREATED = "work_object.created"
    WORK_OBJECT_UPDATED = "work_object.updated"
    PLAN_JOB_CREATED = "plan_job.created"
    APPROVAL_RECORDED = "approval.recorded"
    EXECUTE_JOB_CREATED = "execute_job.created"
    EXECUTE_JOB_STATUS_CHANGED = "execute_job.status_changed"
    BRIDGE_ACTION_DISPATCHED = "bridge_action.dispatched"
    BRIDGE_ACTION_COMPLETED = "bridge_action.completed"
    BRIDGE_ACTION_FAILED = "bridge_action.failed"
    COMPACTION_CREATED = "compaction.created"
    RUNTIME_REQUESTED = "runtime.requested"
    RUNTIME_RESPONSE_RECEIVED = "runtime.response_received"
    RUNTIME_ERROR = "runtime.error"
    CAPABILITY_REQUESTED = "capability.requested"
    CAPABILITY_COMPLETED = "capability.completed"
    CAPABILITY_ERROR = "capability.error"
