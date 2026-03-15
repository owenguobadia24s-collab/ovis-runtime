from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_state_models import (  # noqa: E402
    Approval,
    Branch,
    BridgeAction,
    CompactionRecord,
    Event,
    ExecuteJob,
    PlanJob,
    Signal,
    WorkObject,
)


def test_canonical_models_are_importable() -> None:
    model_names = {
        Approval.__name__,
        Branch.__name__,
        BridgeAction.__name__,
        CompactionRecord.__name__,
        Event.__name__,
        ExecuteJob.__name__,
        PlanJob.__name__,
        Signal.__name__,
        WorkObject.__name__,
    }

    assert "Signal" in model_names
    assert "CompactionRecord" in model_names
