# ---
# id: MODULE-LOOP-0001
# title: Ovis Loop Package Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: loop
# repo: ovis-runtime
# path: src/ovis_loop/__init__.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-LOOP-0001.yaml
# module_id: MOD-PLANNING-EXECUTION-LOOP-0001
# module_slug: planning_execution_loop
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
"""Thin orchestration layer for one governed recursive branch loop."""

from .runner import RecursiveLoopRunner
from .types import (
    LoopApprovalInput,
    LoopExecutionMode,
    LoopRequest,
    LoopResult,
    LoopSignalInput,
    LoopStage,
)

__all__ = [
    "LoopApprovalInput",
    "LoopExecutionMode",
    "LoopRequest",
    "LoopResult",
    "LoopSignalInput",
    "LoopStage",
    "RecursiveLoopRunner",
]
