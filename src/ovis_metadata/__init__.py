# ---
# id: MODULE-GOV-0001
# title: OVIS Metadata Package
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: gov
# repo: ovis-runtime
# path: src/ovis_metadata/__init__.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-GOV-0001.yaml
# ---
"""Workspace metadata validation and reconciliation helpers."""

from .parser import parse_metadata_file
from .reconciler import reconcile_workspace
from .scanner import scan_workspace
from .scaffold import init_file

__all__ = [
    "init_file",
    "parse_metadata_file",
    "reconcile_workspace",
    "scan_workspace",
]