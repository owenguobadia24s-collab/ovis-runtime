# ---
# id: TEST-STATE-0001
# title: Test Ids And Enums Test
# type: TEST
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: state
# repo: ovis-runtime
# path: tests/test_ids_and_enums.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/TEST-STATE-0001.yaml
# module_id: MOD-WORK-OBJECT-REGISTRY-0001
# module_slug: work_object_registry
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_ids import generate_branch_id  # noqa: E402
from ovis_state_models.enums import (  # noqa: E402
    ApprovalDecision,
    EventType,
    PolicyProfile,
    RiskClass,
    WorkObjectStatus,
)
from ovis_state_models.ids import BranchId, CorrelationId, SignalId  # noqa: E402


def test_canonical_id_aliases_are_constructible() -> None:
    assert SignalId("sig-001") == "sig-001"
    assert BranchId("br-001") == "br-001"
    assert CorrelationId("corr-001") == "corr-001"
    assert str(generate_branch_id()).startswith("br_")


def test_core_enums_expose_canonical_values() -> None:
    assert WorkObjectStatus.AWAITING_REVIEW == "awaiting_review"
    assert ApprovalDecision.APPROVE == "approve"
    assert PolicyProfile.HUMAN_APPROVED == "human-approved"
    assert RiskClass.R4 == "R4"
    assert EventType.COMPACTION_CREATED == "compaction.created"
    assert EventType.CAPABILITY_ERROR == "capability.error"
    assert EventType.BRANCH_CLOSED == "branch.closed"
