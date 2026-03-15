from datetime import UTC, datetime
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_event_log import (  # noqa: E402
    EventAppendReceipt,
    PlaceholderAppendOnlyEventWriter,
    build_root_event,
)


def test_placeholder_writer_is_importable_and_explicitly_unimplemented() -> None:
    writer = PlaceholderAppendOnlyEventWriter()
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

    with pytest.raises(NotImplementedError):
        writer.append(event)

    with pytest.raises(NotImplementedError):
        writer.append_many((event,))


def test_event_append_receipt_shape_is_stable_and_minimal() -> None:
    receipt = EventAppendReceipt(
        event_id="evt-001",
        correlation_id="corr-001",
        object_type="signal",
        object_id="sig-001",
        created_at=datetime.now(UTC),
    )

    assert receipt.event_id == "evt-001"
    assert receipt.object_id == "sig-001"
