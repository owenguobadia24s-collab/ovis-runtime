# ---
# id: TEST-STATE-0003
# title: Test Model Imports Test
# type: TEST
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: state
# repo: ovis-runtime
# path: tests/test_model_imports.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/TEST-STATE-0003.yaml
# module_id: MOD-WORK-OBJECT-REGISTRY-0001
# module_slug: work_object_registry
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
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
