# ---
# id: MODULE-EVENT-0008
# title: Hash Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: event
# repo: ovis-runtime
# path: src/ovis_event_log/hash.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-EVENT-0008.yaml
# module_id: MOD-EVENT-LOG-0001
# module_slug: event_log
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
"""Deterministic hashing helpers for persisted event records."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy

from .writer import PersistedEventRecord


def compute_event_hash(event_dict: PersistedEventRecord) -> str:
    """Compute the canonical SHA-256 hash for a normalized event record."""

    hash_input = deepcopy(event_dict)
    hash_input.pop("hash", None)
    hash_input.pop("sequence", None)
    serialized = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
