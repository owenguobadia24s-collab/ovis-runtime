# ---
# id: TEST-BRANCH-0002
# title: Test Branch Lifecycle Test
# type: TEST
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: branch
# repo: ovis-runtime
# path: tests/test_branch_lifecycle.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/TEST-BRANCH-0002.yaml
# module_id: MOD-BRANCH-CONTINUITY-0001
# module_slug: branch_continuity
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
from datetime import UTC, datetime
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_branch import BranchEventReference, BranchLifecycleManager, BranchStatus, CreateBranchInput  # noqa: E402
from ovis_event_log import MemoryEventWriter, build_root_event  # noqa: E402
from ovis_state_models import ActorType, Event, ObjectType, Signal, generate_event_id  # noqa: E402


def _signal() -> Signal:
    return Signal(
        signal_id="sig-001",
        source_type="test",
        source_ref="signal://001",
        raw_input_ref="raw://001",
        compressed_summary="summary",
        extracted_signals=("signal",),
        nuance=None,
        branch_id="br_existing",
        created_at=datetime.now(UTC),
        created_by="tester",
    )


def _event(branch_id: str, correlation_id: str = "corr_001") -> Event:
    return build_root_event(
        event_id=generate_event_id(),
        event_type="signal.created",
        correlation_id=correlation_id,
        object_type=ObjectType.SIGNAL,
        object_id="sig-001",
        branch_id=branch_id,
        actor_type=ActorType.SYSTEM,
        actor_id="tester",
        created_at=datetime.now(UTC),
        payload_inline={"source": "test"},
    )


def test_create_branch_issues_canonical_id_and_can_be_read_back() -> None:
    manager = BranchLifecycleManager()

    created = manager.create_branch(
        CreateBranchInput(root_signal_id="sig-001", correlation_id="corr_001")
    )
    fetched = manager.get_branch(str(created.branch.branch_id))

    assert str(created.branch.branch_id).startswith("br_")
    assert fetched == created
    assert created.branch.status == BranchStatus.OPEN
    assert created.branch.current_state_ref == f"memory://branches/{created.branch.branch_id}"
    assert created.correlation_id == "corr_001"


def test_create_branch_from_signal_derives_root_signal_and_skips_event_emission_without_correlation() -> None:
    writer = MemoryEventWriter()
    manager = BranchLifecycleManager(event_writer=writer)

    created = manager.create_branch(_signal())

    assert created.branch.root_signal_id == "sig-001"
    assert created.correlation_id is None
    assert writer.records() == ()


def test_append_event_preserves_identity_and_append_order() -> None:
    manager = BranchLifecycleManager()
    created = manager.create_branch(
        CreateBranchInput(root_signal_id="sig-001", correlation_id="corr_001")
    )

    first = manager.append_event(
        str(created.branch.branch_id),
        BranchEventReference(event_id="evt_001", event_type="signal.created", correlation_id="corr_001"),
    )
    second = manager.append_event(
        str(created.branch.branch_id),
        BranchEventReference(event_id="evt_002", event_type="work_object.updated", correlation_id="corr_001"),
    )

    assert [event.event_id for event in first.event_refs] == ["evt_001"]
    assert [event.event_id for event in second.event_refs] == ["evt_001", "evt_002"]
    assert second.latest_event is not None
    assert second.latest_event.event_id == "evt_002"
    assert second.branch.updated_at >= created.branch.updated_at


def test_append_canonical_event_updates_branch_state_and_preserves_correlation() -> None:
    manager = BranchLifecycleManager()
    created = manager.create_branch(CreateBranchInput(root_signal_id="sig-001"))

    appended = manager.append_event(str(created.branch.branch_id), _event(str(created.branch.branch_id)))

    assert appended.correlation_id == "corr_001"
    assert appended.latest_event is not None
    assert appended.latest_event.event_type == "signal.created"


def test_close_branch_marks_branch_closed() -> None:
    manager = BranchLifecycleManager()
    created = manager.create_branch(
        CreateBranchInput(root_signal_id="sig-001", correlation_id="corr_001")
    )

    closed = manager.close_branch(str(created.branch.branch_id))

    assert closed.branch.status == BranchStatus.CLOSED
    assert closed.branch.updated_at >= created.branch.updated_at


def test_missing_branch_operations_raise_key_error() -> None:
    manager = BranchLifecycleManager()

    with pytest.raises(KeyError):
        manager.get_branch("br_missing")

    with pytest.raises(KeyError):
        manager.append_event("br_missing", BranchEventReference(event_id="evt_001"))

    with pytest.raises(KeyError):
        manager.close_branch("br_missing")


def test_malformed_ids_raise_value_error() -> None:
    manager = BranchLifecycleManager()
    created = manager.create_branch(CreateBranchInput(root_signal_id="sig-001"))

    with pytest.raises(ValueError):
        manager.get_branch("bad_001")

    with pytest.raises(ValueError):
        manager.append_event(str(created.branch.branch_id), BranchEventReference(event_id="bad_001"))

    with pytest.raises(ValueError):
        manager.create_branch(CreateBranchInput(root_signal_id="sig-001", correlation_id="bad_001"))


def test_append_to_closed_branch_and_reclose_fail_cleanly() -> None:
    manager = BranchLifecycleManager()
    created = manager.create_branch(
        CreateBranchInput(root_signal_id="sig-001", correlation_id="corr_001")
    )
    manager.close_branch(str(created.branch.branch_id))

    with pytest.raises(ValueError):
        manager.append_event(str(created.branch.branch_id), BranchEventReference(event_id="evt_001"))

    with pytest.raises(ValueError):
        manager.close_branch(str(created.branch.branch_id))


def test_correlation_mismatch_on_append_raises_value_error() -> None:
    manager = BranchLifecycleManager()
    created = manager.create_branch(
        CreateBranchInput(root_signal_id="sig-001", correlation_id="corr_001")
    )

    with pytest.raises(ValueError):
        manager.append_event(
            str(created.branch.branch_id),
            BranchEventReference(event_id="evt_001", correlation_id="corr_999"),
        )


def test_lifecycle_events_emit_only_when_correlation_exists_and_writer_is_configured() -> None:
    writer = MemoryEventWriter()
    manager = BranchLifecycleManager(event_writer=writer)
    created = manager.create_branch(
        CreateBranchInput(root_signal_id="sig-001", correlation_id="corr_001")
    )

    manager.append_event(
        str(created.branch.branch_id),
        BranchEventReference(event_id="evt_001", event_type="signal.created", correlation_id="corr_001"),
    )
    manager.close_branch(str(created.branch.branch_id))

    records = writer.records()
    assert [record["event_type"] for record in records] == [
        "branch.created",
        "branch.event_appended",
        "branch.closed",
    ]
    assert all(str(record["event_id"]).startswith("evt_") for record in records)
    assert all(record["branch_id"] == str(created.branch.branch_id) for record in records)
