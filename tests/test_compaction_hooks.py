from datetime import UTC, datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_branch_compaction import (  # noqa: E402
    CompactionHookContext,
    CompactionHooks,
    build_compaction_created_event,
)
from ovis_event_log import PlaceholderAppendOnlyEventWriter  # noqa: E402
from ovis_state_models import Branch, CompactionRecord, Event, ObjectRef, ObjectType  # noqa: E402


def _branch() -> Branch:
    return Branch(
        branch_id="br-001",
        root_signal_id="sig-001",
        current_state_ref="state/branch-001.json",
        latest_compaction_id=None,
        status="active",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _record() -> CompactionRecord:
    return CompactionRecord(
        compaction_id="cmp-001",
        branch_id="br-001",
        source_range="events:1-10",
        compacted_state_ref="state/compactions/cmp-001.json",
        preserved_reference_index=(
            ObjectRef(object_type=ObjectType.SIGNAL, object_id="sig-001"),
        ),
        created_at=datetime.now(UTC),
    )


def test_compaction_created_event_uses_root_construction_when_no_parent() -> None:
    event = build_compaction_created_event(
        record=_record(),
        branch=_branch(),
        context=CompactionHookContext(
            correlation_id="corr-001",
            actor_type="system",
            actor_id="ovis",
            created_at=datetime.now(UTC),
        ),
    )

    assert isinstance(event, Event)
    assert event.event_type == "compaction.created"
    assert event.parent_event_id is None


def test_compaction_created_event_uses_child_linkage_with_parent_event() -> None:
    event = build_compaction_created_event(
        record=_record(),
        branch=_branch(),
        context=CompactionHookContext(
            correlation_id="corr-001",
            actor_type="system",
            actor_id="ovis",
            created_at=datetime.now(UTC),
            parent_event_id="evt-parent",
        ),
    )

    assert isinstance(event, Event)
    assert event.event_type == "compaction.created"
    assert event.parent_event_id == "evt-parent"


def test_compaction_hooks_accept_placeholder_event_writer() -> None:
    hooks = CompactionHooks(event_writer=PlaceholderAppendOnlyEventWriter())

    assert hooks.event_writer is not None
