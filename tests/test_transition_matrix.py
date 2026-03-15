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
