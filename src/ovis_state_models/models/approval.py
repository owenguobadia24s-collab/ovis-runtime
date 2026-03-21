# ---
# id: MODULE-STATE-0008
# title: Approval Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: state
# repo: ovis-runtime
# path: src/ovis_state_models/models/approval.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-STATE-0008.yaml
# module_id: MOD-WORK-OBJECT-REGISTRY-0001
# module_slug: work_object_registry
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
"""Canonical Approval model."""

from __future__ import annotations

from ..base import OvisBaseModel, Timestamp
from ..enums import ApprovalDecision, ObjectType, PolicyProfile, RiskClass
from ..ids import ApprovalId


class Approval(OvisBaseModel):
    approval_id: ApprovalId
    target_object_type: ObjectType
    target_object_id: str
    decision: ApprovalDecision
    rationale: str
    reviewer_id: str
    risk_class: RiskClass
    policy_profile: PolicyProfile
    approval_scope: str
    expires_at: Timestamp | None = None
    created_at: Timestamp
