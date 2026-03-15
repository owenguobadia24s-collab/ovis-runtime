from datetime import UTC, datetime
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_event_log import build_child_event, build_root_event, validate_parent_child_linkage  # noqa: E402


def test_parent_child_linkage_validation_accepts_valid_lineage() -> None:
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

    validate_parent_child_linkage(parent_event, child_event)


def test_parent_child_linkage_validation_rejects_correlation_mismatch() -> None:
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
    ).model_copy(update={"correlation_id": "corr-override"})

    with pytest.raises(ValueError):
        validate_parent_child_linkage(parent_event, child_event)


def test_parent_child_linkage_validation_rejects_self_parent_reference() -> None:
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
    ).model_copy(update={"parent_event_id": "evt-child"})

    with pytest.raises(ValueError):
        validate_parent_child_linkage(parent_event, child_event)
