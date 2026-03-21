# ---
# id: TEST-COMPACTION-0001
# title: Test Compaction Commands Test
# type: TEST
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: compaction
# repo: ovis-runtime
# path: tests/test_compaction_commands.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/TEST-COMPACTION-0001.yaml
# module_id: MOD-BRANCH-COMPACTION-0001
# module_slug: branch_compaction
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
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
                branch_id="br_001",
                root_signal_id="sig_001",
                current_state_ref="state/branch_001.json",
                latest_compaction_id=None,
                status="open",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
            trigger=CompactionTriggerClass.HISTORY_NOISE,
            source_range="events:1-10",
            correlation_id="corr_001",
            preserved_reference_index=PreservedReferenceIndex(
                references=(ObjectRef(object_type=ObjectType.SIGNAL, object_id="sig_001"),)
            ),
        )
    )

    with pytest.raises(NotImplementedError):
        runner.compact(command)
