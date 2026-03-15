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
