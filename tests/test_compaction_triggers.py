# ---
# id: TEST-COMPACTION-0003
# title: Test Compaction Triggers Test
# type: TEST
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: compaction
# repo: ovis-runtime
# path: tests/test_compaction_triggers.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/TEST-COMPACTION-0003.yaml
# module_id: MOD-BRANCH-COMPACTION-0001
# module_slug: branch_compaction
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
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
