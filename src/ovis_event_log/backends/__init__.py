# ---
# id: MODULE-EVENT-0002
# title: Backends Package Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: event
# repo: ovis-runtime
# path: src/ovis_event_log/backends/__init__.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-EVENT-0002.yaml
# module_id: MOD-EVENT-LOG-0001
# module_slug: event_log
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
"""Concrete append-only event writer backends."""

from .file_writer import FileEventWriter
from .memory_writer import MemoryEventWriter

__all__ = ["FileEventWriter", "MemoryEventWriter"]
