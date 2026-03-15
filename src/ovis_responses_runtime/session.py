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
