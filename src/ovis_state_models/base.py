# ---
# id: MODULE-STATE-0002
# title: Base Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: state
# repo: ovis-runtime
# path: src/ovis_state_models/base.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-STATE-0002.yaml
# module_id: MOD-WORK-OBJECT-REGISTRY-0001
# module_slug: work_object_registry
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
"""Shared base model configuration for canonical OVIS state models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OvisBaseModel(BaseModel):
    """Base model for canonical OVIS schema objects."""

    model_config = ConfigDict(extra="forbid")


Timestamp = datetime
