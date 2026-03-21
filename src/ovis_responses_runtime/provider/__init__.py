# ---
# id: MODULE-RUNTIME-0006
# title: Provider Package Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: runtime
# repo: ovis-runtime
# path: src/ovis_responses_runtime/provider/__init__.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-RUNTIME-0006.yaml
# module_id: MOD-RUNTIME-GATEWAY-0001
# module_slug: runtime_gateway
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
"""Provider adapters for canonical runtime invocation."""

from .openai_responses_adapter import OpenAIProviderResult, OpenAIResponsesProviderAdapter

__all__ = ["OpenAIProviderResult", "OpenAIResponsesProviderAdapter"]
