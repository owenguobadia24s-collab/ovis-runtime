from datetime import UTC, datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_branch_compaction import (  # noqa: E402
    CompactedStateOutput,
    CompactionRequest,
    CompactionResponse,
    CompactionTriggerClass,
    PreservedReferenceIndex,
)
from ovis_state_models import Branch, CompactionRecord, ObjectRef, ObjectType  # noqa: E402


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


def test_compaction_types_accept_canonical_models() -> None:
    branch = _branch()
    index = PreservedReferenceIndex(
        references=(ObjectRef(object_type=ObjectType.SIGNAL, object_id="sig-001"),)
    )
    output = CompactedStateOutput(
        compacted_state_ref="state/compactions/cmp-001.json",
        preserved_reference_index=index,
        source_range="events:1-10",
    )
    request = CompactionRequest(
        branch=branch,
        trigger=CompactionTriggerClass.HISTORY_NOISE,
        source_range="events:1-10",
        correlation_id="corr-001",
        preserved_reference_index=index,
    )
    response = CompactionResponse(
        branch=branch,
        record=_record(),
        output=output,
    )

    assert request.branch.branch_id == "br-001"
    assert response.record.compaction_id == "cmp-001"
