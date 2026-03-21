# ---
# id: TEST-EVENT-0005
# title: Test Event Writer File Test
# type: TEST
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: event
# repo: ovis-runtime
# path: tests/test_event_writer_file.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/TEST-EVENT-0005.yaml
# module_id: MOD-EVENT-LOG-0001
# module_slug: event_log
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
import json
from datetime import UTC, datetime
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_event_log import FileEventWriter, emit_event  # noqa: E402
from ovis_state_models import ActorType, Event, EventType, ObjectType  # noqa: E402


def _event(event_id: str, correlation_id: str = "corr_001", branch_id: str = "br_001") -> Event:
    return Event(
        event_id=event_id,
        event_type=EventType.SIGNAL_CREATED,
        correlation_id=correlation_id,
        object_type=ObjectType.SIGNAL,
        object_id="sig_001",
        branch_id=branch_id,
        actor_type=ActorType.SYSTEM,
        actor_id="ovis",
        payload_ref="payloads/signal-001.json",
        created_at=datetime(2026, 3, 15, 12, 0, tzinfo=UTC),
    )


def test_file_writer_persists_deterministic_jsonl_records(tmp_path: Path) -> None:
    writer = FileEventWriter(tmp_path)

    first = emit_event(_event("evt_001"), writer)
    second = emit_event(_event("evt_002"), writer)

    output_path = tmp_path / "events" / "2026-03-15.jsonl"
    lines = output_path.read_text(encoding="utf-8").splitlines()

    assert output_path.exists()
    assert len(lines) == 2
    assert first["sequence"] == 1
    assert second["sequence"] == 2

    first_line = json.loads(lines[0])
    assert first_line["event_id"] == "evt_001"
    assert first_line["timestamp"] == "2026-03-15T12:00:00+00:00"
    assert first_line["payload"]["actor_id"] == "ovis"
    assert lines[0] == json.dumps(first_line, sort_keys=True, separators=(",", ":"))


def test_file_writer_rejects_noncanonical_prefixes(tmp_path: Path) -> None:
    writer = FileEventWriter(tmp_path)

    with pytest.raises(ValueError):
        emit_event(_event("bad_001"), writer)

    with pytest.raises(ValueError):
        emit_event(_event("evt_003", correlation_id="bad_003"), writer)

    with pytest.raises(ValueError):
        emit_event(_event("evt_004", branch_id="bad_004"), writer)
