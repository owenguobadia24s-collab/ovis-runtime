# ---
# id: TEST-EVENT-0004
# title: Test Event Validation Test
# type: TEST
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: event
# repo: ovis-runtime
# path: tests/test_event_validation.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/TEST-EVENT-0004.yaml
# module_id: MOD-EVENT-LOG-0001
# module_slug: event_log
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
from datetime import UTC, datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_event_log import build_root_event, is_event_append_ready, validate_event_for_append  # noqa: E402


def test_append_validation_accepts_valid_canonical_event() -> None:
    event = build_root_event(
        event_id="evt_001",
        event_type="signal.created",
        correlation_id="corr_001",
        object_type="signal",
        object_id="sig-001",
        branch_id="br_001",
        actor_type="system",
        actor_id="ovis",
        created_at=datetime.now(UTC),
        payload_ref="payloads/signal-001.json",
    )

    validate_event_for_append(event)
    assert is_event_append_ready(event)


def test_append_validation_rejects_non_event_objects() -> None:
    assert not is_event_append_ready(object())


def test_append_validation_rejects_self_parent_reference() -> None:
    event = build_root_event(
        event_id="evt_001",
        event_type="signal.created",
        correlation_id="corr_001",
        object_type="signal",
        object_id="sig-001",
        branch_id="br_001",
        actor_type="system",
        actor_id="ovis",
        created_at=datetime.now(UTC),
        payload_ref="payloads/signal-001.json",
    ).model_copy(update={"parent_event_id": "evt_001"})

    assert not is_event_append_ready(event)
