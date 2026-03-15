from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_event_log.constants import (  # noqa: E402
    BRIDGE_EVENT_FAMILIES,
    CAPABILITY_EVENT_FAMILIES,
    COMPACTION_EVENT_FAMILIES,
    EXECUTION_EVENT_FAMILIES,
    PLAN_EVENT_FAMILIES,
    SIGNAL_EVENT_FAMILIES,
    WORK_OBJECT_EVENT_FAMILIES,
)
from ovis_state_models.enums import EventType  # noqa: E402


def test_event_family_groupings_are_sourced_from_canonical_event_type() -> None:
    assert SIGNAL_EVENT_FAMILIES == (
        EventType.SIGNAL_CREATED,
        EventType.SIGNAL_COMPRESSED,
    )
    assert WORK_OBJECT_EVENT_FAMILIES == (
        EventType.WORK_OBJECT_CREATED,
        EventType.WORK_OBJECT_UPDATED,
    )
    assert PLAN_EVENT_FAMILIES == (
        EventType.PLAN_JOB_CREATED,
        EventType.APPROVAL_RECORDED,
    )
    assert EXECUTION_EVENT_FAMILIES == (
        EventType.EXECUTE_JOB_CREATED,
        EventType.EXECUTE_JOB_STATUS_CHANGED,
    )
    assert CAPABILITY_EVENT_FAMILIES == (
        EventType.CAPABILITY_REQUESTED,
        EventType.CAPABILITY_COMPLETED,
        EventType.CAPABILITY_ERROR,
    )
    assert BRIDGE_EVENT_FAMILIES[-1] == EventType.BRIDGE_ACTION_FAILED
    assert COMPACTION_EVENT_FAMILIES == (EventType.COMPACTION_CREATED,)
