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
