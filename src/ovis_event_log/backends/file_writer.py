# ---
# id: MODULE-EVENT-0003
# title: File Writer Module
# type: MODULE
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: event
# repo: ovis-runtime
# path: src/ovis_event_log/backends/file_writer.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/MODULE-EVENT-0003.yaml
# module_id: MOD-EVENT-LOG-0001
# module_slug: event_log
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
"""JSONL file-backed append-only event writer."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
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


class FileEventWriter:
    """Append-only JSONL writer partitioned by event date."""

    def __init__(self, root_dir: str | Path) -> None:
        self._root_dir = Path(root_dir)
        self._last_persisted_record: PersistedEventRecord | None = None

    def append(self, event: Event) -> EventAppendReceipt:
        validate_event_for_append(event)
        record = normalize_event_for_persistence(event)
        record["hash"] = compute_event_hash(record)
        target_path = self._target_path_for_record(record)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        record["sequence"] = self._next_sequence(target_path)
        serialized = json.dumps(record, sort_keys=True, separators=(",", ":"))
        with target_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(serialized)
            handle.write("\n")
        self._last_persisted_record = deepcopy(record)
        return build_event_append_receipt(record)

    def append_many(self, events: Sequence[Event]) -> tuple[EventAppendReceipt, ...]:
        return tuple(self.append(event) for event in events)

    def get_last_persisted_record(self) -> PersistedEventRecord | None:
        """Return the most recently persisted record."""

        return deepcopy(self._last_persisted_record)

    def _target_path_for_record(self, record: PersistedEventRecord) -> Path:
        timestamp = str(record["timestamp"])
        event_date = timestamp.split("T", 1)[0]
        return self._root_dir / "events" / f"{event_date}.jsonl"

    def _next_sequence(self, target_path: Path) -> int:
        if not target_path.exists():
            return 1
        with target_path.open("r", encoding="utf-8") as handle:
            return sum(1 for line in handle if line.strip()) + 1
