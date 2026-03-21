# ---
# id: TEST-STATE-0002
# title: Test Json Schema Export Test
# type: TEST
# status: active
# authority: operational
# version: '0.1'
# layer: runtime
# domain: state
# repo: ovis-runtime
# path: tests/test_json_schema_export.py
# owner: Owen Vitae
# created: '2026-03-21'
# last_updated: '2026-03-21'
# registry: ovis-blueprint/REGISTRIES/entries/TEST-STATE-0002.yaml
# module_id: MOD-WORK-OBJECT-REGISTRY-0001
# module_slug: work_object_registry
# system_id: SYS-KERNEL-0001
# system_slug: ovis_kernel
# ---
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ovis_state_models.export import (  # noqa: E402
    export_model_schemas,
    export_schema_manifest,
    get_model_registry,
)


def test_schema_export_surface_covers_all_canonical_models() -> None:
    registry = get_model_registry()
    schemas = export_model_schemas()
    manifest = export_schema_manifest()

    assert set(registry) == set(schemas)
    assert set(registry) == set(manifest)
    assert "Signal" in schemas
    assert schemas["Signal"]["type"] == "object"
    assert "signal_id" in schemas["Signal"]["properties"]
    assert manifest["Signal"] == "schemas/generated/Signal.json"
