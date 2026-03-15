from datetime import UTC, datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_branch import BranchEventReference, BranchState, BranchStatus  # noqa: E402
from ovis_branch_compaction import CompactionTriggerClass, RuntimeBranchCompactor  # noqa: E402
from ovis_state_models import Branch, ObjectType  # noqa: E402


def _branch_state() -> BranchState:
    branch = Branch(
        branch_id="br_001",
        root_signal_id="sig_001",
        current_state_ref="memory://branches/br_001",
        latest_compaction_id=None,
        status=BranchStatus.OPEN,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    event_refs = (
        BranchEventReference(event_id="evt_001", event_type="signal.created", correlation_id="corr_001"),
        BranchEventReference(event_id="evt_002", event_type="work_object.updated", correlation_id="corr_001"),
    )
    return BranchState(
        branch=branch,
        correlation_id="corr_001",
        event_refs=event_refs,
        latest_event=event_refs[-1],
    )


def test_runtime_compactor_produces_deterministic_reduction() -> None:
    created_at = datetime(2026, 3, 15, 12, 0, tzinfo=UTC)
    result = RuntimeBranchCompactor().compact(
        branch_state=_branch_state(),
        trigger=CompactionTriggerClass.HISTORY_NOISE,
        compaction_id="cmp_001",
        created_at=created_at,
        artifact_path="compactions/branch_br_001_compaction_cmp_001.json",
        correlation_id="corr_001",
    )

    assert result.source_range == "events:1-2"
    assert result.source_event_count == 2
    assert result.preserved_reference_index.references[0].object_type == ObjectType.SIGNAL
    assert result.preserved_reference_index.references[0].object_id == "sig_001"
    assert [reference.object_id for reference in result.preserved_reference_index.references[1:]] == [
        "evt_001",
        "evt_002",
    ]
    assert result.artifact_payload["source_event_count"] == 2
    assert result.artifact_payload["event_refs"][1]["event_id"] == "evt_002"
    assert (
        result.summary
        == "Branch br_001 compacted at 2026-03-15T12:00:00+00:00; status=open; root_signal=sig_001; source_events=2; latest_event=evt_002; trigger=history-noise"
    )
