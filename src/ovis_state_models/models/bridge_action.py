"""Canonical BridgeAction model."""

from __future__ import annotations

from ..base import OvisBaseModel, Timestamp
from ..enums import BridgeActionStatus
from ..ids import BridgeActionId, ExecuteJobId


class BridgeAction(OvisBaseModel):
    bridge_action_id: BridgeActionId
    execute_job_id: ExecuteJobId
    target_system: str
    action_type: str
    status: BridgeActionStatus
    request_ref: str | None
    response_ref: str | None
    created_at: Timestamp
    updated_at: Timestamp
