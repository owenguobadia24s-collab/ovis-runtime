# ---
# id: MODULE-STATE-0010
# title: Bridge Action Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: state
# repo: ovis-runtime
# path: src/ovis_state_models/models/bridge_action.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-STATE-0010.yaml
# module_id: MOD-WORK-OBJECT-REGISTRY-0001
# module_slug: work_object_registry
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
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
