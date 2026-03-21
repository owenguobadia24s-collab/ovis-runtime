# ---
# id: TEST-COMPACTION-0004
# title: Test Compaction Types Test
# type: TEST
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: compaction
# repo: ovis-runtime
# path: tests/test_compaction_types.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/TEST-COMPACTION-0004.yaml
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
    CompactedStateOutput,
    CompactionRequest,
    CompactionResponse,
    CompactionTriggerClass,
    PreservedReferenceIndex,
)
from ovis_state_models import Branch, CompactionRecord, ObjectRef, ObjectType  # noqa: E402


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


def test_compaction_types_accept_canonical_models() -> None:
    branch = _branch()
    index = PreservedReferenceIndex(
        references=(ObjectRef(object_type=ObjectType.SIGNAL, object_id="sig_001"),)
    )
    output = CompactedStateOutput(
        compacted_state_ref="state/compactions/cmp_001.json",
        preserved_reference_index=index,
        source_range="events:1-10",
    )
    request = CompactionRequest(
        branch=branch,
        trigger=CompactionTriggerClass.HISTORY_NOISE,
        source_range="events:1-10",
        correlation_id="corr_001",
        preserved_reference_index=index,
    )
    response = CompactionResponse(
        branch=branch,
        record=_record(),
        output=output,
    )

    assert request.branch.branch_id == "br_001"
    assert response.record.compaction_id == "cmp_001"
