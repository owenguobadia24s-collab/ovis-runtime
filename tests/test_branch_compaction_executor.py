# ---
# id: TEST-BRANCH-0001
# title: Test Branch Compaction Executor Test
# type: TEST
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: branch
# repo: ovis-runtime
# path: tests/test_branch_compaction_executor.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/TEST-BRANCH-0001.yaml
# module_id: MOD-BRANCH-COMPACTION-0001
# module_slug: branch_compaction
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
import json
from datetime import UTC, datetime
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_branch import BranchEventReference, BranchLifecycleManager, BranchStatus, CreateBranchInput  # noqa: E402
from ovis_branch_compaction import (  # noqa: E402
    BranchCompactionExecutor,
    CompactionHooks,
    CompactionCommand,
    CompactionRequest,
    CompactionTriggerClass,
    PreservedReferenceIndex,
)
from ovis_event_log import MemoryEventWriter  # noqa: E402
from ovis_state_models import Branch, ObjectRef, ObjectType  # noqa: E402


def _manager_with_branch() -> tuple[BranchLifecycleManager, str]:
    manager = BranchLifecycleManager()
    created = manager.create_branch(CreateBranchInput(root_signal_id="sig_001", correlation_id="corr_001"))
    manager.append_event(
        str(created.branch.branch_id),
        BranchEventReference(event_id="evt_001", event_type="signal.created", correlation_id="corr_001"),
    )
    manager.append_event(
        str(created.branch.branch_id),
        BranchEventReference(event_id="evt_002", event_type="work_object.updated", correlation_id="corr_001"),
    )
    return manager, str(created.branch.branch_id)


def test_compaction_executor_writes_artifact_updates_branch_and_emits_event(tmp_path: Path) -> None:
    manager, branch_id = _manager_with_branch()
    writer = MemoryEventWriter()
    executor = BranchCompactionExecutor(
        branch_lifecycle=manager,
        artifact_root=tmp_path / "compactions",
        hooks=CompactionHooks(event_writer=writer),
    )

    response = executor.compact_branch(branch_id, CompactionTriggerClass.HISTORY_NOISE)

    artifact_path = tmp_path / "compactions" / f"branch_{branch_id}_compaction_{response.record.compaction_id}.json"
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    updated_state = manager.get_branch(branch_id)
    records = writer.records()

    assert str(response.record.compaction_id).startswith("cmp_")
    assert response.record.branch_id == branch_id
    assert artifact["branch_id"] == branch_id
    assert artifact["source_range"] == "events:1-2"
    assert artifact["source_event_count"] == 2
    assert [event["event_id"] for event in artifact["event_refs"]] == ["evt_001", "evt_002"]
    assert artifact["preserved_references"][0]["object_id"] == "sig_001"
    assert updated_state.branch.latest_compaction_id == response.record.compaction_id
    assert updated_state.branch.current_state_ref == artifact_path.as_posix()
    assert updated_state.branch.updated_at >= updated_state.branch.created_at
    assert len(records) == 1
    assert records[0]["event_type"] == "compaction.created"
    assert records[0]["payload"]["payload_inline"]["source_event_count"] == 2


def test_compaction_executor_skips_event_when_no_correlation_exists(tmp_path: Path) -> None:
    manager = BranchLifecycleManager()
    created = manager.create_branch(CreateBranchInput(root_signal_id="sig_001"))
    manager.append_event(
        str(created.branch.branch_id),
        BranchEventReference(event_id="evt_001", event_type="signal.created"),
    )
    writer = MemoryEventWriter()
    executor = BranchCompactionExecutor(
        branch_lifecycle=manager,
        artifact_root=tmp_path / "compactions",
        hooks=CompactionHooks(event_writer=writer),
    )

    response = executor.compact_branch(str(created.branch.branch_id), CompactionTriggerClass.HISTORY_NOISE)

    assert response.record.branch_id == created.branch.branch_id
    assert writer.records() == ()


def test_compaction_executor_uses_authoritative_lifecycle_state_for_command_input(tmp_path: Path) -> None:
    manager, branch_id = _manager_with_branch()
    executor = BranchCompactionExecutor(
        branch_lifecycle=manager,
        artifact_root=tmp_path / "compactions",
        hooks=CompactionHooks(),
    )
    stale_branch = Branch(
        branch_id=branch_id,
        root_signal_id="sig_old",
        current_state_ref="memory://stale",
        latest_compaction_id=None,
        status=BranchStatus.CLOSED,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    response = executor.compact(
        CompactionCommand(
            request=CompactionRequest(
                branch=stale_branch,
                trigger=CompactionTriggerClass.HISTORY_NOISE,
                source_range="events:999-999",
                correlation_id="corr_001",
                preserved_reference_index=PreservedReferenceIndex(
                    references=(ObjectRef(object_type=ObjectType.SIGNAL, object_id="sig_old"),)
                ),
            )
        )
    )
    artifact_path = tmp_path / "compactions" / f"branch_{branch_id}_compaction_{response.record.compaction_id}.json"
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))

    assert artifact["root_signal_id"] == "sig_001"
    assert artifact["source_range"] == "events:1-2"


def test_compaction_executor_handles_missing_and_malformed_ids_cleanly(tmp_path: Path) -> None:
    manager = BranchLifecycleManager()
    executor = BranchCompactionExecutor(
        branch_lifecycle=manager,
        artifact_root=tmp_path / "compactions",
        hooks=CompactionHooks(),
    )

    with pytest.raises(KeyError):
        executor.compact_branch("br_missing", CompactionTriggerClass.HISTORY_NOISE)

    with pytest.raises(ValueError):
        executor.compact_branch("bad_001", CompactionTriggerClass.HISTORY_NOISE)

    created = manager.create_branch(CreateBranchInput(root_signal_id="sig_001", correlation_id="corr_001"))
    with pytest.raises(ValueError):
        executor.compact_branch(
            str(created.branch.branch_id),
            CompactionTriggerClass.HISTORY_NOISE,
            parent_event_id="bad_001",
        )


def test_repeated_compactions_receive_distinct_ids(tmp_path: Path) -> None:
    manager, branch_id = _manager_with_branch()
    executor = BranchCompactionExecutor(
        branch_lifecycle=manager,
        artifact_root=tmp_path / "compactions",
        hooks=CompactionHooks(),
    )

    first = executor.compact_branch(branch_id, CompactionTriggerClass.HISTORY_NOISE)
    second = executor.compact_branch(branch_id, CompactionTriggerClass.HISTORY_NOISE)

    assert first.record.compaction_id != second.record.compaction_id
