"""JSON Schema export surfaces for canonical OVIS models."""

from __future__ import annotations

from collections.abc import Mapping

from ..models import (
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

MODEL_REGISTRY = {
    "Signal": Signal,
    "WorkObject": WorkObject,
    "PlanJob": PlanJob,
    "Approval": Approval,
    "ExecuteJob": ExecuteJob,
    "Event": Event,
    "BridgeAction": BridgeAction,
    "Branch": Branch,
    "CompactionRecord": CompactionRecord,
}


def export_model_schemas() -> dict[str, dict[str, object]]:
    """Return JSON Schema documents generated from canonical Python models."""

    return {
        name: model.model_json_schema()
        for name, model in MODEL_REGISTRY.items()
    }


def export_schema_manifest() -> dict[str, str]:
    """Return the generated output path for each exported schema."""

    return {
        name: f"schemas/generated/{name}.json"
        for name in MODEL_REGISTRY
    }


def get_model_registry() -> Mapping[str, type]:
    """Return the canonical model registry used for schema export."""

    return dict(MODEL_REGISTRY)
