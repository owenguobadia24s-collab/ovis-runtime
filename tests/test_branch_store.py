from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_branch import BranchEventReference, BranchState, BranchStatus, InMemoryBranchStore  # noqa: E402
from ovis_state_models import Branch  # noqa: E402


def _state(branch_id: str = "br_001") -> BranchState:
    branch = Branch(
        branch_id=branch_id,
        root_signal_id="sig-001",
        current_state_ref=f"memory://branches/{branch_id}",
        latest_compaction_id=None,
        status=BranchStatus.OPEN,
        created_at="2026-03-15T00:00:00Z",
        updated_at="2026-03-15T00:00:00Z",
    )
    return BranchState(
        branch=branch,
        correlation_id="corr_001",
        event_refs=(BranchEventReference(event_id="evt_001"),),
        latest_event=BranchEventReference(event_id="evt_001"),
    )


def test_in_memory_branch_store_round_trips_state() -> None:
    store = InMemoryBranchStore()
    created = store.create(_state())

    fetched = store.get("br_001")

    assert created.branch.branch_id == "br_001"
    assert fetched.latest_event is not None
    assert fetched.latest_event.event_id == "evt_001"


def test_in_memory_branch_store_rejects_missing_or_duplicate_branches() -> None:
    store = InMemoryBranchStore()
    state = _state()
    store.create(state)

    with pytest.raises(ValueError):
        store.create(state)

    with pytest.raises(KeyError):
        store.get("br_missing")

    with pytest.raises(KeyError):
        store.replace(_state("br_missing"))
