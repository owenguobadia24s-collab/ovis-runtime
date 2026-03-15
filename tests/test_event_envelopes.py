from datetime import UTC, datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_event_log import build_child_event, build_root_event  # noqa: E402
from ovis_state_models import Event  # noqa: E402


def test_build_root_event_returns_canonical_event() -> None:
    event = build_root_event(
        event_id="evt-001",
        event_type="signal.created",
        correlation_id="corr-001",
        object_type="signal",
        object_id="sig-001",
        branch_id="br-001",
        actor_type="system",
        actor_id="ovis",
        created_at=datetime.now(UTC),
        payload_ref="payloads/signal-001.json",
    )

    assert isinstance(event, Event)
    assert event.parent_event_id is None
    assert event.event_type == "signal.created"


def test_build_child_event_inherits_parent_lineage() -> None:
    parent_event = build_root_event(
        event_id="evt-parent",
        event_type="signal.created",
        correlation_id="corr-001",
        object_type="signal",
        object_id="sig-001",
        branch_id="br-001",
        actor_type="system",
        actor_id="ovis",
        created_at=datetime.now(UTC),
        payload_ref="payloads/signal-001.json",
    )

    child_event = build_child_event(
        parent_event=parent_event,
        event_id="evt-child",
        event_type="work_object.created",
        object_type="work_object",
        object_id="wo-001",
        actor_type="tool",
        actor_id="router",
        created_at=datetime.now(UTC),
        payload_hash="hash-001",
    )

    assert isinstance(child_event, Event)
    assert child_event.correlation_id == parent_event.correlation_id
    assert child_event.branch_id == parent_event.branch_id
    assert child_event.parent_event_id == parent_event.event_id
