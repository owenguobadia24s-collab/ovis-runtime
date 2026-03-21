# ---
# id: TEST-EVENT-0007
# title: Test Event Writer Memory Test
# type: TEST
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: event
# repo: ovis-runtime
# path: tests/test_event_writer_memory.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/TEST-EVENT-0007.yaml
# module_id: MOD-EVENT-LOG-0001
# module_slug: event_log
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
from datetime import UTC, datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_event_log import MemoryEventWriter, emit_event  # noqa: E402
from ovis_state_models import Event, EventType, ObjectType, ActorType  # noqa: E402


def _event(event_id: str, created_at: datetime | None = None) -> Event:
    return Event(
        event_id=event_id,
        event_type=EventType.SIGNAL_CREATED,
        correlation_id="corr_001",
        object_type=ObjectType.SIGNAL,
        object_id="sig_001",
        branch_id="br_001",
        actor_type=ActorType.SYSTEM,
        actor_id="ovis",
        payload_ref="payloads/signal-001.json",
        created_at=created_at or datetime.now(UTC),
    )


def test_memory_writer_appends_normalized_records_with_sequence_and_hash() -> None:
    writer = MemoryEventWriter()

    first = emit_event(_event("evt_001"), writer)
    second = emit_event(_event("evt_002"), writer)

    records = writer.records()

    assert len(records) == 2
    assert first["sequence"] == 1
    assert second["sequence"] == 2
    assert isinstance(first["hash"], str)
    assert first["event_id"] == "evt_001"
    assert first["payload"]["object_type"] == "signal"


def test_memory_writer_hash_is_deterministic_before_sequence_assignment() -> None:
    timestamp = datetime(2026, 3, 15, 12, 0, tzinfo=UTC)
    writer_one = MemoryEventWriter()
    writer_two = MemoryEventWriter()

    first = emit_event(_event("evt_001", created_at=timestamp), writer_one)
    second = emit_event(_event("evt_001", created_at=timestamp), writer_two)

    assert first["hash"] == second["hash"]
