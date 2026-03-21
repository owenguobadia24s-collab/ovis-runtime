# ---
# id: MODULE-STATE-0018
# title: Validators Package Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: state
# repo: ovis-runtime
# path: src/ovis_state_models/validators/__init__.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-STATE-0018.yaml
# module_id: MOD-WORK-OBJECT-REGISTRY-0001
# module_slug: work_object_registry
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
"""Validation helpers for canonical OVIS state models."""

from .transitions import (
    BRIDGE_ACTION_TRANSITIONS,
    EXECUTE_JOB_TRANSITIONS,
    PLAN_JOB_TRANSITIONS,
    WORK_OBJECT_TRANSITIONS,
    is_allowed_transition,
)

__all__ = [
    "BRIDGE_ACTION_TRANSITIONS",
    "EXECUTE_JOB_TRANSITIONS",
    "PLAN_JOB_TRANSITIONS",
    "WORK_OBJECT_TRANSITIONS",
    "is_allowed_transition",
]
