from datetime import UTC, datetime
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_branch_compaction import (  # noqa: E402
    CompactedStateOutput,
    CompactionRequest,
    CompactionResponse,
    CompactionTriggerClass,
    PreservedReferenceIndex,
    is_compaction_request_valid,
    is_compaction_response_valid,
    validate_compaction_request,
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


def _index_with_root() -> PreservedReferenceIndex:
    return PreservedReferenceIndex(
        references=(ObjectRef(object_type=ObjectType.SIGNAL, object_id="sig-001"),)
    )


def test_compaction_request_with_root_signal_is_valid() -> None:
    request = CompactionRequest(
        branch=_branch(),
        trigger=CompactionTriggerClass.BEFORE_ARCHIVAL,
        source_range="events:1-10",
        correlation_id="corr-001",
        preserved_reference_index=_index_with_root(),
    )

    validate_compaction_request(request)
    assert is_compaction_request_valid(request)


def test_compaction_request_missing_root_signal_fails() -> None:
    request = CompactionRequest(
        branch=_branch(),
        trigger=CompactionTriggerClass.BEFORE_ARCHIVAL,
        source_range="events:1-10",
        correlation_id="corr-001",
        preserved_reference_index=PreservedReferenceIndex(
            references=(ObjectRef(object_type=ObjectType.WORK_OBJECT, object_id="wo-001"),)
        ),
    )

    with pytest.raises(ValueError):
        validate_compaction_request(request)

    assert not is_compaction_request_valid(request)


def test_compaction_response_mismatch_fails_validation() -> None:
    branch = _branch()
    response = CompactionResponse(
        branch=branch,
        record=CompactionRecord(
            compaction_id="cmp-001",
            branch_id="br-other",
            source_range="events:1-10",
            compacted_state_ref="state/compactions/cmp-001.json",
            preserved_reference_index=_index_with_root().references,
            created_at=datetime.now(UTC),
        ),
        output=CompactedStateOutput(
            compacted_state_ref="state/compactions/cmp-001.json",
            preserved_reference_index=_index_with_root(),
            source_range="events:1-10",
        ),
    )

    assert not is_compaction_response_valid(response)
