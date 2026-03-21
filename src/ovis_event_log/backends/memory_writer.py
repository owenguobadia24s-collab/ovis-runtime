# ---
# id: MODULE-EVENT-0004
# title: Memory Writer Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: event
# repo: ovis-runtime
# path: src/ovis_event_log/backends/memory_writer.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-EVENT-0004.yaml
# module_id: MOD-EVENT-LOG-0001
# module_slug: event_log
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
"""In-memory append-only event writer for tests and local verification."""

from __future__ import annotations

from copy import deepcopy
from collections.abc import Sequence

from ovis_state_models import Event

from ..hash import compute_event_hash
from ..validation import validate_event_for_append
from ..writer import (
    EventAppendReceipt,
    PersistedEventRecord,
    build_event_append_receipt,
    normalize_event_for_persistence,
)


class MemoryEventWriter:
    """Append-only in-memory writer using the persisted record projection."""

    def __init__(self) -> None:
        self._records: list[PersistedEventRecord] = []
        self._last_persisted_record: PersistedEventRecord | None = None

    def append(self, event: Event) -> EventAppendReceipt:
        validate_event_for_append(event)
        record = normalize_event_for_persistence(event)
        record["hash"] = compute_event_hash(record)
        record["sequence"] = len(self._records) + 1
        self._records.append(record)
        self._last_persisted_record = deepcopy(record)
        return build_event_append_receipt(record)

    def append_many(self, events: Sequence[Event]) -> tuple[EventAppendReceipt, ...]:
        return tuple(self.append(event) for event in events)

    def records(self) -> tuple[PersistedEventRecord, ...]:
        """Return a read-only snapshot of persisted records."""

        return tuple(deepcopy(record) for record in self._records)

    def get_last_persisted_record(self) -> PersistedEventRecord | None:
        """Return the most recently persisted record."""

        return deepcopy(self._last_persisted_record)
