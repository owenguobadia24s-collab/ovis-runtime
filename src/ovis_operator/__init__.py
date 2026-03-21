# ---
# id: MODULE-OPERATOR-0003
# title: Ovis Operator Package Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: operator
# repo: ovis-runtime
# path: src/ovis_operator/__init__.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-OPERATOR-0003.yaml
# module_id: MOD-OPERATOR-SURFACE-0001
# module_slug: operator_surface
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
"""Thin operator CLI package for OVIS."""

from .cli import main

__all__ = ["main"]
