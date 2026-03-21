# ---
# id: MODULE-RUNTIME-0003
# title: Config Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: runtime
# repo: ovis-runtime
# path: src/ovis_responses_runtime/config.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-RUNTIME-0003.yaml
# module_id: MOD-RUNTIME-GATEWAY-0001
# module_slug: runtime_gateway
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
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
