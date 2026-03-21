# ---
# id: MODULE-RUNTIME-0008
# title: Session Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: runtime
# repo: ovis-runtime
# path: src/ovis_responses_runtime/session.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-RUNTIME-0008.yaml
# module_id: MOD-RUNTIME-GATEWAY-0001
# module_slug: runtime_gateway
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
"""Governed session mode surfaces for the Responses runtime scaffold."""

from __future__ import annotations

from enum import StrEnum


class SessionMode(StrEnum):
    """Session-mode postures aligned with ADR-004."""

    ZDR_FIRST = "zdr-first"
    DURABLE_OPTIONAL = "durable-optional"
    DURABLE_PROHIBITED = "durable-prohibited"


def default_session_config() -> "RuntimeSessionConfig":
    """Return the canonical default governed session posture."""

    from .config import RuntimeSessionConfig

    return RuntimeSessionConfig(
        session_mode=SessionMode.ZDR_FIRST,
        store_enabled=False,
        durable_state_allowed=False,
    )
