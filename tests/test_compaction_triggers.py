from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_branch_compaction import CompactionTriggerClass  # noqa: E402


def test_compaction_trigger_enum_exposes_all_canonical_values() -> None:
    assert CompactionTriggerClass.BEFORE_ARCHIVAL == "before-archival"
    assert CompactionTriggerClass.BEFORE_FORK == "before-fork"
    assert CompactionTriggerClass.EXECUTION_MILESTONE == "execution-milestone"
    assert CompactionTriggerClass.HISTORY_NOISE == "history-noise"
    assert CompactionTriggerClass.RUNTIME_CONTEXT_LIMIT == "runtime-context-limit"
    assert CompactionTriggerClass.OPERATOR_REQUEST == "operator-request"
    assert CompactionTriggerClass.SYSTEM_POLICY == "system-policy"
