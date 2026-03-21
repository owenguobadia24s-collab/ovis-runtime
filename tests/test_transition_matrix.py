# ---
# id: TEST-STATE-0004
# title: Test Transition Matrix Test
# type: TEST
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: state
# repo: ovis-runtime
# path: tests/test_transition_matrix.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/TEST-STATE-0004.yaml
# module_id: MOD-WORK-OBJECT-REGISTRY-0001
# module_slug: work_object_registry
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_state_models.enums import (  # noqa: E402
    BridgeActionStatus,
    ExecuteJobStatus,
    PlanJobStatus,
    WorkObjectStatus,
)
from ovis_state_models.validators.transitions import is_allowed_transition  # noqa: E402


def test_work_object_transition_matrix_matches_adr_direction() -> None:
    assert is_allowed_transition(WorkObjectStatus.INBOX, WorkObjectStatus.ROUTED)
    assert not is_allowed_transition(WorkObjectStatus.INBOX, WorkObjectStatus.EXECUTING)


def test_plan_and_execute_job_transitions_are_purely_validated() -> None:
    assert is_allowed_transition(PlanJobStatus.DRAFT, PlanJobStatus.READY_FOR_REVIEW)
    assert is_allowed_transition(ExecuteJobStatus.READY, ExecuteJobStatus.RUNNING)
    assert not is_allowed_transition(ExecuteJobStatus.READY, ExecuteJobStatus.COMPLETED)


def test_bridge_action_transition_matrix_is_available() -> None:
    assert is_allowed_transition(BridgeActionStatus.PENDING, BridgeActionStatus.DISPATCHED)
    assert not is_allowed_transition(BridgeActionStatus.ACKNOWLEDGED, BridgeActionStatus.PENDING)
