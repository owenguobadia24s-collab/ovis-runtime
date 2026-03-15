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
