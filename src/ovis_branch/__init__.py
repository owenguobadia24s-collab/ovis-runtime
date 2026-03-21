# ---
# id: MODULE-BRANCH-0001
# title: Ovis Branch Package Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: branch
# repo: ovis-runtime
# path: src/ovis_branch/__init__.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-BRANCH-0001.yaml
# module_id: MOD-BRANCH-CONTINUITY-0001
# module_slug: branch_continuity
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# related_module_ids:
# - MOD-EVENT-LOG-0001
# ---
"""Canonical branch lifecycle package."""

from .lifecycle import BranchLifecycleManager
from .store import BranchStore, InMemoryBranchStore, JsonFileBranchStore
from .types import BranchEventReference, BranchState, BranchStatus, CreateBranchInput

__all__ = [
    "BranchEventReference",
    "BranchLifecycleManager",
    "BranchState",
    "BranchStatus",
    "BranchStore",
    "CreateBranchInput",
    "InMemoryBranchStore",
    "JsonFileBranchStore",
]
