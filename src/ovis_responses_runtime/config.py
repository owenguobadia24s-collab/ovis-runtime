"""Runtime adapter configuration structures."""

from __future__ import annotations

from dataclasses import dataclass

from .session import SessionMode


@dataclass(frozen=True)
class RuntimeModelConfig:
    """Minimal model configuration surface for the runtime adapter."""

    model_name: str


@dataclass(frozen=True)
class RuntimeSessionConfig:
    """Governed session configuration for runtime requests."""

    session_mode: SessionMode
    store_enabled: bool
    durable_state_allowed: bool


@dataclass(frozen=True)
class RuntimeAdapterConfig:
    """Top-level configuration for the runtime adapter scaffold."""

    model: RuntimeModelConfig
    session: RuntimeSessionConfig
    emit_events: bool = True
    gateway_integration_enabled: bool = True
