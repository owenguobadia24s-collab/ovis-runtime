# ---
# id: TEST-COMPACTION-0002
# title: Test Compaction Hooks Test
# type: TEST
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: compaction
# repo: ovis-runtime
# path: tests/test_compaction_hooks.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/TEST-COMPACTION-0002.yaml
# module_id: MOD-BRANCH-COMPACTION-0001
# module_slug: branch_compaction
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
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
        branch_id="br_001",
        root_signal_id="sig_001",
        current_state_ref="state/branch_001.json",
        latest_compaction_id=None,
        status="open",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _record() -> CompactionRecord:
    return CompactionRecord(
        compaction_id="cmp_001",
        branch_id="br_001",
        source_range="events:1-10",
        compacted_state_ref="state/compactions/cmp_001.json",
        preserved_reference_index=(
            ObjectRef(object_type=ObjectType.SIGNAL, object_id="sig_001"),
        ),
        created_at=datetime.now(UTC),
    )


def test_compaction_created_event_uses_root_construction_when_no_parent() -> None:
    event = build_compaction_created_event(
        record=_record(),
        branch=_branch(),
        context=CompactionHookContext(
            correlation_id="corr_001",
            actor_type="system",
            actor_id="ovis",
            created_at=datetime.now(UTC),
        ),
        payload_inline={"artifact_path": "state/compactions/cmp_001.json"},
    )

    assert isinstance(event, Event)
    assert event.event_type == "compaction.created"
    assert event.parent_event_id is None
    assert str(event.event_id).startswith("evt_")


def test_compaction_created_event_uses_child_linkage_with_parent_event() -> None:
    event = build_compaction_created_event(
        record=_record(),
        branch=_branch(),
        context=CompactionHookContext(
            correlation_id="corr_001",
            actor_type="system",
            actor_id="ovis",
            created_at=datetime.now(UTC),
            parent_event_id="evt_parent",
        ),
        payload_inline={"artifact_path": "state/compactions/cmp_001.json"},
    )

    assert isinstance(event, Event)
    assert event.event_type == "compaction.created"
    assert event.parent_event_id == "evt_parent"


def test_compaction_hooks_accept_placeholder_event_writer() -> None:
    hooks = CompactionHooks(event_writer=PlaceholderAppendOnlyEventWriter())

    assert hooks.event_writer is not None
