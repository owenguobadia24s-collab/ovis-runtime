# ---
# id: MODULE-COMPACTION-0006
# title: Triggers Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: compaction
# repo: ovis-runtime
# path: src/ovis_branch_compaction/triggers.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-COMPACTION-0006.yaml
# module_id: MOD-BRANCH-COMPACTION-0001
# module_slug: branch_compaction
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# related_module_ids:
# - MOD-BRANCH-CONTINUITY-0001
# ---
"""Compaction trigger classes aligned with ADR-006."""

from __future__ import annotations

from enum import StrEnum


class CompactionTriggerClass(StrEnum):
    """Canonical trigger classes for branch compaction."""

    BEFORE_ARCHIVAL = "before-archival"
    BEFORE_FORK = "before-fork"
    EXECUTION_MILESTONE = "execution-milestone"
    HISTORY_NOISE = "history-noise"
    RUNTIME_CONTEXT_LIMIT = "runtime-context-limit"
    OPERATOR_REQUEST = "operator-request"
    SYSTEM_POLICY = "system-policy"
