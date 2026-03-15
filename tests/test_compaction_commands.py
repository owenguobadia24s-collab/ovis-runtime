from datetime import UTC, datetime
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_branch_compaction import (  # noqa: E402
    CompactionCommand,
    CompactionRequest,
    CompactionTriggerClass,
    PlaceholderBranchCompactionCommandRunner,
    PreservedReferenceIndex,
)
from ovis_state_models import Branch, ObjectRef, ObjectType  # noqa: E402


def test_placeholder_branch_compaction_runner_is_explicitly_unimplemented() -> None:
    runner = PlaceholderBranchCompactionCommandRunner()
    command = CompactionCommand(
        request=CompactionRequest(
            branch=Branch(
                branch_id="br-001",
                root_signal_id="sig-001",
                current_state_ref="state/branch-001.json",
                latest_compaction_id=None,
                status="active",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
            trigger=CompactionTriggerClass.HISTORY_NOISE,
            source_range="events:1-10",
            correlation_id="corr-001",
            preserved_reference_index=PreservedReferenceIndex(
                references=(ObjectRef(object_type=ObjectType.SIGNAL, object_id="sig-001"),)
            ),
        )
    )

    with pytest.raises(NotImplementedError):
        runner.compact(command)
